# %% Load config
from tabor_client import TaborClient
import time
import re
import math
from tabor_client.data import (
    TaborFunctionGeneratorSegment,
    TaborDataSegment,
    TaborWaveform,
    TaborFunctionGeneratorSegmentFType,
)
from matplotlib import pyplot as plt

# %% Connect to tabor

# host = "134.74.27.64"
host = "134.74.27.16"
port = "5025"
client = TaborClient(host, port, keep_command_and_query_record=True)


client.connect()
client.select_channel(1)
print("\n".join(client.print_command_record()))

# %% Do voltage
# client.set_offset(0.5, 1)
client.command_record.clear()
do_plot(client.voltage_out(1, 0, False, offset=0.25))
client.on(1)
print("\n".join(client.print_command_record()))

# %% RAW COMMANDS
client.raw_query(
    "*CLS",
    ":INST:CHAN:SEL 2",
    ":VOLT 0.5",
    # ":VOLT:LEV 0.2",
    ":VOLT:OFFS 0",
    # "*OPC?",
    ":OUTP ON",
    ":SYST:ERR?",
)

# %% Create functions


def do_plot(
    segment: TaborDataSegment | TaborWaveform,
    as_dac_values: bool = False,
):
    if isinstance(segment, TaborWaveform):
        segment = segment.data_segment

    x, y = segment.to_plot_data(as_dac_values=as_dac_values)
    plt.plot(x, y)


def output_dc(
    channel,
    value=1,
    plt=True,
    as_dac_values: bool = False,
):
    wav = TaborWaveform(
        channel=channel,
        values=[value],
    )
    if plt:
        do_plot(
            wav,
            as_dac_values=as_dac_values,
        )
    client.waveform_out(wav)


def output_func(
    channel,
    freq=1e7,
    amplitude=0.5,
    offset=0,
    func=TaborFunctionGeneratorSegmentFType.sin,
    plt=True,
    as_dac_values: bool = False,
):
    wav = TaborWaveform(
        channel=channel,
        values=TaborFunctionGeneratorSegment(
            freq=freq,
            amplitude=amplitude,
            offset=offset,
            phase=math.pi * 1,
            function=func,
        ),
    )
    if plt:
        do_plot(
            wav,
            as_dac_values=as_dac_values,
        )
    client.waveform_out(wav)


# %% Reset
client.reset()

# %%  Turn off
client.off(1, 2)

# %% Turn on
client.on(1, 2)

# %% Set voltatge

# %% Test function
client.command_record.clear()

client.off(1)
client.voltage_out(1, 0)

output_func(
    1,
    freq=1e3,
    amplitude=0.5,
    # amplitude=0.1,
    offset=0.5,
    func=TaborFunctionGeneratorSegmentFType.square,
    as_dac_values=True,
)
print("\n".join(client.print_command_record()))

# %% Turn off
client.off(1)


# %% Test channel output

client.select_channel(2)
print(client.query(":INST:CHAN:OFFS:DEF?"))
# client.command(
#     ":MODE DIR",
#     ":VOLT 0.1",
# )
# client.on(2)
