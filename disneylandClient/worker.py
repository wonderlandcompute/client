from multiprocessing import Process
from time import sleep

from . import Job, RequestWithId, ListJobsRequest, new_client


class Worker(object):
    def __init__(
            self,
            stub,
            job_kind,
            job_func,
            threads_num=2,
            sleep_time=10):
        self.stub = stub
        self.job_kind = job_kind
        self.sleep_time = sleep_time
        self.do_job = job_func
        self.cpu_avail = threads_num
        self.cpus_per_job = {}  # job_id -> needed_cpus
        self.processes = []
        self.running = False
        self.stream = None

    def start(self):
        self.running = True
        self.run()

    def init_streaming(self):
        def gen():
            while True:
                yield ListJobsRequest(how_many=self.cpu_avail, kind=self.job_kind)
                sleep(self.sleep_time)

        self.stream = self.stub.BidiJobs(gen())

    def stop(self):
        self.running = False
        for p in self.processes:
            p.terminate()

    def fail_all(self):
        self.cleanup_processes()
        self.stop()
        processes_snapshot = self.processes[:]
        for p in processes_snapshot:
            job_id = p.name.strip("job:")
            job = self.stub.GetJob(RequestWithId(id=job_id))
            job.status = Job.FAILED
            self.stub.ModifyJob(job)

    def sleep(self):
        sleep(self.sleep_time)

    def cleanup_processes(self):
        processes_snapshot = self.processes[:]
        for p in processes_snapshot:
            if not p.is_alive():
                self.processes.remove(p)
                self.release_cpus(p.name)

    def acquire_cpus(self, process_name, ncpus):
        ncpus = int(ncpus)
        self.cpus_per_job[process_name] = ncpus
        self.cpu_avail -= ncpus

    def release_cpus(self, process_name):
        self.cpu_avail += self.cpus_per_job[process_name]
        self.cpus_per_job.pop(process_name, None)
        print("Released cpu, available: {}".format(self.cpu_avail))

    def run(self):
        Process(target=self.init_streaming()).start()
        while True:
            jobs = []
            self.cleanup_processes()

            if self.cpu_avail <= 0:
                self.sleep()
                continue

            try:
                for job in self.stream:
                    jobs.append(job)
            except BaseException:
                jobs = []

            if len(jobs) == 0:
                self.sleep()
                continue

            for job in jobs:
                process_name = 'job:{}'.format(job.id)

                self.acquire_cpus(process_name, 1)

                p = Process(name=process_name, target=self.do_job, args=(job, new_client()))
                self.processes.append(p)
                p.start()
                self.sleep()
