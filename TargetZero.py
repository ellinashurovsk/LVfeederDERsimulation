import pandas as pd
import pandapower as pp
import pandapower.timeseries.data_sources.frame_data as fd
from pandapower.control import ConstControl
from pandapower.networks import ieee_european_lv_asymmetric
from pandapower.timeseries.run_time_series import run_timeseries
from pandapower.timeseries import OutputWriter
import matplotlib.pyplot as plt
import pandapower.control.basic_controller as basic_controller
import numpy

# initialize a network

net = ieee_european_lv_asymmetric('on_peak_566')

# turn off asymmetric loads

for index, _ in net.asymmetric_load.iterrows():
    net.asymmetric_load.in_service.at[index] = False

# power flow run

pp.runpp(net)

# load consumer bus indices

consumer_bus_indices = pd.read_csv('buses.csv', sep=";")

# function of kW to MW convertation


def convertkWToMW(x):
    return x * 0.001

# initialize a subclass for storage controller


class ZeroTargetStorage(basic_controller.Controller):

    def __init__(self, net, load_index, storage_index, generator_index, time_step_length=600, in_service=True, recycle=False, order=0, level=0, initial_powerflow=True, **kwargs):
        super().__init__(net, in_service=in_service, recycle=recycle, order=order, level=level,
                         initial_powerflow=initial_powerflow, **kwargs)

        self.load_index = load_index
        self.storage_index = storage_index
        self.generator_index = generator_index
        self.time_step_length = time_step_length
        self.soc_percent = net.storage.at[storage_index, "soc_percent"]
        self.stored_energy_mwh = net.storage.at[storage_index,
                                                "max_e_mwh"] * net.storage.at[storage_index, "soc_percent"]/100
        self.applied = False
        self.p_mw = net.storage.at[storage_index, "p_mw"]
        self.last_time_step = None

    def get_stored_energy(self):
        return self.stored_energy_mwh

    # convergence check
    def is_converged(self):
        # check whether controller already was applied
        return self.applied

    def write_to_net(self):
        self.net.storage.at[self.storage_index, "p_mw"] = self.p_mw
        self.net.storage.at[self.storage_index,
                            "soc_percent"] = self.soc_percent

    def control_step(self):
        self.write_to_net()
        self.applied = True

    def time_step(self, time):
        # keep track of the soc
        if self.last_time_step is not None:
            dt = time-self.last_time_step
            self.stored_energy_mwh += self.p_mw * dt * self.time_step_length/3600
            self.stored_energy_mwh = numpy.clip(self.stored_energy_mwh, 0, self.net.storage.at[storage_index,
                                                                                               "max_e_mwh"])
            if self.stored_energy_mwh <= 0:
                net_p_mw = self.net.sgen.at[self.generator_index,
                                            "p_mw"]-self.net.load.at[self.load_index, "p_mw"]
                if net_p_mw <= 0:
                    self.p_mw = 0
                else:
                    self.p_mw = numpy.clip(
                        net_p_mw, 0, self.net.storage.at[self.storage_index, "max_p_mw"])
            elif self.stored_energy_mwh >= self.net.storage.at[self.storage_index, "max_e_mwh"]:
                net_p_mw = self.net.sgen.at[self.generator_index,
                                            "p_mw"]-self.net.load.at[self.load_index, "p_mw"]
                if net_p_mw >= 0:
                    self.p_mw = 0
                else:
                    self.p_mw = numpy.clip(
                        net_p_mw, self.net.storage.at[self.storage_index, "min_p_mw"], 0)
            else:
                net_p_mw = self.net.sgen.at[self.generator_index,
                                            "p_mw"]-self.net.load.at[self.load_index, "p_mw"]
                self.p_mw = numpy.clip(
                    net_p_mw, self.net.storage.at[self.storage_index, "min_p_mw"], self.net.storage.at[self.storage_index, "max_p_mw"])

            self.soc_percent = self.stored_energy_mwh / self.net.storage.at[
                self.storage_index, "max_e_mwh"] * 100

        self.last_time_step = time

        self.applied = False


for _, row in consumer_bus_indices.iterrows():
    # initialize loads

    load_index = pp.create_load(net, bus=row.bus, p_mw=0)

    load_profile_raw = pd.read_csv(
        "European_LV_Test_Feeder_v2/European_LV_CSV/Load Profiles/"+row.load_profile_filename, sep=",", decimal=".")

    load_profile_raw['mult'] = load_profile_raw['mult'].apply(
        convertkWToMW).iloc[::10].reset_index(drop=True)

    load_profile = fd.DFData(pd.DataFrame(load_profile_raw))

    load_controller = ConstControl(
        net, element='load', element_index=load_index, variable='p_mw', data_source=load_profile, profile_name='mult', recycle=False
    )

    # initialize PV generation

    sgen_index = pp.create_sgen(net, bus=row.bus, p_mw=0, sn_mva=0, type='PV')

    pv_profile_raw = pd.read_csv("PVProfile1440.csv", sep=";", decimal=".")

    pv_profile_raw['pv_output_power_kw'] = pv_profile_raw['pv_output_power_kw'].apply(
        convertkWToMW).iloc[::10].reset_index(drop=True)

    pv_profile = fd.DFData(pd.DataFrame(pv_profile_raw))

    sgen_controller = ConstControl(
        net, element='sgen', element_index=sgen_index, variable='p_mw',
        data_source=pv_profile, profile_name='pv_output_power_kw',
        recycle=False)

    # initialize storage elements

    storage_index = pp.create_storage(
        net, bus=row.bus, p_mw=0, max_e_mwh=0.0077, soc_percent=50, sn_mva=0.003, max_p_mw=0.003, min_p_mw=-0.003)

    storage_controller = ZeroTargetStorage(
        net, load_index=load_index, storage_index=storage_index, generator_index=sgen_index)


time_steps = range(0, 144)

ow = OutputWriter(net, output_path="./result",
                  output_file_type=".csv")

ow.log_variable("storage", "soc_percent", index=[0])
ow.log_variable("load", "p_mw", index=[0])
ow.log_variable("sgen", "p_mw", index=[0])
ow.log_variable("storage", "p_mw", index=[0])


run_timeseries(net, time_steps, continue_on_divergence=True)
