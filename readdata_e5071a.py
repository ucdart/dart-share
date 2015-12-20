import visa

import numpy as np

import matplotlib.pyplot as plt

import time

#measurement parameters. Change PortN to the desired port number. Usually this should be 2 for a 2-port device
PortN = 2

rm = visa.ResourceManager()

# use rm.list_resources() to find a list of available instrument and their corresponding resource names
inst_e5071a = rm.open_resource('GPIB::16::INSTR')

#assume that calibration is done locally on the instrument
#assume that frequency range, number of points, source power, etc are all set correctly at the instrument

#get number of points
NoP = int(inst_e5071a.query('SENS:SWE:POIN?'))

#freq = np.zeros([1,NoP])
sp = np.zeros([PortN*PortN*2, NoP])

#read frequency
str_freq = inst_e5071a.query(':SENS1:FREQ:DATA?')   #you always get a string from VISA commands
freq = [float(x) for x in str_freq.split(',')]      #values are comma separated

          
#set active trace
inst_e5071a.write(':CALC1:PAR1:SEL')

#set the format of the data on the active trace to Smith chart log magnitude so that we can read both the magnitude and the phase 
#refer to page 232 of the E5071A's programming guide
inst_e5071a.write(':CALC1:FORM SLOG')

#read calibrated s parameters

for i in range(PortN):
    for j in range(PortN):
        #set the data to be retrieved
        inst_e5071a.write(':CALC1:PAR1:DEF S'+str(i+1)+str(j+1))
        
        #delay some time so that the command could be executed in full
        #this delay should allow data to be copied to the output registers. So the delay is dependent on the number of points
        #by trial and error, delay of 0.2*NoP/201 is good enough
        #this delay essentially sets the data transfer speed
        #speed may be improved if data is read in binary format; default is ASCII
        time.sleep(0.2*NoP/201)
        
        #read data 
        str_s = inst_e5071a.query('CALC1:DATA:FDAT?')
        float_s = [float(x) for x in str_s.split(',')]

        #index is 2*((i-1)*PortN+(j-1)) for mag and 2*((i-1)*PortN+(j-1))+1 for phase
        sp[2*(i*PortN+j),:] = np.array([float_s[2*x] for x in range(NoP)])
        sp[2*(i*PortN+j)+1,:] = [float_s[2*x+1] for x in range(NoP)]

#generate a plot of S11 and S21 to verify that data collection is successful
plt.plot(freq,sp[0,:],'r')  #s11 magnitude
plt.plot(freq,sp[2,:],'g')  #s12 magnitude

#export the data
data=np.concatenate((np.array(freq).reshape(1,NoP),sp),axis=0)

np.savetxt('data_save.s'+str(PortN)+'p',data.reshape(NoP, PortN*PortN+1),fmt='%10.5f',delimiter='\t', header='GHZ S DB R 50')
