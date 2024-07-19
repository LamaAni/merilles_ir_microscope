# %% Define client
from typing import List, Union
from tabor.tabor_client import TaborClient, TaborFunctionSegment
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import re

# host = "134.74.27.64"
host = "134.74.27.16"
port = "5025"

# %% Connect

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

# %% Marker data config


def marker_values_to_binary_data(
    vals: List[Union[float, int, bool]],
    channel: int = 1,
    use_8_bits: bool = True,
):
    assert channel > 0 and channel < 5, ValueError(
        f"Channel {channel} out of range, 1-4"
    )

    def to_channel_bits(val):
        # Use bit shift to move the bits to the correct
        # value.
        # If was channel = 2, then starting with 1, e.g
        # 1<<1 = 0001 --> 0010
        # 1<<2 = 0001 --> 0100 .. etc
        return 1 << channel - 1 if val > 0 else 0

    idx = 0
    data = []
    while idx < len(vals):
        num = to_channel_bits(vals[idx])
        idx += 1
        if use_8_bits:
            if idx >= len(vals):
                # Not enough to compose the next
                # 8 bit.
                # Skip (should error)
                break
            # Shift by 4
            # 0010 --> 00100000
            
            # Do a or operation, join two, e.g.
            # 0100 |
            # 0001 =
            # 0101
            num = to_channel_bits(vals[idx]) << 4 | num
            idx += 1

        data.append(num)

    # This is an 8 bit operation in the case where.
    # we have the 8 bits for the values.
    return bytes(data)


# Should print all channel 1 options. Notice that
# the number of bytes is always 1, which
# means we are generating the proper data.
# e.g. 00010001 -> means two 1 values in channel 1.
for d in [
    marker_values_to_binary_data([1, 1]),
    marker_values_to_binary_data([0, 0]),
    marker_values_to_binary_data([1, 0]),
    marker_values_to_binary_data([0, 1]),
]:
    # Note that the binary data is capped at the 5th bit
    # this is the way bin function works.
    print(bin(d[0]), f"Number of bytes: {len(d)}")


# %% Upload marker data.
data = marker_values_to_binary_data(
    [1] * int(1024 / 8) + [0] * int(1024 / 8),
)
client.command("*CLS")
# Choose the write method for bytes
client.write_binary(":MARK:DATA", data, "b")

# %%
