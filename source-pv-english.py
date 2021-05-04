import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


result = pd.read_csv("data/source/PVProfile1440.csv",
                     sep=";", decimal=".")


result.index = result.index.astype(int)
result.sort_index()

fig, ax = plt.subplots(1, 1)

y = ['pv_output_power_kw']


result.plot(kind='line', y=y,
            ax=ax, legend=True, lw=2)

ax.xaxis.set_label_text("Time step[min]")
ax.yaxis.set_label_text("Generated power [kW]")
ax.set_title("Solar PV generation")


ax.grid()

dir_path = "graphs/source/en"
file_path = "{}/pv.png".format(dir_path)
os.makedirs(dir_path, exist_ok=True)
fig.savefig(file_path)
