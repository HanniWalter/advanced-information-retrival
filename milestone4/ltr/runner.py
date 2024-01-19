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
for mu in [1000, 1100, 1200, 2900, 3000]:
    for k_1 in [0.4, 0.7, 0.8, 1.1, 1.2, 1.3]:
        for b in [0.1, 0.3, 0.7, 0.8, 0.9]:
            jobs.append({"mu": mu, "k_1": k_1, "b": b,
                         "eval_metrics": ";".join(['ndcg_cut_5', 'ndcg_cut_10', 'P_10'])})
running_jobs_containers = []
max_jobs_running = 1


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
    k_1 = job["k_1"]
    b = job["b"]

    print("starting container", mu, k_1, b)
    container = client.containers.run("ltr", detach=True, environment=[
                                      "LM_mu={mu}".format(mu=mu),
                                      "BM25_k_1={k_1}".format(k_1=k_1),
                                      "BM25_b={b}".format(b=b),
                                      "EVAL_METRIC={eval_metrics}".format(eval_metrics=job["eval_metrics"])])
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
    foldername = "milestone4/ltr/out/"+folder
    # create folder
    os.mkdir(foldername)

    # print("persisting container", container)
    # print(json.dumps(container.diff()))
    container.restart()
    while container.status != "running":
        container.reload()
    archive_data, _ = container.get_archive(
        "/app/output/results.csv")
    archive_bytes = b"".join(archive_data)
    with tarfile.open(fileobj=BytesIO(archive_bytes), mode='r') as tar:
        # Assuming there is only one file in the archive
        file_info = tar.getmembers()[0]
        file_content = tar.extractfile(file_info).read()
    with open(foldername+"/result.csv", 'w') as outfile:
        outfile.write(file_content.decode("utf-8"))

    # metadatametadata
    metadata = {"id": folder}
    metadata["mu"] = job["mu"]
    metadata["k_1"] = job["k_1"]
    metadata["b"] = job["b"]
    metadata["type"] = "ltr"
    metadata["completed"] = datetime.datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S")
    with open(foldername+"/metadata.json", 'w') as outfile:
        json.dump(metadata, outfile)
    container.stop()


main_loop()
