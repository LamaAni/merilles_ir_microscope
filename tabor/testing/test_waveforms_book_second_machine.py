# %% Imports
import math
from tabor.tabor_client import TaborClient
from matplotlib import pyplot as plt
from tabor.tabor_client.data import (
    TaborFunctionGeneratorSegment,
    TaborDataSegment,
    TaborWaveform,
    TaborFunctionGeneratorSegmentFType,
)


# Create client
host = "134.74.27.56"
port = "5025"
client = TaborClient(host, port, keep_command_and_query_record=True)
print("Client created")
client.connect()
print("Client connected")
client.raw_query("*IDN?", "*OPC?")
client.__channel_select_command = "INST:SEL"


# %% Send sepcific commands
# client.raw_query("*RST", "*OPC?")
client.raw_query(
    # "*CLS",
    ":INST:SEL 1",
    # ":VOLT 0.2",
    ":VOLT:LEV 0.5",
    ":VOLT:OFFS 0.5",
    # "*OPC?",
    ":OUTP ON",
    ":SYST:ERR?",
)
# client.command(":INST:CHAN 1")

# %% Send sepcific commands
client.raw_query(
    # "*CLS",
    ":INST:SEL 1",
    # ":VOLT 0.2",
    # "*OPC?",
    ":OUTP OFF",
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
client.off(1)

# %% Turn on
client.on(1, 2)

# %% Set voltatge

# %% Test function
# client.command_record.clear()

client.off(1)
# client.voltage_out(1, 0)

output_func(
    1,
    freq=1e5,
    amplitude=0.3,
    # amplitude=0.1,
    offset=0.2,
    func=TaborFunctionGeneratorSegmentFType.square,
    as_dac_values=True,
)
print("\n".join(client.print_command_record()))

# %% Test channel output

# client.select_channel(2)
# print(client.query(":INST:CHAN:OFFS:DEF?"))
# client.command(
#     ":MODE DIR",
#     ":VOLT 0.1",
# )
# client.on(2)
