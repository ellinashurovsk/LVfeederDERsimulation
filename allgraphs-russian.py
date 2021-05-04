import os
import pandas as pd
import matplotlib.pyplot as plt

pv_ev_bat_data = pd.read_csv("data/results/PV_EV_battery/04-graph-data/graph-data.csv",
                             sep=",", decimal=".")

pv_bat_data = pd.read_csv("data/results/PV_battery/04-graph-data/graph-data.csv",
                          sep=",", decimal=".")

ev_bat_data = pd.read_csv("data/results/EV_battery/04-graph-data/graph-data.csv",
                          sep=",", decimal=".")


pv_ev_bat_data.index = pv_ev_bat_data.index.astype(int)
pv_ev_bat_data.sort_index()

pv_bat_data.index = pv_bat_data.index.astype(int)
pv_bat_data.sort_index()

ev_bat_data.index = ev_bat_data.index.astype(int)
ev_bat_data.sort_index()

colors = {
    0: 'red',
    25: 'blue',
    50: 'yellow',
    75: 'orange',
    100: 'green'
}

cooperation_labels = {
    0: '0% коллективной оптимизации',
    25: '25% коллективной оптимизации',
    50: '50% коллективной оптимизации',
    75: '75% коллективной оптимизации',
    100: '100% коллективной оптимизации'
}


def plot_results(data, ycolumn, xlabel, ylabel, title, filename):
    fig, ax = plt.subplots()

    for cooperationPercent in range(0, 101, 25):
        singleDataFrame = data.loc[data['cooperation_percent']
                                   == cooperationPercent]

        ax.scatter('installations_percent', ycolumn, data=singleDataFrame,
                   color=colors[cooperationPercent], linewidth=2, label=cooperation_labels[cooperationPercent])

    plt.grid()
    plt.legend(loc="upper left")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    dir_path = "graphs/scatter-plots/ru"
    file_path = "{}/{}".format(dir_path, filename)
    os.makedirs(
        dir_path, exist_ok=True)
    plt.savefig(file_path)


def main():
    plot_results(
        pv_ev_bat_data, 'voltage_factor', 'Уровень распределенных энергоресурсов [%]', 'Ku', 'Ku, на шине потребителя', 'PV_EV_battery Ku на шине потребителя.png')
    plot_results(pv_bat_data, 'voltage_factor', 'Уровень распределенных энергоресурсов [%]', 'Ku',
                 'Ku, на шинах потребителя', 'PV_battery Ku на шине потребителя.png')
    plot_results(ev_bat_data, 'voltage_factor', 'Уровень распределенных энергоресурсов [%]', 'Ku',
                 'Ku, на шинах потребителя', 'EV_battery Ku на шине потребителя.png')

    plot_results(
        pv_ev_bat_data, 'lv_voltage_factor', 'Уровень распределенных энергоресурсов [%]', 'Ku', 'Ku, на шине НН трансформатора', 'PV_EV_battery Ku на шине НН трансформатора.png')
    plot_results(pv_bat_data, 'lv_voltage_factor', 'Уровень распределенных энергоресурсов [%]', 'Ku',
                 'Ku, на шине НН трансформатора', 'PV_battery Ku на шине НН трансформатора.png')
    plot_results(ev_bat_data, 'lv_voltage_factor', 'Уровень распределенных энергоресурсов [%]', 'Ku',
                 'Ku, на шине НН трансформатора', 'EV_battery Ku на шине НН трансформатора.png')

    plot_results(
        pv_ev_bat_data, 'load_factor', 'Уровень распределенных энергоресурсов [%]', 'Kp', 'Kp, на шине потребителя', 'PV_EV_battery Kp на шине потребителя.png')
    plot_results(pv_bat_data, 'load_factor', 'Уровень распределенных энергоресурсов [%]', 'Kp',
                 'Kp, на шине потребителя', 'PV_battery Kp на шине потребителя.png')
    plot_results(ev_bat_data, 'load_factor', 'Уровень распределенных энергоресурсов [%]', 'Kp',
                 'Kp, на шине потребителя', 'EV_battery Kp на шине потребителя.png')

    plot_results(
        pv_ev_bat_data, 'lv_load_factor', 'Уровень распределенных энергоресурсов [%]', 'Kp', 'Kp, на шине НН трансформатора', 'PV_EV_battery Kp на шине НН трансформатора.png')
    plot_results(pv_bat_data, 'lv_load_factor', 'Уровень распределенных энергоресурсов [%]', 'Kp',
                 'Kp, на шине НН трансформатора', 'PV_battery Kp на шине НН трансформатора.png')
    plot_results(ev_bat_data, 'lv_load_factor', 'Уровень распределенных энергоресурсов [%]', 'Kp',
                 'Kp, на шине НН трансформатора', 'EV_battery Kp на шине НН трансформатора.png')


if __name__ == "__main__":
    main()
