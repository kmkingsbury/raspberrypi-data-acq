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
import sys, argparse


class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)


GPIO.setmode(GPIO.BCM)

SPICLK = 18 #17
SPIMISO = 23 #24
SPIMOSI = 24 #25
SPICS = 25 #27

# Parse Args:
def mainargs(argv):
  parser = argparse.ArgumentParser(description='Collects Data on a Raspberry Pi 2 B+.',
  formatter_class=SmartFormatter
  )
  parser.add_argument('-s', '--sleep', type=float, nargs=1, required=False,
                   help='Time to sleep between measurements')
  parser.add_argument('-c', '--channels', type=int, nargs=1, required=False,
                 help='Number of channels to record')
  parser.add_argument('-o', '--outfile', nargs=1, required=False,
               help='CSV Outfile to use')
  parser.add_argument('-d', '--debug', action='store_true', required=False,
               help='Print Debug messages')
  parser.add_argument('-t', '--type', type=str, nargs='+', required=False, choices=['raw', 'ctemp', 'ftemp'],
               help="R|Datatypes to record space separate.\n"
         " raw = raw values (0 to 1024, default value)\n"
         " ctemp = Temperature (Celsius)\n"
         " ftemp = Temperature (Fahrenheit)")
  args = parser.parse_args()
  return args



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

# Parse Args, handle options
args = mainargs(sys.argv[1:])

# Sleep
sleeptime = 1;
if args.sleep: sleeptime = args.sleep[0]
if args.debug: print "Sleep time: " + str(sleeptime)

# Channels
channels = 4;
if args.channels: channels = int(args.channels[0])
if args.debug: print "Channels: " + str(channels)

# Outfile
outfile = 'test.csv'
if args.outfile: outfile = args.outfile[0]
if args.debug: print "Outfile: " + outfile

# This is all matching the datatypes and getting the correct array sizes
types = []
if args.type:
  types = args.type
else:
  types = ['raw'] * channels

datatype = ['raw'] * 8
if args.debug: print "Len:" + str(len(types))
if len(types) != channels:
  for val in range(0,channels):
    if args.debug: print "Vals: " + str(val)
    try:
      #print "DT (" + str(val) + "):" + str(datatype[val-1] )
      if args.debug: print "T (" + str(val) + "):" + str(types[val] )

      datatype[(val)] = types[val]
    except IndexError:
      datatype.append('raw')
elif len(types) > channels:
  datatype = types[:(channels)]
else:
  datatype = types[:(channels)]

# make final correct size
datatype = datatype[:(channels)]
if args.debug: print "Types: " + '[%s]' % ', '.join(map(str, types))
if args.debug: print "DataTypes: " + '[%s]' % ', '.join(map(str, datatype))



if __name__ == '__main__':

  runner = True

  # Logger open CSV
  fp = open(outfile, 'a')
  csv = csv.writer(fp, delimiter=',')

  # set up the SPI interface pins
  GPIO.setup(SPIMOSI, GPIO.OUT)
  GPIO.setup(SPIMISO, GPIO.IN)
  GPIO.setup(SPICLK, GPIO.OUT)
  GPIO.setup(SPICS, GPIO.OUT)

  try:
    while (runner == True):
      #It may take a second or two to get good data

      # Time:
      mynow = str(time.time())
      timenow = strftime("%Y-%m-%d %H:%M:%S", gmtime())
      dec = mynow.split(".")
      timenow += "."+dec[1]

      data = [ timenow,0,0,0,0,0,0,0,0 ]
      rawvalues = [0] * 8
      values = [0] * 8
      for val in range(0,channels):
       if args.debug: print "Val:" + str(val)
       rawvalues[val] = readadc(val, SPICLK, SPIMOSI, SPIMISO, SPICS)

       # Convert raw value to something else if specificed in type option.
       if datatype[(val)] == 'ftemp':
         values[val] = CtoF(ConvertTemp(ConvertmVolts(rawvalues[val])))
       elif datatype[(val)] == 'ctemp':
         values[val] = ConvertTemp(ConvertmVolts(rawvalues[val]))
       else:
         values[val] = rawvalues[val]
       data[(val+1)] = values[val]

      # Prepare and Print the raw values if debug flag set
      rawline = 'Raw '
      for val in range(0,channels):
        rawline += "V"+str(val+1)+":"+ str(rawvalues[val]) + " "
      if args.debug: print rawline
#      print "Vals: 1:"+ str(fahrenheittemp) + " 2:"+  str(value2) + " 3:" + str(value3)

      data = data[:channels+1]
      #Output converted values
      print "Data: ",
      print (data)

      #Record to CSV
      csv.writerow(data)

      #Sleep
      time.sleep(sleeptime)

  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."
    runner = False
  print "Almost done."
  fp.close()
  GPIO.cleanup()
  print "Done.\nExiting."
  exit();
