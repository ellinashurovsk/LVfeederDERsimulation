import os
import pandas as pd
import matplotlib.pyplot as plt


def gen_storage(x):
    return x * (-1)


# data\results\PV_EV_battery\01-individual\storage-profiles\Storage_profile_1.csv

# result = pd.read_csv("data/results/PV_EV_battery/01-individual/storage-profiles/Storage_profile_1/energy_kWh.csv",
#                      sep=";", decimal=".")

# result = result.rename(columns={"0": "soc_percent"})
result = pd.DataFrame()

# result['energy_kWh'] = pd.read_csv("data\\results\\PV_EV_battery\\01-individual\\storage-profiles\\Storage_profile_9.csv",
#                                    sep=",", decimal=".")["energy_kWh"]

result['нагрузка'] = pd.read_csv("data/results/PV_EV_battery/01-individual/storage-profiles/Storage_profile_9.csv",
                                 sep=",", decimal=".")['load_kW']

result['электромобиль'] = pd.read_csv("data/results/PV_EV_battery/01-individual/storage-profiles/Storage_profile_9.csv",
                                      sep=",", decimal=".")['ev_kW']


result['генерация'] = pd.read_csv("data/results/PV_EV_battery/01-individual/storage-profiles/Storage_profile_9.csv",
                                  sep=",", decimal=".")['generation_kW'].apply(
    gen_storage)

result['СНЭ'] = pd.read_csv("data/results/PV_EV_battery/01-individual/storage-profiles/Storage_profile_9.csv",
                            sep=",", decimal=".")['power_kW'].apply(
    gen_storage)

result['из сети'] = pd.read_csv("data/results/PV_EV_battery/01-individual/storage-profiles/Storage_profile_9.csv",
                                sep=",", decimal=".")['flow_kW']


result.index = result.index.astype(int)
result.sort_index()
fig, ax1 = plt.subplots(1, 1)
# ax2 = ax1.twinx()
result.plot(kind='line', y=['нагрузка', 'генерация',
                            'СНЭ', 'из сети', 'электромобиль'], ax=ax1, figsize=(10, 5))
# result.plot(kind='line', y=['нагрузка', 'генерация', 'СНЭ', 'из сети'], secondary_y=[
#             'energy_kWh'], ax=ax1, figsize=(10, 5))
# result['energy_kWh'].plot(ax=ax2, style='y-')
ax1.xaxis.set_label_text("Время t×10 [мин]")
ax1.yaxis.set_label_text("Активная мощность [кВт]")
ax1.set_title("Индивидуальная оптимизация")

# ax2.legend([ax2.get_lines()[0]], ['energy_kWh'],
#            loc='upper right', bbox_to_anchor=(1., 0.825))

ax1.grid()

# plt.show()

dir_path = "graphs/min-power/ru"
file_path = "{}/min-power-graph.png".format(dir_path)
os.makedirs(dir_path, exist_ok=True)
fig.savefig(file_path)
