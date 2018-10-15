import os
import sys
import yaml
import json
from pathlib import Path

import grpc
import numpy as np
from hashlib import sha256

from .wonderland_pb2_grpc import WonderlandStub


def new_client():
    default_path = os.environ.get("WONDERCOMPUTECONFIG")
    if default_path is None:
        raise Exception("WONDERCOMPUTECONFIG environment variable wasn't set")
    return new_client_from_path(default_path)


def new_client_from_path(config_path):
    config = load_config(config_path)
    creds = load_credentials(config)
    channel = grpc.secure_channel(
        config.get("connect_to"),
        creds,
        options=(
            ('grpc.max_send_message_length', 1024 * 1024 * 1024),
            ('grpc.max_receive_message_length', 1024 * 1024 * 1024),
        )
    )
    return WonderlandStub(channel)


def load_config(config_path):
    if not os.path.exists(config_path):
        raise Exception("Config file `{}` does not exist".format(config_path))

    with open(config_path) as config_f:
        return yaml.load(config_f)


def load_credentials(config):
    ca_cert = Path(config.get("ca_cert")).expanduser()
    client_key = Path(config.get("client_key")).expanduser()
    client_cert = Path(config.get("client_cert")).expanduser()
    path_ok = [
        ca_cert.exists(),
        client_key.exists(),
        client_cert.exists(),
    ]
    if not all(path_ok):
        raise ValueError("One of credentials files does not exist")

    credentials = grpc.ssl_channel_credentials(
        root_certificates=ca_cert.read_bytes(),
        private_key=client_key.read_bytes(),
        certificate_chain=client_cert.read_bytes()
    )

    return credentials


def check_jobs_equal(a, b):
    return (a.project == b.project) and (a.id == b.id) and (a.status == b.status) and (
        a.metadata == b.metadata) and (a.kind == b.kind) and (a.output == b.output) and (a.input == b.input)

# def generate_data(file,
#                   n_samples=1000,
#                   n_features=20,
#                   n_informative=10,
#                   n_classes=2):
#     X, y = make_classification(n_samples=n_samples,
#                                n_features=n_features,
#                                n_informative=n_informative,
#                                n_classes=n_classes)
#     dataset = XYCDataset(X, y)
#     y = np.array([y])
#     data = np.concatenate((X, y.T), axis=1)
#     np.savetxt(file, data,
#                fmt='%.2f',
#                header=','.join([str(x) for x in range(n_features)] + ['y']),
#                delimiter=',')
#     return dataset

def logbar(current, total):
    if total == 0:
        sys.stdout.write("\rDownloading [%s]" % ('=' * 50))
        sys.stdout.flush()
        return
    done = int(50.0 * current / total)
    sys.stdout.write("\rDownloading [%s%s]" % ('=' * done, ' ' * (50 - done)))
    if current == total:
        sys.stdout.write("\n")
    sys.stdout.flush()

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