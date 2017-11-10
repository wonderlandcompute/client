Installation
---

You can install pydisneyland for python3 like this: `pip install git+https://github.com/skygrid/pydisneyland.git`.

To use client, you'll need to create `.disney` directory in your home dir, and put following files there:

* Server CA certificate, user's private key and certificate — those 3 can be obtained from system administrator
* File named `config.yml` with contenst like the following:

```yaml
client_cert: /path/to/client/cert.crt  # change this to path for user cert on your system
client_key: /path/to/client/key.key # change this to path for user key on your system
ca_cert: /path/to/ca/cert.crt # change this to path for user CA on your system
connect_to: 127.0.0.1:50051 # this should also be given by system administrator
```


Example: docker computation submission
---


```python
import time
import json

from disneylandClient import (
    new_client,
    Job,
    RequestWithId,
)

STATUS_IN_PROCESS = set([
    Job.PENDING,
    Job.PULLED,
    Job.RUNNING,
])
STATUS_FINAL = set([
    Job.COMPLETED,
    Job.FAILED,
])

descriptor = {
    "input": [],

    "container": {
        "workdir": "",
        "name": "busybox:latest",
        "cpu_needed": 1,
        "max_memoryMB": 1024,
        "min_memoryMB": 512,
        "cmd": "sh -lc 'echo 123 > /output/test.txt'",
    },

    "required_outputs": {
        "output_uri": "none:",
        "file_contents": [
            {"file": "test.txt", "to_variable": "out"}
        ]
    }
}


def main():
    stub = new_client()

    job = Job(
        input=json.dumps(descriptor),
        kind="docker",
    )

    job = stub.CreateJob(job)
    print("Job", job)

    while True:
        time.sleep(3)
        job = stub.GetJob(RequestWithId(id=job.id))
        print("[{}] Job :\n {}\n".format(time.time(), job))

        if job.status in STATUS_FINAL:
            break

    if job.status == Job.FAILED:
        print("Job failed!")

    print("result:", json.loads(job.output))


if __name__ == '__main__':
    main()
```


Example: parabola non-gradient optimisation
---

Here we need two scripts. First does the optimisation computation:

```python
import numpy as np
from skopt import gp_minimize
import time

import grpc
from disneylandClient import (
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
    print "[{}] Created Job :\n {}\n".format(time.time(), job)
    while True:
        time.sleep(SLEEP_TIME)
        job = stub.GetJob(RequestWithId(id=job.id))
        print "[{}] Job :\n {}\n".format(time.time(), job)

        if job.status in STATUS_FINAL:
            break

    if job.status == Job.FAILED:
        raise Exception("Job failed!")

    print "result:", job.output

    return float(job.output)


def main():
    res = gp_minimize(f, [(-100.0, 100.0)])
    print "Optimization result:", res


if __name__ == '__main__':
    main()
```


And the worker script which computes function:


```python
import numpy as np
from skopt import gp_minimize
import time

import grpc

from disneylandClient import (
    new_client,
    Job,
    RequestWithId,
    ListJobsRequest
)

SLEEP_TIME = 1 # seconds

stub = new_client()


def process_job(job):
    job.output = str(float(job.input)**2)
    job.status = disneylandClient.disneyland_pb2.Job.COMPLETED
    stub.ModifyJob(job)


def main():
    while True:
        pulled_jobs = stub.PullPendingJobs(ListJobsRequest(how_many=100))
        for job in pulled_jobs.jobs:
            process_job(job)
            print "Processed:\n", job

if __name__ == '__main__':
    main()

```

There is also disneyClient.worker module which has userful `Worker` class.
