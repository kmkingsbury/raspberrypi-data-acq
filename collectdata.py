#! /usr/bin/python
# Based off the code written by Dan Mandle http://dan.mandle.me September 2012
# Modified by Kevin Kingsbury: https://github.com/kmkingsbury
# License: Apache 2.0
 
import os
from daemon import Daemon

import RPi.GPIO as GPIO

import time
from time import gmtime, strftime
import threading
#import yaml
import csv
#import rrdtool

#Sesnsor libraries


GPIO.setmode(GPIO.BCM) 
sensor = 11
DHpin = 7
SPICLK = 18 #17
SPIMISO = 23 #24
SPIMOSI = 24 #25
SPICS = 25 #27
humidity_adc = 0
mybutton = 40
mywindspeed = 38
myraingauge = 37
light_adc = 1
winddir_adc = 2

def CtoF(temp):
	temp = (temp * (9.0/5.0))+32.0
	return round(temp,2)

def ConvertTemp(data):
	temp = ((data - 100)/10.0) - 40.0
	temp = round(temp,4)
	return temp


def ConvertmVolts(data):
	volts = (data * 3300.0) / 1023.0
	volts = round(volts, 4)
	return volts


runner = True
rain_count = 0
windspeed_count = 0
# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)  # start clock low
        GPIO.output(cspin, False)     # bring CS low

        commandout = adcnum
        commandout |= 0x18  # start bit + single-ended bit
        commandout <<= 3    # we only need to send 5 bits here
        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin, True)
                else:
                        GPIO.output(mosipin, False)
                commandout <<= 1
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)

        adcout = 0
        # read in one empty bit, one null bit and 10 ADC bits
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout <<= 1
                if (GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin, True)
        
        adcout >>= 1       # first bit is 'null' so drop it
        return adcout




# RRD 
#from rrdtool import update as rrd_update
#ret = rrd_update('example.rrd', 'N:%s:%s' %(metric1, metric2));

# Main Loop
if __name__ == '__main__':


# Logger open CSV
  fp = open('test.csv', 'a')
  csv = csv.writer(fp, delimiter=',')

  # set up the SPI interface pins
  GPIO.setup(SPIMOSI, GPIO.OUT)
  GPIO.setup(SPIMISO, GPIO.IN)
  GPIO.setup(SPICLK, GPIO.OUT)
  GPIO.setup(SPICS, GPIO.OUT)


  
 
  try:
    while (runner == True):
      #It may take a second or two to get good data



      timenow = strftime("%Y-%m-%d %H:%M:%S", gmtime())



      value1 = CtoF(ConvertTemp(ConvertmVolts(readadc(humidity_adc, SPICLK, SPIMOSI, SPIMISO, SPICS))))
      value2 = CtoF(ConvertTemp(ConvertmVolts(readadc(1, SPICLK, SPIMOSI, SPIMISO, SPICS))))
      value3 = CtoF(ConvertTemp(ConvertmVolts(readadc(2, SPICLK, SPIMOSI, SPIMISO, SPICS))))
      #print value1, value2, value3

#      print "Vals: 1:"+ str(fahrenheittemp) + " 2:"+  str(value2) + " 3:" + str(value3)


      #Record to CSV
      data = [ timenow, value1, value2, value3 ]
      print "Data: ",
      print (data)
      csv.writerow(data)
         
      #Sleep
      time.sleep(.05) #set to whatever

  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."    
    runner = False
  print "Almost done."
  fp.close()
  GPIO.cleanup()
  print "Done.\nExiting."
  exit();

