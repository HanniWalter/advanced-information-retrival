import docker
import json
import tarfile
client = docker.from_env()
#docker build . -t bm25
# if python-minimal doesnt want to be installed https://askubuntu.com/questions/1461807/i-cant-install-python3-10-minimal-on-ubuntu-22-04-lts-in-container


jobs = []
for i in range(1):
    jobs.append({"k_1": 1.2, "b": 0.6, "eval_metrics": ";".join(['ndcg_cut_5'])})
running_jobs_containers = []
max_jobs_running = 1

def main_loop():
    while True:
        for running in running_jobs_containers:
            job = running[0]
            container = running[1]
            is_running = check_container(container,job)
            if not is_running:
                running_jobs_containers.remove(running)
        for i in range(max_jobs_running-len(running_jobs_containers)):
            if len(jobs) > 0:
                job = jobs.pop()
                container = start_container(job)
                running_jobs_containers.append([job,container])
        if len(jobs) == 0 and len(running_jobs_containers) == 0:
            break

    


def start_container(job):
    k_1 = job["k_1"]
    b = job["b"]
    container =client.containers.run("bm25", detach=True, environment=["BM25_k_1={k_1}".format(k_1=k_1),"BM25_b={b}".format(b=b),"EVAL_METRIC={eval_metrics}".format(eval_metrics=job["eval_metrics"])])
    return container
    

def check_container(container,job):
    container.reload()
    if container.status == "created":
        return True
    if container.status == "running":
        return True
    if container.status == "exited":
        persist_container(container,job)
        return False
    print("unknown",container,"status", container.status,"job:" ,job)
    return False

def persist_container(container, job):
    #print("persisting container", container)
    #print(json.dumps(container.diff()))
    k_1 = job["k_1"]
    b = job["b"]
    container.restart()
    while container.status != "running":
        container.reload()
    archive = container.get_archive("/app/grid-search/training/bm25-b={b}-k_1={k_1}/run.txt".format(b=b,k_1=k_1))
    #print(archive)
    with tarfile.open(fileobj=archive.data, mode='r') as tar:
        # Assuming there is only one file in the archive
        file_info = tar.getmembers()[0]
        file_content_1 = tar.extractfile(file_info).read()

    archive = container.get_archive("/app/grid-search/validation.csv".format(b=b,k_1=k_1))
    #print(archive)
    with tarfile.open(fileobj=archive.data, mode='r') as tar:
        # Assuming there is only one file in the archive
        file_info = tar.getmembers()[0]
        file_content_2 = tar.extractfile(file_info).read()
    # Print the content
    container.stop()
    print(file_content_1.decode('utf-8'))
    print(file_content_2.decode('utf-8'))

main_loop()