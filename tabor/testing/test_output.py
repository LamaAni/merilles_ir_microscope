# %% Load config
from tabor.tabor_client import TaborClient
from tabor.tabor_client.data import TaborWaveform, TaborFunctionGeneratorSegment
import matplotlib.pyplot as plt
import numpy as np
import time
import re

# host = "134.74.27.64"
host = "134.74.27.16"
port = "5025"


# %% Connect to tabor
client = TaborClient(host, port, keep_command_and_query_record=True).connect()

# %%

dt = 0.2
channel_number = 2
channel = f"CH{channel_number}"
max_voltage = 0.5
# Create counter
client.command(
    "*CLS",
    f":INST:CHAN:SEL {channel_number}",
    f":VOLT {max_voltage}",
    # ":VOLT:LEV 0.2",
    ":VOLT:OFFS 0",
    "*OPC?",
    ":OUTP ON",
    # ":SYST:ERR?",
)


# %% Test output waveform.

import pandas as pd
import numpy as np

wav = TaborWaveform(channel_number, [0.3])
plt.plot(*wav.to_plot_data())
client.waveform_out(wav)

# %%
