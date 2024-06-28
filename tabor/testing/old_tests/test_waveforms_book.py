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
# host = "134.74.27.64"
host = "134.74.27.16"
port = "5025"
client = TaborClient(host, port, keep_command_and_query_record=True)
client.connect()
client.select_channel(1)
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
        offset=0,
        values=TaborFunctionGeneratorSegment(
            freq=freq,
            amplitude=amplitude,
            offset=offset,
            phase=math.pi * 0,
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
channel_num = 2

client.voltage_out(channel_num, 0.2, False)
# %% Test function

client.command_record.clear()

client.off(channel_num)
client.voltage_out(channel_num, 0.2)

output_func(
    channel_num,
    freq=2.5e5,
    amplitude=0.3,
    # amplitude=0.1,
    offset=0,
    func=TaborFunctionGeneratorSegmentFType.square,
    as_dac_values=True,
)
print("\n".join(client.print_command_record()))

# %% Test channel output

client.select_channel(2)
print(client.query(":INST:CHAN:OFFS:DEF?"))
# client.command(
#     ":MODE DIR",
#     ":VOLT 0.1",
# )
# client.on(2)
