import os

import grpc
import yaml

import optimusClient.optimus_pb2


def checkJobsEqual(a, b):
    return (a.Project == b.Project) and (a.Id == b.Id) and (a.Status == b.Status) and (
        a.Coordinate == b.Coordinate) and (a.MetricValue == b.MetricValue) and (
               a.Metadata == b.Metadata) and (a.Kind == b.Kind) and (a.Output == b.Output) and (a.Input == b.Input)


def initTestsConfig(config_dict):
    config_path = os.getenv("OPTIMUS_TESTS_CONFIG")
    if os.path.exists(config_path):
        with open(config_path, 'r') as stream:
            try:
                data_map = (yaml.load(stream))
                config_dict.update(data_map)
            except yaml.YAMLError as exc:
                print(exc)


config_dict = {"client_cert": "", "client_key": "", "ca_cert": "", "connect_to": "", "db_uri": ""}
initTestsConfig(config_dict)
print(config_dict)

host = config_dict.get("connect_to")
idx = host.find(":")
port = host[idx + 1:]
host = host[0:idx]
print("host:{0}, port:{1}".format(host, port))
# read in certificate
clientpem_path = "../configs/client.pem"
if os.path.exists(clientpem_path):
    credentials = grpc.ssl_channel_credentials(clientpem_path)
else:
    print(os.getcwd())
    raise ValueError

# create channel using ssl credentials
channel = grpc.secure_channel(config_dict.get("connect_to"), credentials)
stub = optimusClient.OptimusStub(channel)
job= optimusClient.Job()

stub.CreateJob(optimusClient.Job())
print("success")
