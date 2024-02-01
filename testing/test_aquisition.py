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
# Create counter
client.command(
    "*CLS",
    ":DIG:CHAN CH2",
    ":DIG:TRIG:SOUR CH2",
    ":DIG:CHAN:STAT ENAB",
    ":DIG:TRIG:TYPE EDGE",
    ":DIG:INIT OFF",
    ":DIG:PULS INT, FIX, 1e-1",
    ":DIG:INIT ON",
)

# %%
# Test counter

dt = 1e-2
client.command(
    ":DIG:PULS: TRIG: IMM",
)


def read_counts():
    rslt: str = client.query(":DIG: PULS: COUN?")
    assert "," in rslt, Exception("Failed to read")
    rslt = rslt.strip()
    counts = [int(v) for v in re.split(r"[\s,]+", rslt)]
    return counts


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

        print(f"{' ,'.join(str(counts_per_sec))} [c/s]")
    except Exception:
        print(f"Read failed on iter {i}")


# %% Marks command
# time.sleep(2e-3)
# print(client.query(":DIG: PULS: COUN?"))

# %% Disconnect
client.disconnect()

# %%
