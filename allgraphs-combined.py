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


def plot_results(ax, data, ycolumn, xlabel, ylabel, title, filename):
    for cooperationPercent in range(0, 101, 25):
        singleDataFrame = data.loc[data['cooperation_percent']
                                   == cooperationPercent]

        ax.scatter('installations_percent', ycolumn, data=singleDataFrame,
                   color=colors[cooperationPercent], linewidth=2, label=cooperation_labels[cooperationPercent])

    ax.grid()


def main():
    fig, ax = plt.subplots(
        4, 3, sharex='col', sharey='row', figsize=(12, 6))

    plot_results(
        ax[0, 2], pv_ev_bat_data, 'voltage_factor', 'DER penetration level [%]', 'VF', 'VF, consumer node', 'PV_EV_battery VF consumer node.png')
    plot_results(ax[0, 1], pv_bat_data, 'voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, consumer node', 'PV_battery VF consumer node.png')
    plot_results(ax[0, 0], ev_bat_data, 'voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, consumer node', 'EV_battery VF consumer node.png')

    plot_results(
        ax[1, 2], pv_ev_bat_data, 'lv_voltage_factor', 'DER penetration level [%]', 'VF', 'VF, transformer node', 'PV_EV_battery VF transformer node.png')
    plot_results(ax[1, 1], pv_bat_data, 'lv_voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, transformer node', 'PV_battery VF transformer node.png')
    plot_results(ax[1, 0], ev_bat_data, 'lv_voltage_factor', 'DER penetration level [%]', 'VF',
                 'VF, transformer node', 'EV_battery VF transformer node.png')

    plot_results(
        ax[2, 2], pv_ev_bat_data, 'load_factor', 'DER penetration level [%]', 'NLF', 'NLF, consumer node', 'PV_EV_battery NLF consumer node.png')
    plot_results(ax[2, 1], pv_bat_data, 'load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, consumer node', 'PV_battery NLF consumer node.png')
    plot_results(ax[2, 0], ev_bat_data, 'load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, consumer node', 'EV_battery NLF consumer node.png')

    plot_results(
        ax[3, 2], pv_ev_bat_data, 'lv_load_factor', 'DER penetration level [%]', 'NLF', 'NLF, transformer node', 'PV_EV_battery NLF transformer node.png')
    plot_results(ax[3, 1], pv_bat_data, 'lv_load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, transformer node', 'PV_battery NLF transformer node.png')
    plot_results(ax[3, 0], ev_bat_data, 'lv_load_factor', 'DER penetration level [%]', 'NLF',
                 'NLF, transformer node', 'EV_battery NLF transformer node.png')

    plt.setp(ax[0, 2],  title="PV_EV_storage")
    plt.setp(ax[0, 1],  title="PV_storage")
    plt.setp(ax[0, 0],  title="EV_storage")

    plt.setp(ax[0, 0], ylabel="VF, \n cons. node")
    plt.setp(ax[1, 0], ylabel="VF, \n trans. node\n")
    plt.setp(ax[2, 0], ylabel="NLF, \n cons. node")
    plt.setp(ax[3, 0], ylabel="NLF, \n trans. node\n")

    plt.setp(ax[3, 0], xlabel='DER penetration level [%]')
    plt.setp(ax[3, 1], xlabel='DER penetration level [%]')
    plt.setp(ax[3, 2], xlabel='DER penetration level [%]')

    # plt.xlabel('DER penetration level [%]', fontsize=16)
    dir_path = "graphs"
    file_path = "{}/combined.png".format(dir_path)
    os.makedirs(
        dir_path, exist_ok=True)
    plt.savefig(file_path)


if __name__ == "__main__":
    main()
