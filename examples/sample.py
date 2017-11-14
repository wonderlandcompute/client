import time

import disneylandClient.disneyland_pb2
from disneylandClient.disneyland_pb2 import ListJobsRequest, ListOfJobs, Job, RequestWithId


def gen(i=0):
    while i < 2:
        yield ListJobsRequest(how_many=1, kind="test")
        i += 1
        time.sleep(0.1)


print("\tUser:")

user_client = disneylandClient.new_client()

print("\tCreate Job blank")
blank_job = user_client.CreateJob(Job())
print("success\n{0}".format(blank_job))

print("\tModify Job")
blank_job.status = Job.PENDING
blank_job.metadata = "meta_test"
blank_job.kind = "docker"
updated_job = user_client.ModifyJob(blank_job)
print("success\n{0}".format(updated_job))

print("\tCreate Job with params")
job = Job(metadata="vs", input="python-client-input", output="python-client-output", kind="test")
created_job = user_client.CreateJob(job)
print("success\n{0}".format(created_job))

print("\tGet Job")
read_job = user_client.GetJob(RequestWithId(id=blank_job.id))
disneylandClient.check_jobs_equal(blank_job, read_job)
print("success\n{0}".format(read_job))

print("\tList Jobs with params")
all_jobs = user_client.ListJobs(ListJobsRequest(how_many=1))
if len(all_jobs.jobs) > 0:
    print("success\n{0}".format(all_jobs))

print("\tPull Jobs with proper project")
pulled_jobs = user_client.PullPendingJobs(ListJobsRequest(how_many=2))
if len(pulled_jobs.jobs) > 0:
    print("success\n{0}".format(pulled_jobs))

print("\tCreate Job with params")
created_job = user_client.CreateJob(Job(kind="docker"))
print("success\n{0}".format(created_job))

print("\tDelete Job")
deleted_job = user_client.DeleteJob(RequestWithId(id=blank_job.id))
print("success\n{0}".format(deleted_job))

print ("\tCreate multiple Jobs")
created_jobs = user_client.CreateMultipeJobs(ListOfJobs(jobs=[Job(kind="docker"), Job(kind="test")]))
print (created_jobs)

print ("\tBidi RPC")
stream = user_client.BidiJobs(gen())
for job in stream:
    print (job)

print("\tWorker:")

worker_client = disneylandClient.new_client_from_path("/Users/macbook/.disney/config2.yml")
print("\tGet Job")
read_job = worker_client.GetJob(RequestWithId(id=created_job.id))
print("success\n{0}".format(read_job))

print("\tModify Job")
read_job.input = "worker-input"
read_job.metadata = "worker_test"

updated_job = worker_client.ModifyJob(read_job)
print("success\n{0}".format(updated_job))

print("\tPull Jobs with proper kind")
pulled_jobs = worker_client.PullPendingJobs(ListJobsRequest(how_many=1))
if len(pulled_jobs.jobs) > 0:
    print("success\n{0}".format(pulled_jobs))
