from skopt import gp_minimize
import time

from wonderlandClient import (
    new_client,
    Job,
    RequestWithId
)


SLEEP_TIME = 5 # seconds

STATUS_IN_PROCESS = set([
    Job.PENDING,
    Job.PULLED,
    Job.RUNNING,
])
STATUS_FINAL = set([
    Job.COMPLETED,
    Job.FAILED,
])

stub = new_client()


def f(x):
    job = Job(
        input=str(x[0]),
        kind="parabola-optimize-queue",
    )

    job = stub.CreateJob(job)
    print("[{}] Created Job :\n {}\n".format(time.time(), job))
    while True:
        # time.sleep(SLEEP_TIME)
        job = stub.GetJob(RequestWithId(id=job.id))
        print("[{}] Job :\n {}\n".format(time.time(), job))

        if job.status in STATUS_FINAL:
            break

    if job.status == Job.FAILED:
        raise Exception("Job failed!")

    print("result:", job.output)

    return float(job.output)


def main():
    res = gp_minimize(f, [(-100.0, 100.0)], n_calls=10)
    print("Optimization result: {}".format(res))


if __name__ == '__main__':
    main()