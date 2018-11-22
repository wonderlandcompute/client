from multiprocessing import Process, Event
from time import sleep

from . import Job, ListJobsRequest, new_client, RequestWithId


class WorkerProcess:

    def __init__(self, job, job_func, args_list):
        self._finished = Event()

        self.job = job
        self.process_name = 'job:{}'.format(self.job.id)
        self.work_process = Process(
            name=self.process_name,
            target=job_func,
            args=tuple(args_list + [self._finished])
        )
        self.work_process.start()

    @property
    def finished(self):
        return self._finished.is_set()

    def kill(self):
        self.work_process.terminate()
        self._finished.set()


class Worker(object):

    def __init__(
            self,
            stub,
            job_kind,
            job_func,
            threads_num=2,
            sleep_time=10):
        self.job_kind = job_kind
        self.sleep_time = sleep_time
        self.do_job = job_func
        self.cpu_avail = threads_num
        self.cpus_per_job = {}  # job_id -> needed_cpus
        self.processes = []

        self.running = False

    def start(self):
        self.running = True
        self.run()

    def stop(self):
        self.running = False
        for p in self.processes:
            p.worker_process.terminate()

    def fail_all(self):
        self.cleanup_processes()
        self.stop()
        processes_snapshot = self.processes[:]
        stub = new_client()
        for p in processes_snapshot:
            p.job.status = Job.FAILED
            stub.ModifyJob(p.job)

    def sleep(self):
        sleep(self.sleep_time)

    def cleanup_processes(self):
        stub = new_client()
        processes_snapshot = self.processes[:]
        for p in processes_snapshot:
            if stub.GetJob(RequestWithId(id=p.job.id)).status == Job.KILLED:
                p.kill()
                print("Job:{} is killed".format(p.job.id))
            if p.finished:
                self.processes.remove(p)
                self.release_cpus(p.job.id)

    def acquire_cpus(self, job_id, ncpus):
        ncpus = int(ncpus)
        self.cpus_per_job[job_id] = ncpus
        self.cpu_avail -= ncpus

    def release_cpus(self, job_id):
        self.cpu_avail += self.cpus_per_job[job_id]
        self.cpus_per_job.pop(job_id, None)
        print("Released cpu, available: {}".format(self.cpu_avail))

    def run(self):
        while True:
            self.cleanup_processes()

            if self.cpu_avail <= 0:
                self.sleep()
                continue

            try:
                stub = new_client()
                pulled = stub.PullPendingJobs(
                    ListJobsRequest(
                        how_many=self.cpu_avail,
                        kind=self.job_kind
                    ),
                    timeout=10
                )
                jobs = pulled.jobs
            except BaseException:
                jobs = []

            if len(jobs) == 0:
                self.sleep()
                continue

            for job in jobs:
                self.acquire_cpus(job.id, 1)

                p = WorkerProcess(
                    job=job,
                    job_func=self.do_job,
                    args_list=[job]
                )
                self.processes.append(p)
