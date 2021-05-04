import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def convert10minkWhTokW(x):
    return x * 6


result = pd.read_csv("data/source/ev_profiles/EV_home_profiles_1.csv",
                     sep=";", decimal=",")

result["load"] = result["load"].apply(convert10minkWhTokW)

result.index = result.index.astype(int)
result.sort_index()

fig, ax = plt.subplots(1, 1)

y = ['load']

result.plot(kind='line', y=y,
            ax=ax, legend=True, lw=2)

ax.xaxis.set_label_text("Time step [10 min]")
ax.yaxis.set_label_text("EV charging power [kW]")
ax.set_title("EV charging power")

ax.grid()

dir_path = "graphs/source/en"
file_path = "{}/ev.png".format(dir_path)
os.makedirs(dir_path, exist_ok=True)
fig.savefig(file_path)
