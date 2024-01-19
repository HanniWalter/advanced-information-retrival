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
for mu in [1800, 1900, 2000, 2100, 2200, 2300, 2400, 2500, 2600, 2700, 2800, 2900, 3000]:
    jobs.append({"mu": mu})
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
    mu = job["mu"]

    print("starting container", mu)
    container = client.containers.run("lm", detach=True, environment=[
                                      "LM_mu={mu}".format(mu=mu)])
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
    foldername = "milestone4/lm/out/"+folder
    # create folder
    os.mkdir(foldername)

    # print("persisting container", container)
    # print(json.dumps(container.diff()))
    container.restart()
    while container.status != "running":
        container.reload()
    archive_data, _ = container.get_archive(
        "/app/lm/training/run.txt")
    archive_bytes = b"".join(archive_data)
    with tarfile.open(fileobj=BytesIO(archive_bytes), mode='r') as tar:
        # Assuming there is only one file in the archive
        file_info = tar.getmembers()[0]
        file_content = tar.extractfile(file_info).read()
    with open(foldername+"/run.txt", 'w') as outfile:
        outfile.write(file_content.decode("utf-8"))

    archive_data, _ = container.get_archive("/app/lm/validation.csv")
    archive_bytes = b"".join(archive_data)
    with tarfile.open(fileobj=BytesIO(archive_bytes), mode='r') as tar:
        # Assuming there is only one file in the archive
        file_info = tar.getmembers()[0]
        file_content = tar.extractfile(file_info).read()

    with open(foldername+"/validation.csv", 'w') as outfile:
        outfile.write(file_content.decode("utf-8"))

    # metadatametadata
    metadata = {"id": folder}
    metadata["mu"] = job["mu"]
    metadata["type"] = "lm"
    metadata["completed"] = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S")
    with open(foldername+"/metadata.json", 'w') as outfile:
        json.dump(metadata, outfile)
    container.stop()


main_loop()
