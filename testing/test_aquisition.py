# %% Load config
from tabor_client import TaborClient

host = "134.74.27.64"
host = "134.74.27.62"
port = "5025"
client = TaborClient(host, port, keep_command_and_query_record=True)

# %% Connect to tabor
client.connect()

# %% Setup digitizer

client.command(
    ":DIG:CHAN CH2",
    ":DIG:INIT OFF",
    ":DIG:TRIG:SOUR CH2",
    ":DIG:CHAN:STAT ENAB",
    ":DIG:TRIG:TYPE EDGE",
    ":DIG:PULS INT,FIX,2e-8",
    ":DIG:INIT ON",
)
# %% Query
client.query(
    ":DIG:ACQ:STAT?",
    ":DIG:CHAN:STAT?",
    ":DIG:PULS:COUN?",
)

# %% Disconnect
client.disconnect()
