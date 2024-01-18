from io import BytesIO
import docker
import json
import tarfile
import time
import os
import datetime
client = docker.from_env()
# docker build . -t bm25
# if python-minimal doesnt want to be installed https://askubuntu.com/questions/1461807/i-cant-install-python3-10-minimal-on-ubuntu-22-04-lts-in-container

jobs = []
for i in range(1):
    for k_1 in [1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]:
        for b in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:

            jobs.append(
                {"k_1": k_1, "b": b, "eval_metrics": ";".join(['ndcg_cut_5', 'ndcg_cut_10', 'P_10'])})
running_jobs_containers = []
max_jobs_running = 8


def main_loop():
    while True:
        for running in running_jobs_containers:
            job = running[0]
            container = running[1]
            is_running = check_container(container, job)
            if not is_running:
                running_jobs_containers.remove(running)
        for i in range(max_jobs_running-len(running_jobs_containers)):
            if len(jobs) > 0:
                job = jobs.pop(0)
                container = start_container(job)
                running_jobs_containers.append([job, container])
        if len(jobs) == 0 and len(running_jobs_containers) == 0:
            break
    time.sleep(1)


def start_container(job):
    k_1 = job["k_1"]
    b = job["b"]
    print("starting container", k_1, b)
    container = client.containers.run("bm25", detach=True, environment=["BM25_k_1={k_1}".format(
        k_1=k_1), "BM25_b={b}".format(b=b), "EVAL_METRIC={eval_metrics}".format(eval_metrics=job["eval_metrics"])])
    return container


def check_container(container, job):
    container.reload()
    if container.status == "created":
        return True
    if container.status == "running":
        return True
    if container.status == "exited":
        persist_container(container, job)
        return False
    print("unknown", container, "status", container.status, "job:", job)
    return False


def persist_container(container, job):
    # time dependet foldername as number
    folder = str(int(time.time()*1000))
    foldername = "milestone4/bm25/out/"+folder
    # create folder
    os.mkdir(foldername)

    # print("persisting container", container)
    # print(json.dumps(container.diff()))
    k_1 = job["k_1"]
    b = job["b"]
    container.restart()
    while container.status != "running":
        container.reload()
    archive_data, _ = container.get_archive(
        "/app/grid-search/training/bm25-b={b}-k_1={k_1}/run.txt".format(b=b, k_1=k_1))
    archive_bytes = b"".join(archive_data)
    with tarfile.open(fileobj=BytesIO(archive_bytes), mode='r') as tar:
        # Assuming there is only one file in the archive
        file_info = tar.getmembers()[0]
        file_content = tar.extractfile(file_info).read()
    with open(foldername+"/run.txt", 'w') as outfile:
        outfile.write(file_content.decode("utf-8"))

    archive_data, _ = container.get_archive("/app/grid-search/validation.csv")
    archive_bytes = b"".join(archive_data)
    with tarfile.open(fileobj=BytesIO(archive_bytes), mode='r') as tar:
        # Assuming there is only one file in the archive
        file_info = tar.getmembers()[0]
        file_content = tar.extractfile(file_info).read()

    with open(foldername+"/validation.csv", 'w') as outfile:
        outfile.write(file_content.decode("utf-8"))

    # metadatametadata
    metadata = {"k_1": k_1, "b": b,
                "eval_metrics": job["eval_metrics"], "id": folder}
    metadata["completed"] = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S")
    with open(foldername+"/metadata.json", 'w') as outfile:
        json.dump(metadata, outfile)
    container.stop()


main_loop()
