import glob
import json
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

datas = []
k_1 = set()
b = set()

for folder in glob.glob("out/*/"):
    with open(folder+"metadata.json", 'r') as f:
        data = json.load(f)
    data['k_1'] = round(data['k_1'], 10)
    data['b'] = round(data['b'], 10)
    pandas_data = pd.read_csv(folder+"validation.csv")
    value = pandas_data.iloc[0]['ndcg_cut_5']
    data['ndcg_cut_5'] = value
    datas.append(data)

for data in datas:
    k_1.add(data['k_1'])
    b.add(data['b'])

values = {}
for k_1_ in k_1:
    for b_ in b:
        values[(k_1_, b_)] = []

for data in datas:
    k_1_ = round(data['k_1'], 10)
    b_ = round(data['b'], 10)
    values[(k_1_, b_)].append(data['ndcg_cut_5'])

results = []
for k_1_ in sorted(k_1):
    for b_ in sorted(b):
        value = values[(k_1_, b_)][0]
        # make high values more visible
        value = 2**(value*100)
        result = (k_1_, b_, value)
        results.append(result)

# Create a DataFrame from the results
df = pd.DataFrame(results, columns=['k_1', 'b', 'value'])

# Pivot the DataFrame to create a matrix suitable for heatmap
heatmap_data = df.pivot(index='k_1', columns='b', values='value')

# Plotting the heatmap
plt.figure(figsize=(10, 6))
plt.imshow(heatmap_data, cmap='Greens', interpolation='nearest')
plt.colorbar(label='Values')
plt.xticks(np.arange(len(heatmap_data.columns)), heatmap_data.columns)
plt.yticks(np.arange(len(heatmap_data.index)), heatmap_data.index)
plt.xlabel('b')
plt.ylabel('k_1')
plt.title('Heatmap of Values')
plt.show()
