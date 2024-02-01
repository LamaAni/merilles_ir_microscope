# %% Load config
from tabor_client import TaborClient
import time
import re

host = "134.74.27.64"
# host = "134.74.27.62"
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
    ":DIG:CHAN CH2",
    ":DIG: TRIG: SOUR CH2",
    ":DIG: CHAN: STAT ENAB",
    ":DIG: TRIG: TYPE EDGE",
    ":DIG: INIT OFF",
    ":DIG: PULS INT, FIX, 1e9",
    ":DIG: INIT ON",
    ":DIG:PULS: TRIG: IMM",
)

client.query(
    ":DIG:ACQ:STAT?",
    ":DIG:CHAN:STAT?",
    ":DIG:PULS:COUN?",
)


# %%
# Test counter

for i in range(20):
    rslt: str = client.query(":DIG: PULS: COUN?")
    if "," in rslt:
        counts = int(re.split(r"[\s,]+", rslt.strip()))
        print(counts)
    else:
        print("Error reading counts")
    time.sleep(20e-3)

# %% Marks command
# time.sleep(2e-3)
# print(client.query(":DIG: PULS: COUN?"))

# %% Disconnect
client.disconnect()

# %%
