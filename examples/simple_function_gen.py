# Simple WX2184 Example using PyVISA

import teawg

# Connect to the instrument
print()
print("Please insert the instrument address")
print("(either IP-Address or NI-VISA Resource Name)")
print()
conn_str = raw_input("Enter the address: ")
print()
inst = teawg.TEWXAwg(conn_str, paranoia_level=1)


# Perform a reset
inst.send_cmd("*RST")
# Ask for identification details from instrument
print()
IDN = inst.send_query("*IDN?")
print()
print("Connected to: {0}".format(IDN))
print()
# Set instrument to standard mode
inst.send_cmd(":FUNC:MODE FIX")
# Set Channel1 as active
inst.send_cmd(":INST:SEL CH1")
# Set the frequency of the waveform
inst.send_cmd(":FREQ 50e6")
# Set the amplitude in Vp-p
inst.send_cmd(":VOLT 2")
# Set the waveform shape
inst.send_cmd(":FUNC:SHAP SQU")
# Turn the active channel's output
inst.send_cmd(":OUTP ON")
print()
syst_err = inst.send_query(":SYST:ERR?")
print()
print("End of the Example - Status: {0}".format(syst_err))
print()

# Close session
inst.close
