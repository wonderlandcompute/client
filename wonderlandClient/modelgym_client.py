import yaml
import random
import string
import json
import time
import logging
from multiprocessing import cpu_count
from hashlib import sha256
from pathlib import Path

import grpc
import numpy as np
from azure.storage.file import FileService

# from wonderlandClient.util import new_client
from .wonderland_pb2 import Job, RequestWithId
from .util import logbar
from . import wonderland_pb2_grpc





CHUNK_SIZE = 256

MODELGYM_CONFIG = {
    "default_config_path": "~/.wonder/config.yaml",
    "mount_data_endpoint": "/home/data",
    "mount_model_endpoint": "/home/model",
    "data_file": "data.csv",
    "model_file": "model.json",
    "model_pickled": "model.pickle",
    "output_file": "output.json",
    "command_to_execute": "trainer",
    "data_folder": "DATA",
    "single_node_name": "1"
}


class ModelGymClient:
    config = {}
    project_root = ""
    project_name = ""
    user = ""

    def __init__(self, config=None, config_path=MODELGYM_CONFIG["default_config_path"]):
        if config_path:
            self.config = self.__config_by_path(config_path)
        if type(config) is dict:
            self.config.update(config)
        else:
            if config:
                raise TypeError("config must be dictionary!")

        project_root = Path(self.config["local_project_root"]).expanduser()
        self.project_root = project_root
        self.project_name = Path(self.project_root.parts[-1])
        if not project_root.is_dir():
            project_root.mkdir(parents=True, exist_ok=True)
        user_folder = self.project_root / self.config["user"]
        self.user = self.config["user"]
        if not user_folder.is_dir():
            user_folder.mkdir(parents=True, exist_ok=True)

        # self.stub = new_client()
        self.file_service = FileService(account_name=self.config['azurefs_acc_name'],
                                        account_key=self.config['azurefs_acc_key'])
        self.afs_share = self.config['azurefs_share']
        self.__get_client_transport_credentials(str(Path(self.config["client_cert"]).expanduser()),
                                                str(Path(self.config["client_key"]).expanduser()),
                                                str(Path(self.config["ca_cert"]).expanduser()))
        self.channel = grpc.secure_channel(self.config["connect_to"],
                                           self.creds,
                                           options=(
                                               ('grpc.max_send_message_length', self.config["max_msg_size_megabytes"]),
                                               ('grpc.max_receive_message_length',
                                                self.config["max_msg_size_megabytes"]),
                                           ))
        self.stub = wonderland_pb2_grpc.WonderlandStub(self.channel)
        self.check_user()

    def check_user(self):
        list_folder = self.file_service.list_directories_and_files(self.afs_share)
        for folder in list_folder:
            if self.user == folder.name:
                return True
        print(self.afs_share)
        print(type(self.afs_share))
        print(self.user)
        print(type(self.user))
        self.file_service.create_directory(share_name=self.afs_share, directory_name=self.user)
        return True

    def __get_client_transport_credentials(self, client_cert_path, client_key_path, ca_cert_path):
        client_cert_path = Path(client_cert_path).expanduser()
        client_key_path = Path(client_key_path).expanduser()
        ca_cert_path = Path(ca_cert_path).expanduser()
        path_ok = [
            client_cert_path.exists(),
            client_key_path.exists(),
            ca_cert_path.exists()
        ]
        if not all(path_ok):
            raise ValueError("One of credentials files does not exist")
        self.creds = grpc.ssl_channel_credentials(ca_cert_path.read_bytes(),
                                                  client_key_path.read_bytes(),
                                                  client_cert_path.read_bytes())

    def __config_by_path(self, path):
        path = Path(path).expanduser()
        if path.exists():
            with path.open() as file:
                config = yaml.load(file)
            return config
        else:
            raise FileNotFoundError("Config {} doesn't exist !!! Check ~/.wonder/config.yaml".format(path))

    def eval_model(self, model_info, data_path):
        model_path = self.send_model(model_info)
        job = Job(input=json.dumps({
            "model_path": str(model_path),
            "data_path": str(data_path)}),
            kind="hyperopt")
        job = self.stub.CreateJob(job)
        self.stub.GetJob(RequestWithId(id=job.id))
        return job.id

    def gather_results(self, job_id_list, timeout):
        job_compeleted = {job_id: Job.PENDING for job_id in job_id_list}
        deadline = time.time() + timeout
        while True:
            time.sleep(5)
            for id in job_id_list:
                job = self.stub.GetJob(RequestWithId(id=id))
                job_compeleted[id] = job.status
            if not any(s in job_compeleted.values() for s in (Job.PENDING,
                                                              Job.RUNNING,
                                                              Job.PULLED)):
                break
            if time.time() > deadline:
                print("Timeout was expired!")
                break

        results = []
        for i, id in enumerate(job_id_list):
            job = self.stub.GetJob(RequestWithId(id=id))
            if job.status == Job.COMPLETED:
                results += [{}]
            else:
                results.append(None)
            files = {}
            if job.output != "":
                files = json.loads(job.output)
            for file, path in files.items():
                self.file_service.get_file_to_path(share_name=self.afs_share,
                                                   directory_name=Path(path).parent,
                                                   file_name=Path(path).name,
                                                   file_path=str(self.project_root / path))
                if file == 'output':
                    with open(self.project_root / path, "r") as f:
                        results[i]['output'] = json.load(f)
                if file == 'result_model_path':
                    results[i]['result_model_path'] = self.project_root / path
                if file == 'error':
                    with open(self.project_root / path, "r") as f:
                        logging.warning(f.read())
        return results


    def send_model(self, model_info):
        folder = "model-" + ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(12)])
        model_path = self.project_root / self.user / folder / MODELGYM_CONFIG["model_file"]
        try:
            model_folder = model_path.parent
            model_folder.mkdir()
        except FileExistsError:
            logging.warning("Model folder {} is exist !".format(model_folder))
        except FileNotFoundError:
            logging.warning("Model folder {} is missing !".format(model_folder))
        with (model_path).open(mode="w") as file:
            json.dump(model_info, file, cls=NumpyEncoder)
        afs_path = Path(self.user) / folder / MODELGYM_CONFIG["model_file"]
        self.file_service.create_directory(share_name=self.afs_share,
                                           directory_name=afs_path.parent)
        self.file_service.create_file_from_path(share_name=self.afs_share,
                                                directory_name=afs_path.parent,
                                                file_name=afs_path.name,
                                                local_file_path=model_path,
                                                max_connections=cpu_count())
        return afs_path

    def send_data(self, data_path, push_data=False):
        """
        Copy data to the AFS DATA directory.

        :param data_path: <string>. Specify you data path by string.
        :return: path in the AFS share.
        """
        logging.info("Sending data to AFS")
        checksum = get_data_hash(data_path)[:10]
        data_folder = time.strftime("%Y-%m-%d-%H.%M") + '-' + checksum
        afs_path = Path(MODELGYM_CONFIG["data_folder"]) / data_folder / MODELGYM_CONFIG["data_file"]

        list_folder = self.file_service.list_directories_and_files(self.afs_share, directory_name="DATA")
        for folder in list_folder:
            if checksum == folder.name[-10:]:
                logging.info("Folder for data already exist!")
                afs_path = Path("DATA") / folder.name / MODELGYM_CONFIG["data_file"]
                logging.info("Data is in the AFS {}".format(folder.name))
                if push_data:
                    logging.warning("Rewriting data")
                    afs_path = Path(MODELGYM_CONFIG["data_folder"]) / folder.name / MODELGYM_CONFIG["data_file"]
                else:
                    return afs_path
        self.file_service.create_directory(share_name=self.afs_share, directory_name=afs_path.parent)
        self.file_service.create_file_from_path(share_name=self.afs_share,
                                                directory_name=afs_path.parent,
                                                file_name=afs_path.name,
                                                local_file_path=data_path,
                                                max_connections=cpu_count(),
                                                progress_callback=logbar
                                                )
        logging.info("Sending is over")
        return afs_path

    def from_project_root_path(self, path):
        path = Path(path)
        # if not path.exists():
        # logging.warning("{} is missing !!".format(path))
        try:
            relative_path = path.relative_to(self.project_root.parent)
            return str(relative_path)
        except ValueError:
            logging.warning("Path doesn't have project_root folder {}".format(self.project_root))


class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """

    def default(self, obj):
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            return float(obj)
        elif isinstance(obj, (np.ndarray,)):  #### This is the fix
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


def get_data_hash(data_path):
    """
    Calculate sha-256 hash of data file

    :param data_path: <string>, data's path
    :return: <string>
    """
    data_path = str(data_path)
    BLOCKSIZE = 65536
    hasher = sha256()
    with open(data_path, 'rb') as file:
        buf = file.read(BLOCKSIZE)
        while len(buf) > 0:
            hasher.update(buf)
            buf = file.read(BLOCKSIZE)
    return hasher.hexdigest()
