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
    0: '0% cooperation level',
    25: '25% cooperation level',
    50: '50% cooperation level',
    75: '75% cooperation level',
    100: '100% cooperation level'
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
    dir_path = "graphs/scatter-plots/en"
    file_path = "{}/{}".format(dir_path, filename)
    os.makedirs(
        dir_path, exist_ok=True)
    plt.savefig(file_path)


def main():
    plot_results(
        pv_ev_bat_data, 'voltage_factor', 'DER penetration level [%]', 'VF', 'VF, consumer node', 'PV_EV_battery VF consumer node.png')
    plot_results(pv_bat_data, 'voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, consumer node', 'PV_battery VF consumer node.png')
    plot_results(ev_bat_data, 'voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, consumer node', 'EV_battery VF consumer node.png')

    plot_results(
        pv_ev_bat_data, 'lv_voltage_factor', 'DER penetration level [%]', 'VF', 'VF, transformer node', 'PV_EV_battery VF transformer node.png')
    plot_results(pv_bat_data, 'lv_voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, transformer node', 'PV_battery VF transformer node.png')
    plot_results(ev_bat_data, 'lv_voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, transformer node', 'EV_battery VF transformer node.png')

    plot_results(
        pv_ev_bat_data, 'load_factor', 'DER penetration level [%]', 'NLF', 'NLF, consumer node', 'PV_EV_battery NLF consumer node.png')
    plot_results(pv_bat_data, 'load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, consumer node', 'PV_battery NLF consumer node.png')
    plot_results(ev_bat_data, 'load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, consumer node', 'EV_battery NLF consumer node.png')

    plot_results(
        pv_ev_bat_data, 'lv_load_factor', 'DER penetration level [%]', 'NLF', 'NLF, transformer node', 'PV_EV_battery NLF transformer node.png')
    plot_results(pv_bat_data, 'lv_load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, transformer node', 'PV_battery NLF transformer node.png')
    plot_results(ev_bat_data, 'lv_load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, transformer node', 'EV_battery NLF transformer node.png')


if __name__ == "__main__":
    main()
