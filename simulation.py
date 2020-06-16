import math
import os
import sys
from functools import partial
from itertools import repeat
from multiprocessing import Pool

import cvxpy
import pandapower
import pandapower.timeseries.data_sources.frame_data as frame_data
import pandas
from pandapower.control import ConstControl
from pandapower.networks import ieee_european_lv_asymmetric
from pandapower.timeseries import OutputWriter
from pandapower.timeseries.run_time_series import run_timeseries

scenarios = [
    {
        'PV': True
    },
    {
        'EV': True
    },
    {
        'PV': True,
        'EV': True
    }
]


SKIP_EXISTING = True
PRINT_SKIPPING_LINES = False
DER_INSTALLATIONS_PERCENT_STEP = 10
DER_COOPERATION_PERCENT_STEP = 25
BUS_LIMIT = 55

# для отладки можно закомментить сроки сверху и раскомментить эти:

# SKIP_EXISTING = False
# PRINT_SKIPPING_LINES = False
# DER_INSTALLATIONS_PERCENT_STEP = 50
# DER_COOPERATION_PERCENT_STEP = 50
# BUS_LIMIT = 5

T = 144
INTERVAL_LENGTH = 1.0/6.0  # hours (1/6 hour = 10 minutes)
BATTERY_ENERGY_MAX = 7.7  # kWh
RATED_P = 3.0  # kW
INITIAL_BATTERY_CHARGE = 3.85  # kWh
CHARGE_EFFICIENCY = 0.92
DISCHARGE_EFFICIENCY = 0.92

net_structure = ieee_european_lv_asymmetric('on_peak_566')

buses = pandas.read_csv('data/source/buses.csv',
                        sep=";", decimal=',')[:BUS_LIMIT]
buses_nodes = buses['bus'].tolist()

line_nodes = []

print("Obtaining line indices...")

for _, bus in buses.iterrows():
    for line_index, line in net_structure.line.iterrows():
        if bus.bus == line.to_bus:
            line_nodes.append(line_index)


def convertkWToMW(x):
    return x * 0.001


def convertStorage(x):
    return -1 * x


def get_scenario_name(scenario):
    result = []

    if scenario.get('PV') == True:
        result.append("PV")

    if scenario.get('EV') == True:
        result.append("EV")

    result.append("battery")

    return '_'.join(result)


def get_installation_buses_dataframe(installations_percent):
    offset = math.floor(installations_percent * buses.count() / 100)
    return buses[0:offset]


def get_cooperation_buses_dataframe(installations_buses_dataframe, cooperation_percent):
    offset = math.floor(cooperation_percent *
                        installations_buses_dataframe.count() / 100)
    return [
        # nodes that cooperate
        installations_buses_dataframe[0:offset],
        # nodes that use individual peak-shaving
        installations_buses_dataframe[offset:]
    ]


def compute_individual_optimization_fast(scenario, x):
    scenario_name = get_scenario_name(scenario)

    full_dir_path = "data/results/{}/01-individual/storage-profiles".format(
        scenario_name)

    if os.path.exists(full_dir_path) and SKIP_EXISTING:
        if PRINT_SKIPPING_LINES:
            print("[{}] Computing individual optimization... [skipping]".format(
                scenario_name))
        return False

    print("[{}] Computing individual optimization...".format(
        scenario_name))

    power = 0
    N = buses.size

    p = cvxpy.Variable((N, T))
    E = cvxpy.Variable((N, T))
    pChg = cvxpy.Variable((N, T))
    pDischg = cvxpy.Variable((N, T))
    z = cvxpy.Variable((N, T), boolean=True)

    constraints = [
        E >= 0,
        E <= BATTERY_ENERGY_MAX,
        pChg <= 0.0,
        0.0 <= pDischg,
    ]

    result_dfs = []
    loadProfiles = []
    pvProfiles = []
    evProfiles = []

    for n in buses.index:
        current_df = pandas.DataFrame()
        result_dfs.append(current_df)

        constraints += [
            p[n] == pChg[n] + pDischg[n],
            (z[n] - 1.0) * RATED_P <= pChg[n],
            pDischg[n] <= z[n] * RATED_P,
            E[n][0] - INITIAL_BATTERY_CHARGE + (pChg[n][0] * CHARGE_EFFICIENCY + pDischg[n]
                                                [0] * DISCHARGE_EFFICIENCY) * INTERVAL_LENGTH == 0,
            E[n][T-1] - INITIAL_BATTERY_CHARGE + (pChg[n][T-1] * CHARGE_EFFICIENCY + pDischg[n]
                                                  [T-1] * DISCHARGE_EFFICIENCY) * INTERVAL_LENGTH == 0,
            E[n][0] == E[n][T-1]
        ]

        load_profile_raw = pandas.read_csv(
            "data/source/load_profiles/Load_profile_{}.csv".format(n + 1), sep=",", decimal=".")
        loadProfile = load_profile_raw["mult"].iloc[::10].reset_index(
            drop=True)

        loadProfiles.append(loadProfile)

        pv_profile_raw = pandas.read_csv(
            "data/source/PVProfile1440.csv", sep=";", decimal=".")
        pvProfile = pv_profile_raw["pv_output_power_kw"].iloc[::10].reset_index(
            drop=True)

        pvProfiles.append(pvProfile)

        ev_profile_raw = pandas.read_csv(
            "data/source/ev_profiles/EV_home_profiles_{}.csv".format(n + 1), sep=";", decimal=",")
        evProfile = ev_profile_raw["load"]

        evProfiles.append(evProfile)

        current_df["load_kW"] = loadProfile

        if scenario.get('PV') == True:
            current_df["generation_kW"] = pvProfile

        if scenario.get('EV') == True:
            current_df["ev_kW"] = evProfile

        for t in range(0, T - 1):
            constraints += [
                E[n][t+1] == E[n][t] - (pChg[n][t] * CHARGE_EFFICIENCY +
                                        pDischg[n][t] * DISCHARGE_EFFICIENCY) * INTERVAL_LENGTH
            ]

    for t in range(0, T - 1):
        for n in buses.index:
            if scenario.get('PV') == True and scenario.get('EV') == True:
                power += cvxpy.square(loadProfiles[n][t] +
                                      evProfiles[n][t] - pvProfiles[n][t] - p[n][t])
            elif scenario.get('PV') == True:
                power += cvxpy.square(loadProfiles[n]
                                      [t] - pvProfiles[n][t] - p[n][t])
            elif scenario.get('EV') == True:
                power += cvxpy.square(loadProfiles[n]
                                      [t] + evProfiles[n][t] - p[n][t])

    obj = cvxpy.Minimize(power)
    prob = cvxpy.Problem(obj, constraints)

    prob.solve(solver=cvxpy.ECOS_BB)

    os.makedirs(
        full_dir_path, exist_ok=True)

    for n in buses.index:
        current_df = result_dfs[n]

        current_df["power_kW"] = p[n][:].value.round(3)

        flow = []

        for t in range(0, T):
            lp = loadProfiles[n][t]
            pv = pvProfiles[n][t]
            ev = evProfiles[n][t]
            pp = p[n][t].value

            if scenario.get('PV') == True and scenario.get('EV') == True:
                flow.append(lp + ev - pv - pp)
            elif scenario.get('PV') == True:
                flow.append(lp - pv - pp)
            elif scenario.get('EV') == True:
                flow.append(lp + ev - pp)

        current_df["flow_kW"] = pandas.DataFrame(flow).round(3)

        current_df["energy_kWh"] = E[n][:].value.round(3)

        current_df.to_csv(
            "{}/Storage_profile_{}.csv".format(full_dir_path, n + 1))

    return True


def compute_cooperative_optimization(scenario, installations_percent, cooperation_percent, cooperating_buses):
    scenario_name = get_scenario_name(scenario)

    full_dir_path = "data/results/{}/02-collective/{}_installations/{}_cooperation".format(
        scenario_name, installations_percent, cooperation_percent)

    if os.path.exists(full_dir_path) and SKIP_EXISTING:
        if PRINT_SKIPPING_LINES:
            print("[{}] [{}%] [{}%] Computing cooperative optimization... [skipping]".format(
                scenario_name, installations_percent, cooperation_percent))
        return False

    print("[{}] [{}%] [{}%] Computing cooperative optimization...".format(
        scenario_name, installations_percent, cooperation_percent))

    power = 0
    N = cooperating_buses.size

    p = cvxpy.Variable((N, T))
    E = cvxpy.Variable((N, T))
    pChg = cvxpy.Variable((N, T))
    pDischg = cvxpy.Variable((N, T))
    z = cvxpy.Variable((N, T), boolean=True)

    constraints = [
        E >= 0,
        E <= BATTERY_ENERGY_MAX,
        pChg <= 0.0,
        0.0 <= pDischg,
    ]

    result_dfs = []
    loadProfiles = []
    pvProfiles = []
    evProfiles = []

    for n in cooperating_buses.index:
        current_df = pandas.DataFrame()
        result_dfs.append(current_df)

        constraints += [
            p[n] == pChg[n] + pDischg[n],
            (z[n] - 1.0) * RATED_P <= pChg[n],
            pDischg[n] <= z[n] * RATED_P,
            E[n][0] - INITIAL_BATTERY_CHARGE + (pChg[n][0] * CHARGE_EFFICIENCY + pDischg[n]
                                                [0] * DISCHARGE_EFFICIENCY) * INTERVAL_LENGTH == 0,
            E[n][T-1] - INITIAL_BATTERY_CHARGE + (pChg[n][T-1] * CHARGE_EFFICIENCY + pDischg[n]
                                                  [T-1] * DISCHARGE_EFFICIENCY) * INTERVAL_LENGTH == 0,
            E[n][0] == E[n][T-1]
        ]

        load_profile_raw = pandas.read_csv(
            "data/source/load_profiles/Load_profile_{}.csv".format(n + 1), sep=",", decimal=".")
        loadProfile = load_profile_raw["mult"].iloc[::10].reset_index(
            drop=True)

        loadProfiles.append(loadProfile)

        pv_profile_raw = pandas.read_csv(
            "data/source/PVProfile1440.csv", sep=";", decimal=".")
        pvProfile = pv_profile_raw["pv_output_power_kw"].iloc[::10].reset_index(
            drop=True)

        pvProfiles.append(pvProfile)

        ev_profile_raw = pandas.read_csv(
            "data/source/ev_profiles/EV_home_profiles_{}.csv".format(n + 1), sep=";", decimal=",")
        evProfile = ev_profile_raw["load"]

        evProfiles.append(evProfile)

        current_df["load_kW"] = loadProfile

        if scenario.get('PV') == True:
            current_df["generation_kW"] = pvProfile

        if scenario.get('EV') == True:
            current_df["ev_kW"] = evProfile

        for t in range(0, T - 1):
            constraints += [
                E[n][t+1] == E[n][t] - (pChg[n][t] * CHARGE_EFFICIENCY +
                                        pDischg[n][t] * DISCHARGE_EFFICIENCY) * INTERVAL_LENGTH
            ]

    for t in range(0, T - 1):
        power_tmp = 0
        for n in cooperating_buses.index:
            if scenario.get('PV') == True and scenario.get('EV') == True:
                power_tmp += (loadProfiles[n][t] +
                              evProfiles[n][t] - pvProfiles[n][t] - p[n][t])
            elif scenario.get('PV') == True:
                power_tmp += (loadProfiles[n]
                                          [t] - pvProfiles[n][t] - p[n][t])
            elif scenario.get('EV') == True:
                power_tmp += (loadProfiles[n]
                              [t] + evProfiles[n][t] - p[n][t])
        power += cvxpy.square(power_tmp)

    obj = cvxpy.Minimize(power)
    prob = cvxpy.Problem(obj, constraints)

    prob.solve(solver=cvxpy.ECOS_BB)

    os.makedirs(
        full_dir_path, exist_ok=True)

    for n in cooperating_buses.index:
        current_df = result_dfs[n]

        current_df["power_kW"] = p[n][:].value.round(3)

        flow = []

        for t in range(0, T):
            lp = loadProfiles[n][t]
            pv = pvProfiles[n][t]
            ev = evProfiles[n][t]
            pp = p[n][t].value

            if scenario.get('PV') == True and scenario.get('EV') == True:
                flow.append(lp + ev - pv - pp)
            elif scenario.get('PV') == True:
                flow.append(lp - pv - pp)
            elif scenario.get('EV') == True:
                flow.append(lp + ev - pp)

        current_df["flow_kW"] = pandas.DataFrame(flow).round(3)

        current_df["energy_kWh"] = E[n][:].value.round(3)

        current_df.to_csv(
            "{}/Storage_profile_{}.csv".format(full_dir_path, n + 1))

    return True


def simulate_network(scenario, installations_percent, cooperation_percent, installation_buses, cooperating_buses, individual_buses):
    scenario_name = get_scenario_name(scenario)

    full_dir_path = "data/results/{}/03-simulation/{}_installations/{}_cooperative".format(
        scenario_name, installations_percent, cooperation_percent
    )

    if os.path.exists(full_dir_path) and SKIP_EXISTING:
        if PRINT_SKIPPING_LINES:
            print("[{}] [{}%] [{}%] Simulating network... [skipping]".format(
                scenario_name, installations_percent, cooperation_percent))
        return False

    print("[{}] [{}%] [{}%] Simulating network...".format(
        scenario_name, installations_percent, cooperation_percent))

    net = ieee_european_lv_asymmetric('on_peak_566')

    for index, _ in net.asymmetric_load.iterrows():
        net.asymmetric_load.in_service.at[index] = False

    pandapower.runpp(net)

    for original_index, row in buses.iterrows():
        load_index = pandapower.create_load(net, bus=row.bus, p_mw=0)
        load_profile_raw = pandas.read_csv(
            "data/source/load_profiles/Load_profile_{}.csv".format(original_index+1), sep=",", decimal="."
        )
        load_profile_raw['mult'] = load_profile_raw['mult'].apply(
            convertkWToMW).iloc[::10].reset_index(drop=True)
        load_profile = frame_data.DFData(pandas.DataFrame(load_profile_raw))
        load_controller = ConstControl(
            net, element='load', element_index=load_index, variable='p_mw', data_source=load_profile, profile_name='mult', recycle=False
        )

    for original_index, row in installation_buses.iterrows():
        if scenario.get('EV') == True:
            ev_index = pandapower.create_load(net, bus=row.bus, p_mw=0)
            ev_profile_raw = pandas.read_csv(
                "data/source/ev_profiles/EV_home_profiles_{}.csv".format(original_index+1), sep=";", decimal=","
            )
            ev_profile_raw['load'] = ev_profile_raw['load'].apply(
                convertkWToMW)
            ev_profile = frame_data.DFData(pandas.DataFrame(ev_profile_raw))
            ev_controller = ConstControl(
                net, element='load', element_index=ev_index, variable='p_mw', data_source=ev_profile, profile_name='load', recycle=False
            )

        if scenario.get('PV') == True:
            sgen_index = pandapower.create_sgen(
                net, bus=row.bus, p_mw=0, sn_mva=0, type='PV')
            pv_profile_raw = pandas.read_csv(
                "data/source/PVProfile1440.csv", sep=";", decimal=".")
            pv_profile_raw['pv_output_power_kw'] = pv_profile_raw['pv_output_power_kw'].apply(
                convertkWToMW).iloc[::10].reset_index(drop=True)
            pv_profile = frame_data.DFData(pandas.DataFrame(pv_profile_raw))
            sgen_controller = ConstControl(
                net, element='sgen', element_index=sgen_index, variable='p_mw',
                data_source=pv_profile, profile_name='pv_output_power_kw',
                recycle=False)

    for original_index, row in cooperating_buses.iterrows():
        storage_index = pandapower.create_storage(
            net, bus=row.bus, p_mw=0, max_e_mwh=BATTERY_ENERGY_MAX/1000.0, soc_percent=(INITIAL_BATTERY_CHARGE/BATTERY_ENERGY_MAX)*100.0, max_p_mw=RATED_P/1000.0, min_p_mw=-RATED_P/1000.0)
        storage_profile_raw = pandas.read_csv(
            "data/results/{}/02-collective/{}_installations/{}_cooperation/Storage_profile_{}.csv".format(
                scenario_name,
                installations_percent,
                cooperation_percent,
                original_index + 1
            ), sep=",", decimal=".")
        storage_profile_raw['power_kW'] = storage_profile_raw['power_kW'].apply(
            convertkWToMW).apply(convertStorage)
        storage_profile = frame_data.DFData(
            pandas.DataFrame(storage_profile_raw))
        storage_controller = ConstControl(
            net,
            element='storage',
            element_index=storage_index,
            variable='p_mw',
            data_source=storage_profile,
            profile_name='power_kW',
            recycle=False
        )

    for original_index, row in individual_buses.iterrows():
        storage_index = pandapower.create_storage(
            net, bus=row.bus, p_mw=0, max_e_mwh=BATTERY_ENERGY_MAX/1000.0, soc_percent=(INITIAL_BATTERY_CHARGE/BATTERY_ENERGY_MAX)*100.0, max_p_mw=RATED_P/1000.0, min_p_mw=-RATED_P/1000.0)
        storage_profile_raw = pandas.read_csv(
            "data/results/{}/01-individual/storage-profiles/Storage_profile_{}.csv".format(
                scenario_name,
                original_index + 1
            ), sep=",", decimal=".")
        storage_profile_raw['power_kW'] = storage_profile_raw['power_kW'].apply(
            convertkWToMW).apply(convertStorage)
        storage_profile = frame_data.DFData(
            pandas.DataFrame(storage_profile_raw))
        storage_controller = ConstControl(
            net,
            element='storage',
            element_index=storage_index,
            variable='p_mw',
            data_source=storage_profile,
            profile_name='power_kW',
            recycle=False
        )

    time_steps = range(0, T)

    ow = OutputWriter(
        net, output_path=full_dir_path, output_file_type=".csv", log_variables=[])

    ow.log_variable("load", "p_mw")
    ow.log_variable("res_bus", "vm_pu", index=buses_nodes)
    ow.log_variable("res_line", "p_to_mw", index=line_nodes)
    ow.log_variable("res_trafo", "vm_lv_pu")
    ow.log_variable("res_trafo", "p_lv_mw")

    if scenario.get('PV') == True:
        ow.log_variable("sgen", "p_mw")

    if cooperating_buses.size > 0 or individual_buses.size > 0:
        ow.log_variable("storage", "p_mw")

    run_timeseries(net, time_steps, continue_on_divergence=True, verbose=False)

    return True


def compute_graph_data(scenario, x):
    scenario_name = get_scenario_name(scenario)

    full_dir_path = "data/results/{}/04-graph-data".format(scenario_name)

    if os.path.exists(full_dir_path) and SKIP_EXISTING:
        if PRINT_SKIPPING_LINES:
            print("[{}] Computing graph data... [skipping]".format(
                scenario_name))
        return False

    print("[{}] Computing graph data...".format(
        scenario_name))

    result = pandas.DataFrame(columns=[
                              'installations_percent', 'cooperation_percent', 'load_factor', 'voltage_factor', 'lv_load_factor', 'lv_voltage_factor'])

    for i in range(0, 101, DER_INSTALLATIONS_PERCENT_STEP):
        for c in range(0, 101, DER_COOPERATION_PERCENT_STEP):
            vm_pu_raw = pandas.read_csv(
                "data/results/{}/03-simulation/{}_installations/{}_cooperative/res_bus/vm_pu.csv".format(scenario_name, i, c), sep=";", decimal=".")
            p_to_mw_raw = pandas.read_csv(
                "data/results/{}/03-simulation/{}_installations/{}_cooperative/res_line/p_to_mw.csv".format(scenario_name, i, c), sep=";", decimal=".")

            vm_lv_pu_raw = pandas.read_csv(
                "data/results/{}/03-simulation/{}_installations/{}_cooperative/res_trafo/vm_lv_pu.csv".format(scenario_name, i, c), sep=";", decimal=".")
            p_lv_mw_raw = pandas.read_csv(
                "data/results/{}/03-simulation/{}_installations/{}_cooperative/res_trafo/p_lv_mw.csv".format(scenario_name, i, c), sep=";", decimal=".")

            vm_pu_raw_clear_abs = vm_pu_raw.loc[:, vm_pu_raw.columns[1]:].abs()
            p_to_mw_raw_clear_abs = p_to_mw_raw.loc[:,
                                                    p_to_mw_raw.columns[1]:].abs()

            vm_lv_pu_raw_clear_abs = vm_lv_pu_raw.loc[:,
                                                      vm_lv_pu_raw.columns[1]:].abs()
            p_lv_mw_raw_clear_abs = p_lv_mw_raw.loc[:,
                                                    p_lv_mw_raw.columns[1]:].abs()

            vm_pu_abs_max = vm_pu_raw_clear_abs.max().max()
            vm_pu_abs_mean = vm_pu_raw_clear_abs.mean().mean()

            p_to_mw_abs_max = p_to_mw_raw_clear_abs.max().max()
            p_to_mw_abs_mean = p_to_mw_raw_clear_abs.mean().mean()

            vm_lv_pu_abs_max = vm_lv_pu_raw_clear_abs.max()[0]
            vm_lv_pu_abs_mean = vm_lv_pu_raw_clear_abs.mean()[0]

            p_lv_mw_abs_max = p_lv_mw_raw_clear_abs.max()[0]
            p_lv_mw_abs_mean = p_lv_mw_raw_clear_abs.mean()[0]

            load_factor = p_to_mw_abs_mean / p_to_mw_abs_max
            voltage_factor = vm_pu_abs_mean / vm_pu_abs_max
            lv_load_factor = p_lv_mw_abs_mean / p_lv_mw_abs_max
            lv_voltage_factor = vm_lv_pu_abs_mean / vm_lv_pu_abs_max

            result = result.append({'installations_percent': i, 'cooperation_percent': c,
                                    'load_factor': load_factor, 'voltage_factor': voltage_factor,
                                    'lv_load_factor': lv_load_factor, 'lv_voltage_factor': lv_voltage_factor}, ignore_index=True)

    os.makedirs(
        full_dir_path, exist_ok=True)

    result.to_csv("{}/graph-data.csv".format(full_dir_path))

    return True


def main():
    # prepare data for the computation of individual optimizations
    individual_optimizations_args_list = []

    for scenario in scenarios:
        individual_optimizations_args_list.append((scenario, 1))

    # prepare data for the computation of collective optimizations
    cooperative_optimizations_args_list = []

    network_simulations_args_list = []

    for scenario in scenarios:
        for installations_percent in range(0, 101, DER_INSTALLATIONS_PERCENT_STEP):
            installation_buses = get_installation_buses_dataframe(
                installations_percent)

            for cooperation_percent in range(0, 101, DER_COOPERATION_PERCENT_STEP):
                [cooperating_buses, individual_buses] = get_cooperation_buses_dataframe(
                    installation_buses, cooperation_percent)

                if cooperating_buses.size > 0:
                    cooperative_optimizations_args_list.append(
                        (scenario, installations_percent, cooperation_percent, cooperating_buses))

                network_simulations_args_list.append((
                    scenario, installations_percent, cooperation_percent, installation_buses, cooperating_buses, individual_buses
                ))

    p = Pool()

    print("Optimizing/simulating the network using up to {} threads...".format(p._processes))

    # compute cooperative optimizations
    p.starmap(compute_cooperative_optimization,
              cooperative_optimizations_args_list)
    # compute individual optimizations
    p.starmap(compute_individual_optimization_fast,
              individual_optimizations_args_list)
    # simulate the networks
    p.starmap(simulate_network, network_simulations_args_list)
    p.starmap(compute_graph_data, individual_optimizations_args_list)
    p.close()


if __name__ == "__main__":
    main()
