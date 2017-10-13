import grpc

import disneylandClient.disneyland_pb2
from disneylandClient.disneyland_pb2 import Job, RequestWithId, ListOfJobs, ListJobsRequest, DisneylandStub

config_dict = disneylandClient.initTestsConfig()

creds = disneylandClient.getCredentials()

# create channel using ssl credentials
channel = grpc.secure_channel(config_dict.get("connect_to"), creds)
stub = DisneylandStub(channel)

job = Job(metadata="vs", input="python-client-input", output="python-client-output")
created_job = stub.CreateJob(job)
print("success {0}".format(created_job))

read_job = stub.GetJob(RequestWithId(id=created_job.id))
disneylandClient.checkJobsEqual(created_job, read_job)
print("success {0}".format(read_job))

created_job.status = disneylandClient.getEnumValueByName(disneylandClient._JOB_STATUS, "FAILED")
created_job.metric_value = "metric_test"
created_job.metadata = "meta_test"
created_job.kind = "etc."

updated_job = stub.ModifyJob(created_job)
print("success {0}".format(updated_job))

created_job = stub.CreateJob(Job(coordinate="second"))
print("success {0}".format(created_job))

all_jobs = stub.ListJobs(ListJobsRequest())
if len(all_jobs.jobs) > 0:
    print("success {0}".format(all_jobs))

pulled_jobs = stub.PullPendingJobs(ListJobsRequest(how_many=2))
if len(pulled_jobs.jobs) == 2:
    print("success {0}".format(pulled_jobs))

multiple_jobs = stub.CreateMultipleJobs(ListOfJobs(jobs=[Job(input="first"), Job(input="second")]))
if len(multiple_jobs.jobs) == 2:
    print("success {0}".format(multiple_jobs))
