
import numpy as np
#import math
#import csv
import sys
import os
import gc 


#srcpath = os.path.realpath('../')
#sys.path.append(srcpath)


from tevisainst import TEVisaInst


inst = None
admin = None
paranoia_level = 2
max_dac = 0

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
        

def sysReset():
    global inst
    print ('Reset instrument ..')
    # Reset the instrument
    inst.send_scpi_cmd( '*CLS; *RST', paranoia_level)
    inst.send_scpi_cmd( ':TRACe:DELete:ALL', paranoia_level)
    print('Done')	
            
        
def setFreq(FREQ):
   global inst
   cmd=":FREQ:RAST {}".format(FREQ)
   inst.send_scpi_cmd(cmd)
   resp = inst.send_scpi_query(":FREQ:RAST?")
   freq = float(resp)
   print ("DAC Generate Freq:{0}".format(freq))
        


def prepareWaveData(num_channels):
   global max_dac
   seglen = 2**12 #2 ** 20 # 1MB
   num_cycles = [2 ** n for n in range(num_channels)]

   waves = [ None for _ in range(num_channels)]
   
   if dac_mode != 16:
      num_channels = int(num_channels//2)
    
    
   for ii in range(num_channels):
      ncycles = num_cycles[ii]
      cyclelen = int(seglen / ncycles)
    
      x = np.linspace(start=0, stop=seglen, num=seglen, endpoint=False)
      y = np.fmod(x, cyclelen)
      y = (y <= cyclelen / 2) * max_dac
      y = np.round(y)
      y = np.clip(y, 0, max_dac)
    
      if dac_mode == 16:
          waves[ii] = y.astype(np.uint16)
      else:
          waves[ii] = y.astype(np.uint8)
      del x, y

   return waves

def downloadWaves(waves, num_channels):
    global inst
    for ii in range(num_channels):
      ichan = ii
      channb = ichan + 1
      segnum = ichan % 2 + 1
      wav = waves[ichan]
      print('Download wave to segment {0} of channel {1}'.format(segnum, channb))
    
      # Select channel
      cmd = ':INST:CHAN {0}'.format(channb)
      inst.send_scpi_cmd( cmd, paranoia_level)
      seglen = wav.shape[0]
      # Define segment
      cmd = ':TRAC:DEF {0}, {1}'.format(segnum, seglen)
      inst.send_scpi_cmd( cmd, paranoia_level)
      #Select the segment
      cmd = ':TRAC:SEL {0}'.format(segnum)
      inst.send_scpi_cmd( cmd, paranoia_level)
    
      # Increase the timeout before writing binary-data:
      inst.timeout = 30000
    
      # Send the binary-data:
      inst.write_binary_data(':TRAC:DATA', wav)
        
      resp = inst.send_scpi_query(':SYST:ERR?')
      resp = resp.rstrip()
    
      if not resp.startswith('0'):
          print('ERROR: "{0}" after writing binary values'.format(resp))
            
      # Increase the timeout before writing binary-data:
      inst.timeout = 10000
    
	   # Play the specified segment at the selected channel:
      cmd = ':SOUR:FUNC:MODE:SEGM {0}'.format(segnum)
      inst.send_scpi_cmd( cmd, paranoia_level)

      # Turn on the output of the selected channel:
      cmd = ':OUTP ON'
      inst.send_scpi_cmd( cmd, paranoia_level)
    


inst=connect("192.168.0.74")

if inst is not None:
    idn_str = inst.send_scpi_query("*IDN?")
    print('Connected to: ' + idn_str.strip())
    model = inst.send_scpi_query(":SYST:iNF:MODel?")
    print("Model: " + model)
	
    #sysReset()
	
    if 'P9082' in model:
      dac_mode = 8
      FREQ=9e9
      max_dac = 2**8-1
    else:
      dac_mode = 16
      FREQ=2.5e9
      max_dac = 2**16-1

    print("DAC waveform format: {0} bits-per-point".format(dac_mode))
    
    setFreq(FREQ)
	
	
    waves = prepareWaveData(num_channels=4)
    downloadWaves(waves, num_channels=4)
	
	
	
