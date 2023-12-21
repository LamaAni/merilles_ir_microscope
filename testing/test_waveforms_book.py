# %% Imports
import math
from tabor_client import TaborClient
from matplotlib import pyplot as plt
from tabor_client.data import (
    TaborFunctionGeneratorSegment,
    TaborDataSegment,
    TaborWaveform,
    TaborFunctionGeneratorSegmentFType,
)


# Create client

host = "134.74.27.64"
port = "5025"
client = TaborClient(host, port, keep_command_and_query_record=True)
client.connect()

# %% Create functions


def do_plot(segment: TaborDataSegment | TaborWaveform, as_dac_values: bool = False):
    if isinstance(segment, TaborWaveform):
        segment = segment.data_segment

    x, y = segment.to_plot_data(as_dac_values=as_dac_values)
    plt.plot(x, y)


def output_dc(channel, value=1, plt=True):
    wav = TaborWaveform(
        channel=channel,
        values=[value],
    )
    if plt:
        do_plot(wav)
    client.waveform_out(wav)


def output_func(
    channel,
    freq=1e7,
    amplitude=0.5,
    offset=0,
    plt=True,
    func=TaborFunctionGeneratorSegmentFType.sin,
):
    wav = TaborWaveform(
        channel=channel,
        amplitude=amplitude,
        offset=offset,
        values=TaborFunctionGeneratorSegment(
            freq=freq,
            phase=math.pi * 1,
            function=func,
        ),
    )
    if plt:
        do_plot(wav)
    client.waveform_out(wav)


# %% Reset
client.reset()

# %%  Turn off
client.off(1, 2)

# %% Turn on
client.on(1, 2)

# %% Set voltatge

# %% Test function

output_func(
    1,
    func=TaborFunctionGeneratorSegmentFType.square,
    amplitude=0.05,
    offset=0.2,
)

# # %% Test voltage out
# client.select_channel(1)
# client.command(
#     ":OUTP OFF",
#     ":VOLT 0.5",
#     ":VOLT:OFFS 0",
#     ":OUTP ON",
# )

# # %% Test matplotlib
# dc_wav = TaborWaveform(channel=1, values=[1])
# # do_plot(dc_wav, as_dac_values=True)

# client.waveform_out(dc_wav)
# # %%


# do_plot(TaborFunctionGeneratorSegment(freq=1e7))


# do_plot(
#     TaborDataSegment(
#         values=[v for v in [0, 1, 0, 1, 0.5, 0.3, 0] for _ in range(100)],
#     )
# )

# %%
