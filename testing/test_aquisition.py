# %% Load config
from tabor_client import TaborClient
import time
import re

# host = "134.74.27.64"
host = "134.74.27.62"
port = "5025"
client = TaborClient(host, port, keep_command_and_query_record=True)

# %% Connect to tabor
client.connect()

# %% Setup digitizer

# client.command(
#     ":DIG:CHAN CH1",
#     ":DIG:INIT OFF",
#     ":DIG:TRIG:SOUR CH1",
#     ":DIG:CHAN:STAT ENAB",
#     ":DIG:TRIG:TYPE EDGE",
#     ":DIG:PULS INT,FIX,2e-8",
#     ":DIG:INIT ON",
# )

# %%

dt = 0.01
# Create counter
client.command(
    "*CLS",
    ":DIG:CHAN CH2",
    ":DIG:TRIG:SOUR CH2",
    ":DIG:CHAN:STAT ENAB",
    ":DIG:TRIG:TYPE EDGE",
    ":INIT:CONT ON",
    ":DIG:INIT OFF",
    f":DIG:PULS INT, FIX, {dt}",
    ":DIG:INIT ON",
)

# %%
# Test counter


def read_counts():
    client.command(":DIG:PULS:TRIG:IMM")
    time.sleep(dt)
    rslt = client.query(
        ":DIG: PULS:COUN?",
    )
    assert "," in rslt, Exception(f"Failed to read: {rslt}")
    rslt = rslt.strip()
    counts = [int(v) for v in re.split(r"[\s,]+", rslt)]
    return counts


while True:
    try:
        print(read_counts())

    except Exception as ex:
        print(f"Error reading counts, {ex}")


# %%
# Dynamic counting (failed)

dt = 1e-2

for i in range(100):
    try:
        counts_0 = read_counts()
        time.sleep(dt)
        counts_1 = read_counts()
        counts_per_sec = []
        for i in range(len(counts_0)):
            c0 = counts_0[i]
            c1 = counts_1[i]
            counts_per_sec.append((c1 - c0) * 1.0 / dt)

        print(f"{[str(v) for v in counts_per_sec]} [c/s] ({counts_0}, {counts_1})")
    except Exception:
        print(f"Read failed on iter {i}")


# %% Marks command
# time.sleep(2e-3)
# print(client.query(":DIG: PULS: COUN?"))

# %% Disconnect
client.disconnect()

# %%
