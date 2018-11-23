from wonderlandClient import (
    Job,
    new_client,
    ListJobsRequest
)

import time

SLEEP_TIME = 1 # seconds

stub = new_client()


def process_job(job):
    job.output = str(float(job.input)**2)
    job.status = Job.COMPLETED
    stub.ModifyJob(job)


def main():
    while True:
        # time.sleep(5)
        pulled_jobs = stub.PullPendingJobs(ListJobsRequest(how_many=100))
        for job in pulled_jobs.jobs:
            process_job(job)
            print("Processed:\n{}".format(job))

if __name__ == '__main__':
    main()