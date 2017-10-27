import disneylandClient.disneyland_pb2
from disneylandClient.disneyland_pb2 import Job, RequestWithId, ListJobsRequest

print("\tUser:")

user_client = disneylandClient.new_client()

print("\tCreate Job blank")
created_job = user_client.CreateJob(Job())
print("success\n{0}".format(created_job))

print("\tModify Job")
created_job.status = Job.PENDING
created_job.metadata = "meta_test"
created_job.kind = "docker"

updated_job = user_client.ModifyJob(created_job)
print("success\n{0}".format(updated_job))

print("\tCreate Job with params")
job = Job(metadata="vs", input="python-client-input", output="python-client-output", kind="tester")
created_job = user_client.CreateJob(job)
print("success\n{0}".format(created_job))

print("\tGet Job")
read_job = user_client.GetJob(RequestWithId(id=created_job.id))
disneylandClient.check_jobs_equal(created_job, read_job)
print("success\n{0}".format(read_job))

print("\tList Jobs with params")
all_jobs = user_client.ListJobs(ListJobsRequest(how_many=1))
if len(all_jobs.jobs) > 0:
    print("success\n{0}".format(all_jobs))

print("\tPull Jobs with params")
pulled_jobs = user_client.PullPendingJobs(ListJobsRequest(how_many=3))
if len(pulled_jobs.jobs) > 0:
    print("success\n{0}".format(pulled_jobs))

print("\tCreate Job with params")
created_job = user_client.CreateJob(Job(kind="docker"))
print("success\n{0}".format(created_job))

print("\tDelete Job")
deleted_job = user_client.DeleteJob(RequestWithId(id=1))
print("success\n{0}".format(deleted_job))

print("\tWorker:")

worker_client = disneylandClient.new_client_from_path("/Users/macbook/.disney/config2.yml")
print("\tGet Job")
read_job = worker_client.GetJob(RequestWithId(id=3))
print("success\n{0}".format(read_job))

print("\tModify Job")
read_job.input = "worker-input"
read_job.metadata = "worker_test"

updated_job = worker_client.ModifyJob(read_job)
print("success\n{0}".format(updated_job))

print("\tPull Jobs with params")
pulled_jobs = worker_client.PullPendingJobs(ListJobsRequest(how_many=3))
if len(pulled_jobs.jobs) > 0:
    print("success\n{0}".format(pulled_jobs))