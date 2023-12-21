# %%
from tabor_client import TaborClient
from matplotlib import pyplot as plt

# %% Create client
host = "134.74.27.64"
port = "5025"
client = TaborClient(host, port, keep_command_and_query_record=True)
client.connect()

# %%  Turn off

client.off(1, 2)

# %% Test matplotlib


plt.figure(1)
plt.plot([1, 2, 3, 4], [1, 2, 3, 4])

# %%
from matplotlib import pyplot as plt
from tabor_client.data import TaborSignDataSegment, TaborDataSegment, TaborWaveform


def do_plot(segment: TaborDataSegment | TaborWaveform):
    if isinstance(segment, TaborWaveform):
        segment = segment.data_segment

    plt.plot(*segment.to_plot_data())


do_plot(TaborSignDataSegment(freq=1e7))
do_plot(TaborWaveform(channel=2, values=[0.1 for _ in range(32)] + [0.5]))

do_plot(
    TaborDataSegment(
        values=[v for v in [0, 1, 0, 1, 0.5, 0.3, 0] for _ in range(100)],
    )
)
