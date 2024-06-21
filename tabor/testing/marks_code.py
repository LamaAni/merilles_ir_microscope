# %% Me and Daniela added this part
import os


import sys


 


srcpath = os.path.realpath('SourceFiles')


sys.path.append(srcpath)


 


from tevisainst import TEVisaInst


 


import matplotlib.pyplot as plt


 


import numpy as np


 


#Set rates for DAC


sampleRateDAC = 1E9


 


#wavefore parameters


max_dac=(2**16)-1 # Max Dac


half_dac=max_dac/2 # DC Level


min_dac = 0


data_type = np.uint16 # DAC data type


maxVoltPeaktoPeak = 500E-3 # Fullscale


# %% set up instrument
inst_addr = 'TCPIP::127.0.0.1::5025::SOCKET' #Proteus Local
inst = TEVisaInst(inst_addr) # get instruent pointer
print(inst.send_scpi_query("*IDN?"))
# %% Setup digitizer 
':DIG:CHAN CH1')
':DIG: TRIG: SOUR CH1')
':DIG: CHAN: STAT ENAB' )
':DIG: TRIG: TYPE EDGE')
':DIG: INIT OFF')
':DIG: PULS INT, FIX, 1')
':DIG: INIT ON')
':DIG:PULS: TRIG: IMM')


# %% Get number of pulses


num_pulses = inst.send_scpi_query(':DIG: PULS: COUN?')
print (num_pulses)