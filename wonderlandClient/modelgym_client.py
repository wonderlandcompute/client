from wonderlandClient import (
    new_client,
    Job,
    RequestWithId
)
from azure.storage.file import FileService, ContentSettings
from . import wonderland_pb2_grpc
from . import wonderland_pb2

from hashlib import sha256
from pathlib import Path
import yaml
import datetime
import random
import string
import json
import grpc
import logging
import numpy as np
import asyncio
import time

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
        if project_root.is_dir():
            self.project_root = project_root
            self.project_name = Path(self.project_root.parts[-1])
        else:
            raise NotADirectoryError("LOCAL_PROJECT_ROOT folder doesn't exist ! Check Azure File Storage mount")
        if (self.project_root / self.config["user"]).is_dir():
            self.user = self.config["user"]
        else:
            raise NotADirectoryError("USER folder doesn't exist ! Check Azure File Storage mount")

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
        # output_file = self.project_root.parent / model_path / MODELGYM_CONFIG["output_file"]
        # pickled_model_path = self.project_root.parent / model_path / MODELGYM_CONFIG["model_pickled"]
        # await self.get_data(output_file, job.id)
        # with open(output_file, "r") as f:
        #     output = json.load(f)
        # await self.get_data(pickled_model_path, job.id)
        # return {"output": output,
        #         "model_path": pickled_model_path}
        self.stub.GetJob(RequestWithId(id=job.id))
        return job.id

    def gather_results(self, job_id_list):
        job_compeleted = {job_id: wonderland_pb2.Job.PENDING for job_id in job_id_list}
        ##add timeout
        while True:
            time.sleep(5)
            for id in job_id_list:
                job = self.stub.GetJob(RequestWithId(id=id))
                job_compeleted[id] = job.status
            if not any(s in job_compeleted.values() for s in (wonderland_pb2.Job.PENDING,
                                                              wonderland_pb2.Job.RUNNING,
                                                              wonderland_pb2.Job.PULLED)):
                break

        results = {}
        for id in job_id_list:
            results[id] = {}
            job = self.stub.GetJob(RequestWithId(id=id))
            file_list = json.loads(job.output)
            for file, path in file_list.items():
                self.file_service.get_file_to_path(share_name=self.afs_share,
                                                   directory_name=Path(path).parent,
                                                   file_name=Path(path).name,
                                                   file_path=str(self.project_root / path))
                if file == 'output':
                    with open(self.project_root / path, "r") as f:
                        results[id]['output'] = json.load(f)
                if file == 'result_model_path':
                    results[id]['result_model_path'] = self.project_root / path
        return results

    # def make_pipe(self, model_folder, data_folder):
    #     """
    #     Create message for Wonderland grpc-server.
    #       Parameter `data` of wonderland_pb2.Dataset contains part of path on a remote server
    #     :param model: <string>. Model's folder name.
    #     :param data:  <string>. Data's folder name.
    #     :return: wonderland_pb2.Pipeline
    #     """
    #     model_path = self.project_root.parents[0] / model_folder
    #     if not (self.project_root.parents[0] / model_folder).is_dir():
    #         logging.warning("Model folder {} is missing".format(self.project_root.parents[0] / model_folder))
    #     # pipeline = wonderland_pb2.Pipeline(git_info=wonderland_pb2.GitUrl())
    #
    #     dataset_data = wonderland_pb2.Dataset(type="azureFile",
    #                                           data=[self.config["azurefs_share"] + '/' + str(data_folder),
    #                                                 self.config["azurefs_secret"]],
    #                                           container_mount_endpoint=MODELGYM_CONFIG["mount_data_endpoint"])
    #     dataset_model = wonderland_pb2.Dataset(type="azureFile",
    #                                            data=[self.config["azurefs_share"] + '/' + str(model_folder),
    #                                                  self.config["azurefs_secret"]],
    #                                            container_mount_endpoint=MODELGYM_CONFIG["mount_model_endpoint"])
    #     data_path = Path(MODELGYM_CONFIG["mount_data_endpoint"]) / MODELGYM_CONFIG["data_file"]
    #     model_path = Path(MODELGYM_CONFIG["mount_model_endpoint"]) / MODELGYM_CONFIG["model_file"]
    #     output_path = Path(MODELGYM_CONFIG["mount_model_endpoint"]) / MODELGYM_CONFIG["output_file"]
    #     func = wonderland_pb2.Function(docker_image=self.config["docker_image"],
    #                                    command_to_execute=MODELGYM_CONFIG["command_to_execute"],
    #                                    execution_parameters=[str(data_path),
    #                                                          str(model_path),
    #                                                          str(output_path)],
    #                                    inputs={"data": dataset_data, "model": dataset_model}
    #                                    )
    #
    #     pipeline.nodes[MODELGYM_CONFIG["single_node_name"]].func.CopyFrom(func)
    #     return pipeline

    def send_model(self, model_info):
        folder = "model-" + ''.join([random.choice(string.ascii_letters + string.digits) for _ in range(12)])
        model_folder = self.project_root / self.user / folder
        try:
            model_folder.mkdir()
        except FileExistsError:
            logging.warning("Model folder {} is exist !".format(model_folder))
        except FileNotFoundError:
            logging.warning("Model folder {} is missing !".format(model_folder))
        path = model_folder / MODELGYM_CONFIG["model_file"]
        with (path).open(mode="w") as file:
            json.dump(model_info, file, cls=NumpyEncoder)
        # tag = self.from_project_root_path(path)
        afs_path = Path(self.user) / folder
        self.file_service.create_directory(share_name=self.afs_share,
                                           directory_name=afs_path)
        self.file_service.create_file_from_path(share_name=self.afs_share,
                                                directory_name=afs_path,
                                                file_name=MODELGYM_CONFIG["model_file"],
                                                local_file_path=path)
        return afs_path / MODELGYM_CONFIG["model_file"]

    def send_data(self, data_path):
        """
        Copy data to the local DATA directory, that must be mounted with Azure FS.
        (can be replaced by rpc method)

        :param data: <string>. Specify you data path by string.
        :return: Folder's name.
        """
        checksum = get_data_hash(data_path)[:10]

        list_folder = self.file_service.list_directories_and_files(self.afs_share)
        for folder in list_folder:
            if checksum == folder.name[-10:]:
                logging.info("Folder for data already exist!")
                return self.from_project_root_path(self.project_root / MODELGYM_CONFIG["data_folder"] / folder.name)
        time = datetime.datetime.today()
        # data_folder = self.project_root / MODELGYM_CONFIG["data_folder"] / (time.strftime("%Y-%m-%d-%H.%M") + '-' + checksum)
        data_folder = time.strftime("%Y-%m-%d-%H.%M") + '-' + checksum
        afs_path = Path(MODELGYM_CONFIG["data_folder"]) / data_folder
        self.file_service.create_directory(share_name=self.afs_share, directory_name=afs_path)
        self.file_service.create_file_from_path(share_name=self.afs_share,
                                                directory_name=afs_path,
                                                file_name=MODELGYM_CONFIG["data_file"],
                                                local_file_path=data_path)
        return afs_path / MODELGYM_CONFIG["data_file"]

    # def upload_data(self, data_path, tag):
    # data_path = str(data_path)
    # tag = str(tag)
    # chunks_generator = get_file_chunks(data_path, tag)
    # response = self.stub.UploadFile(chunks_generator)
    # # assert response.length == os.path.getsize(data_path)
    # return response

    # def download_data(self, data_path, tag, launch_id):
    #     data_path = str(data_path)
    #     tag = str(tag)
    #     response = self.stub.GetFile(wonderland_pb2.FileRequest(launch_id=launch_id, file_path=tag))
    #     save_chunks_to_file(response, data_path)

    # async def get_data(self, path, launch_id):
    #     tag = self.from_project_root_path(path)
    #     self.download_data(path, tag, launch_id)
    #     while not path.exists():
    #         await asyncio.sleep(5)
    #     return

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

# def get_file_chunks(path, tag):
#     message = wonderland_pb2.Chunk()
#     message.Path = tag
#     yield message
#     with open(path, 'rb') as f:
#         while True:
#             piece = f.read(CHUNK_SIZE);
#             if len(piece) == 0:
#                 return
#             message.Content = piece
#             yield message
#
#
# def save_chunks_to_file(chunks, path):
#     with open(path, 'wb') as f:
#         for chunk in chunks:
#             f.write(chunk.Content)
