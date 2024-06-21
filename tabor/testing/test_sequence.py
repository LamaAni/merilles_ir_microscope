# %% Define sequence

from experiment_control.sequence import Sequence
from experiment_control.devices.NITaskDevice import NITaskDevice

seq = Sequence(freqeuency=1e3)
seq.add_device("dev1", NITaskDevice())
seq.add_channel(name="X", device_name="dev1", physical_address="/dev1/ao0")
seq.add_channel(name="Y", device_name="dev1", physical_address="/dev1/ao1")


# %% Write data out
seq.write("X", [0, 1, 3, 3, 4])
seq.write("Y", [0, 1, 1, 3, 4])

# %% Write data out
seq.plot()

# %%
