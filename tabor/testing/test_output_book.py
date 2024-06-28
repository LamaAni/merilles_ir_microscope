# %% Define client
from typing import List
from tabor.tabor_client import TaborClient, TaborFunctionSegment
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import re

# host = "134.74.27.64"
host = "134.74.27.16"
port = "5025"

client = TaborClient(host, port).connect()

# %% Single value out
client.voltage_out(1, -3)

# %% Function generation

freq = 1e4
data = TaborFunctionSegment(0.001, lambda t: np.sin(t * np.pi * freq) * 5)

plt.plot(*data.to_plot_data())

# %% Send out
client.voltage_out(1, data)

# %% Counter
dt = 1
client.counter_prepare(dt, 1)

for i in range(int(20 / dt)):
    client.counter_trigger()
    time.sleep(dt)
    print(f"{i+1} : {client.counter_read()}")

# %% Marker
client.select_channel(1)
client.command(
    ":MARK:SEL 1",
)

# %% Marker on

client.command(":MARK ON")

# %% Marker off
client.command(":MARK OFF")

# %% Marker data upload


def marker_values_to_binary_data(vals: List[float]):
    def to_bit(v):
        return "0" if v <= 0 else "1"

    def to_bit_set(v):
        return f"11{to_bit(v)}1"

    idx = 0
    data = []
    while idx < len(vals):

        def next_part():
            nonlocal idx
            v = vals[idx] if idx < len(vals) else 0
            idx += 1
            return to_bit_set(v)

        num_as_bits = next_part()
        num_as_bits = next_part() + num_as_bits
        data.append(int(num_as_bits, base=2))

    return data


data = marker_values_to_binary_data([1] * int(1024 / 8) + [0] * int(1024 / 8))
client.command("*CLS")
client.write_binary(":MARK:DATA", data)

# %%
