import os

import grpc
import yaml

from .disneyland_pb2_grpc import DisneylandStub


def new_client():
    default_path = os.path.join(os.environ.get("HOME"), ".disney/config.yml")
    return new_client_from_path(default_path)


def new_client_from_path(config_path):
    config = load_config(config_path)
    creds = load_credentials(config)
    channel = grpc.secure_channel(config.get("connect_to"), creds)
    return DisneylandStub(channel)


def load_config(config_path):
    if not os.path.exists(config_path):
        raise Exception("Config file `{}` does not exist".format(config_path))

    with open(config_path) as config_f:
        return yaml.load(config_f)


def load_credentials(config):
    path_ok = [
        os.path.exists(config.get("ca_cert")),
        os.path.exists(config.get("client_key")),
        os.path.exists(config.get("client_cert")),
    ]
    if not all(path_ok):
        raise ValueError("One of credentials files does not exist")

    root_cert = open(config.get("ca_cert"), 'rb').read()
    private_key = open(config.get("client_key"), 'rb').read()
    cert_chain = open(config.get("client_cert"), 'rb').read()
    credentials = grpc.ssl_channel_credentials(
        root_certificates=root_cert,
        private_key=private_key,
        certificate_chain=cert_chain
    )

    return credentials


def check_jobs_equal(a, b):
    return (a.project == b.project) and (a.id == b.id) and (a.status == b.status) and (
        a.metadata == b.metadata) and (a.kind == b.kind) and (a.output == b.output) and (a.input == b.input)
