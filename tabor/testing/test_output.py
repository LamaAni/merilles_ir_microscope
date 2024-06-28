from tabor.tabor_client import TaborClient
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import re

# host = "134.74.27.64"
host = "134.74.27.16"
port = "5025"
client = TaborClient(host, port).connect()
client.voltage_out(1, -3)
