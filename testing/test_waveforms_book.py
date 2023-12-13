# %%
print("ok")

# %% Test matplotlib
from matplotlib import pyplot as plt

plt.figure(1)
plt.plot([1, 2, 3, 4], [1, 2, 3, 4])

# %%
from matplotlib import pyplot as plt
from tabor_client.data import TaborSignDataSegment, TaborDataSegment

segment = TaborSignDataSegment(freq=1e7)

plt.plot(*segment.to_plot_data())
segment = TaborDataSegment(values=[0.5])

plt.plot(*segment.to_plot_data())
