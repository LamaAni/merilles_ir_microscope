import numpy as np

# import math
# import csv
import sys
import os
import gc


# srcpath = os.path.realpath('../')
# sys.path.append(srcpath)

# from teproteus import TEProteusAdmin, TEProteusInst

from tevisainst import TEVisaInst


inst = None
admin = None


def disconnect():
    global inst
    global admin
    if inst is not None:
        try:
            inst.close_instrument()
        except:
            pass
        inst = None
    if admin is not None:
        try:
            admin.close_inst_admin()
        except:
            pass
        admin = None
    gc.collect()


def connect(ip_address):
    global inst
    try:
        disconnect()
        print("Trying to connect to IP:" + ip_address)
        inst = TEVisaInst(address=ip_address, port=5025, use_ni_visa=False)
        print(inst)
    except:
        print("Exception:")
        pass
    else:
        return inst


inst = connect("192.168.0.74")

if inst is not None:
    idn_str = inst.send_scpi_query("*IDN?")
    print("Connected to: " + idn_str.strip())
