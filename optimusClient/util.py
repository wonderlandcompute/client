import os

import grpc
import yaml


def getCredentials():
    if os.path.exists(_config_dict.get("ca_cert")) and os.path.exists(
            _config_dict.get("client_key")) and os.path.exists(
        _config_dict.get("client_cert")):
        # read in certificate
        root_cert = open(_config_dict.get("ca_cert"), 'rb').read()
        private_key = open(_config_dict.get("client_key"), 'rb').read()
        cert_chain = open(_config_dict.get("client_cert"), 'rb').read()
        credentials = grpc.ssl_channel_credentials(root_certificates=root_cert, private_key=private_key,
                                                   certificate_chain=cert_chain)
    else:
        raise ValueError("no such file")
    return credentials


def checkJobsEqual(a, b):
    return (a.Project == b.Project) and (a.Id == b.Id) and (a.Status == b.Status) and (
        a.Coordinate == b.Coordinate) and (a.MetricValue == b.MetricValue) and (
               a.Metadata == b.Metadata) and (a.Kind == b.Kind) and (a.Output == b.Output) and (a.Input == b.Input)


def initTestsConfig():
    config_path = os.getenv("OPTIMUS_TESTS_CONFIG")
    if os.path.exists(config_path):
        with open(config_path, 'r') as stream:
            try:
                data_map = (yaml.load(stream))
                _config_dict.update(data_map)
                return _config_dict
            except yaml.YAMLError as exc:
                print(exc)
_config_dict = {"client_cert": "", "client_key": "", "ca_cert": "", "connect_to": "", "db_uri": ""}
