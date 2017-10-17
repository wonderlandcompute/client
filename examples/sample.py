import grpc

import disneylandClient.disneyland_pb2
from disneylandClient.disneyland_pb2 import Job, RequestWithId, ListJobsKindRequest, DisneylandStub

config_dict = disneylandClient.initClientConfigFromEnv()
creds = disneylandClient.getCredentials()

# create channel using ssl credentials
channel = grpc.secure_channel(config_dict.get("connect_to"), creds)
stub = DisneylandStub(channel)

print("\tCreate Job with params")
job = Job(metadata="vs", input="python-client-input", output="python-client-output", kind="docker")
created_job = stub.CreateJob(job)
print("success\n{0}".format(created_job))

print("\tGet Job")
read_job = stub.GetJob(RequestWithId(id=created_job.id))
disneylandClient.checkJobsEqual(created_job, read_job)
print("success\n{0}".format(read_job))

print("\tModify Job")
created_job.status = Job.FAILED
created_job.metadata = "meta_test"
created_job.kind = "docker"

updated_job = stub.ModifyJob(created_job)
print("success\n{0}".format(updated_job))

print("\tCreate Job blank")
created_job = stub.CreateJob(Job())
print("success\n{0}".format(created_job))

print("\tList Jobs")
all_jobs = stub.ListJobs(ListJobsKindRequest())
if len(all_jobs.jobs) > 0:
    print("success\n{0}".format(all_jobs))

print("\tList Jobs with params")
all_jobs = stub.ListJobs(ListJobsKindRequest(how_many=2, kind='docker'))
if len(all_jobs.jobs) > 0:
    print("success\n{0}".format(all_jobs))

print("\tPull Jobs with params")
pulled_jobs = stub.PullPendingJobs(ListJobsKindRequest(how_many=2, kind='docker'))
if len(pulled_jobs.jobs) == 2:
    print("success\n{0}".format(pulled_jobs))
