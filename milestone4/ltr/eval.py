import json
import glob
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np


def lm_get_all_configs():
    mu = set()
    for folder in glob.glob("input/lm/*"):

        with open(folder+"/metadata.json") as f:
            config = json.load(f)
            mu.add(config["mu"])
        #    config = json.load(f)
        #    print(config)
    return mu


def bm25_get_all_configs():
    k_1 = set()
    b = set()
    for folder in glob.glob("input/bm25/*"):

        with open(folder+"/metadata.json") as f:
            config = json.load(f)
            k_1.add(config["k_1"])
            b.add(config["b"])
    return k_1, b


def ltr_get_all_configs():
    mu = set()
    k_1 = set()
    b = set()
    for folder in glob.glob("out/*"):

        with open(folder+"/metadata.json") as f:
            config = json.load(f)
            mu.add(config["mu"])
            k_1.add(config["k_1"])
            b.add(config["b"])
    return mu, k_1, b


def bm25_check_all_configs():
    k_1s, bs = bm25_get_all_configs()
    ret = True
    for k_1 in k_1s:
        for b in bs:
            exists = False
            for folder in glob.glob("input/bm25/*"):
                with open(folder+"/metadata.json") as f:
                    config = json.load(f)
                    if config["k_1"] == k_1 and config["b"] == b:
                        exists = True
            if not exists:
                print("missing", k_1, b)
                ret = False
    return ret


def ltr_check_all_configs():
    count = 0
    mus, k_1s, bs = ltr_get_all_configs()
    ret = True
    for mu in mus:
        for k_1 in k_1s:
            for b in bs:
                exists = False
                for folder in glob.glob("out/*"):
                    with open(folder+"/metadata.json") as f:
                        config = json.load(f)
                        if config["mu"] == mu and config["k_1"] == k_1 and config["b"] == b:
                            exists = True
                if not exists:
                    print("missing", mu, k_1, b)
                    count += 1
                    ret = False
    if count > 0:
        print(count, "missing configs")
    return ret


def lm_get_scores():
    scores = {}
    mus = lm_get_all_configs()
    for mu in mus:
        for folder in glob.glob("input/lm/*"):
            with open(folder+"/metadata.json") as f:
                config = json.load(f)
                if config["mu"] == mu:
                    df = pd.read_csv(folder+"/validation.csv")
                    scores[mu] = {}
                    for score in ["ndcg_cut_5", "ndcg_cut_10", "P_10"]:
                        scores[mu][score] = df[score][0]
    return scores
    #    config = json.load(f)
    #    print(config)


def bm25_get_scores():
    scores = {}
    k_1s, bs = bm25_get_all_configs()
    for k_1 in k_1s:
        scores[k_1] = {}
        for b in bs:
            scores[k_1][b] = {}
    for folder in glob.glob("input/bm25/*"):
        with open(folder+"/metadata.json") as f:
            config = json.load(f)
            k_1 = config["k_1"]
            b = config["b"]
            df = pd.read_csv(folder+"/validation.csv")
            for score in ["ndcg_cut_5", "ndcg_cut_10", "P_10"]:
                scores[k_1][b][score] = df[score][0]
    return scores


def ltr_get_scores():
    scores = {}
    mus, k_1s, bs = ltr_get_all_configs()

    for mu in mus:
        scores[mu] = {}
        for k_1 in k_1s:
            scores[mu][k_1] = {}
            for b in bs:
                scores[mu][k_1][b] = {}
    for folder in glob.glob("out/*"):
        with open(folder+"/metadata.json") as f:
            config = json.load(f)
            mu = config["mu"]
            k_1 = config["k_1"]
            b = config["b"]
            df = pd.read_csv(folder+"/result.csv")
            for score in ["ndcg_cut_5", "ndcg_cut_10", "P_10"]:
                for model in ["lm", "bm25", "ltr"]:
                    if model == "lm":
                        scores[mu][k_1][b][model+"_"+score] = df[score][1]
                    if model == "bm25":
                        scores[mu][k_1][b][model+"_"+score] = df[score][0]
                    if model == "ltr":
                        scores[mu][k_1][b][model+"_"+score] = df[score][2]
    return scores


def lm_visualise():
    scores = lm_get_scores()
    for score in ["ndcg_cut_5", "ndcg_cut_10", "P_10"]:
        x_values = sorted(list(scores.keys()))
        print([scores[x].keys() for x in x_values])
        y_values = [scores[x][score] for x in x_values]

        plt.figure(figsize=(10, 6))
        plt.plot(x_values, y_values, marker='o', linestyle='-', color='green')
        plt.title(score + ' Values Over Keys')
        plt.xlabel('Keys')
        plt.ylabel(score + ' Values')
        os.makedirs("fig/lm", exist_ok=True)
        os.makedirs("fig", exist_ok=True)
        plt.savefig("fig/lm/"+score+".png")


def bm25_visualise():
    scores = bm25_get_scores()

    for score in ["ndcg_cut_5", "ndcg_cut_10", "P_10"]:
        results = []
        for k_1 in sorted(scores):
            for b in sorted(scores[k_1]):
                value = scores[k_1][b][score]
                # make high values more visible
                result = (k_1, b, value)
                results.append(result)

        df = pd.DataFrame(results, columns=['k_1', 'b', 'value'])

        # Pivot the DataFrame to create a matrix suitable for heatmap
        heatmap_data = df.pivot(index='k_1', columns='b', values='value')

        # Plotting the heatmap
        plt.figure(figsize=(14, 10))
        plt.imshow(heatmap_data, cmap='Greens', interpolation='nearest')
        plt.colorbar(label='Values')
        plt.xticks(np.arange(len(heatmap_data.columns)), heatmap_data.columns)
        plt.yticks(np.arange(len(heatmap_data.index)), heatmap_data.index)
        plt.xlabel('b')
        plt.ylabel('k_1')
        plt.title('Heatmap of Values')
        os.makedirs("fig", exist_ok=True)
        os.makedirs("fig/bm25", exist_ok=True)
        plt.savefig("fig/bm25/"+score+".png")


def bm25_tablelise():
    k_1s, bs = bm25_get_all_configs()
    scores = bm25_get_scores()
    l = []
    for k_1 in sorted(k_1s):
        for b in sorted(bs):
            ndcg_cut_10 = scores[k_1][b]["ndcg_cut_10"]
            ndcg_cut_5 = scores[k_1][b]["ndcg_cut_5"]
            p_10 = scores[k_1][b]["P_10"]
            l.append([k_1, b, ndcg_cut_10, ndcg_cut_5, p_10])
    df = pd.DataFrame(
        l, columns=['k_1', 'b', 'ndcg_cut_10', 'ndcg_cut_5', 'p_10'])
    os.makedirs("table", exist_ok=True)
    os.makedirs("table/bm25", exist_ok=True)
    df.to_csv("table/bm25/table.csv", index=False)


def lm_tablelise():
    mus = lm_get_all_configs()
    scores = lm_get_scores()
    l = []
    for mu in sorted(mus):
        ndcg_cut_10 = scores[mu]["ndcg_cut_10"]
        ndcg_cut_5 = scores[mu]["ndcg_cut_5"]
        p_10 = scores[mu]["P_10"]
        l.append([mu, ndcg_cut_10, ndcg_cut_5, p_10])
    df = pd.DataFrame(
        l, columns=['mu', 'ndcg_cut_10', 'ndcg_cut_5', 'p_10'])
    os.makedirs("table", exist_ok=True)
    os.makedirs("table/lm", exist_ok=True)
    df.to_csv("table/lm/table.csv", index=False)


def ltr_tablelise():
    mus, k_1s, bs = ltr_get_all_configs()
    scores = ltr_get_scores()
    l = []
    for mu in sorted(mus):
        for k_1 in sorted(k_1s):
            for b in sorted(bs):
                if b == 0.75:
                    continue

                bm25_ndcg_cut_10 = scores[mu][k_1][b]["bm25_ndcg_cut_10"]
                bm25_ndcg_cut_5 = scores[mu][k_1][b]["bm25_ndcg_cut_5"]
                bm25_p_10 = scores[mu][k_1][b]["bm25_P_10"]

                lm_ndcg_cut_10 = scores[mu][k_1][b]["lm_ndcg_cut_10"]
                lm_ndcg_cut_5 = scores[mu][k_1][b]["lm_ndcg_cut_5"]
                lm_p_10 = scores[mu][k_1][b]["lm_P_10"]

                ltr_ndcg_cut_10 = scores[mu][k_1][b]["ltr_ndcg_cut_10"]
                ltr_ndcg_cut_5 = scores[mu][k_1][b]["ltr_ndcg_cut_5"]
                ltr_p_10 = scores[mu][k_1][b]["ltr_P_10"]

                l.append([mu, k_1, b,
                          bm25_ndcg_cut_10, bm25_ndcg_cut_5, bm25_p_10,
                          lm_ndcg_cut_10, lm_ndcg_cut_5, lm_p_10,
                          ltr_ndcg_cut_10, ltr_ndcg_cut_5, ltr_p_10])
    for mu in [2500]:
        for k_1 in [1.2]:
            for b in [0.75]:

                bm25_ndcg_cut_10 = scores[mu][k_1][b]["bm25_ndcg_cut_10"]
                bm25_ndcg_cut_5 = scores[mu][k_1][b]["bm25_ndcg_cut_5"]
                bm25_p_10 = scores[mu][k_1][b]["bm25_P_10"]

                lm_ndcg_cut_10 = scores[mu][k_1][b]["lm_ndcg_cut_10"]
                lm_ndcg_cut_5 = scores[mu][k_1][b]["lm_ndcg_cut_5"]
                lm_p_10 = scores[mu][k_1][b]["lm_P_10"]

                ltr_ndcg_cut_10 = scores[mu][k_1][b]["ltr_ndcg_cut_10"]
                ltr_ndcg_cut_5 = scores[mu][k_1][b]["ltr_ndcg_cut_5"]
                ltr_p_10 = scores[mu][k_1][b]["ltr_P_10"]

                l.append([mu, k_1, b,
                          bm25_ndcg_cut_10, bm25_ndcg_cut_5, bm25_p_10,
                          lm_ndcg_cut_10, lm_ndcg_cut_5, lm_p_10,
                          ltr_ndcg_cut_10, ltr_ndcg_cut_5, ltr_p_10])
    df = pd.DataFrame(
        l, columns=['mu', 'k_1', 'b', 'bm25_ndcg_cut_10', 'bm25_ndcg_cut_5', 'bm25_p_10', 'lm_ndcg_cut_10', 'lm_ndcg_cut_5', 'lm_p_10', 'ltr_ndcg_cut_10', 'ltr_ndcg_cut_5', 'ltr_p_10'])
    os.makedirs("table", exist_ok=True)
    os.makedirs("table/ltr", exist_ok=True)
    df.to_csv("table/ltr/table.csv", index=False)


ltr_tablelise()
