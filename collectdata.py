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
import ConfigParser
import re


class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)


GPIO.setmode(GPIO.BCM)


# Parse Args:
def mainargs(argv):
  parser = argparse.ArgumentParser(description='Collects Data on a Raspberry Pi 2 B+.',
  formatter_class=SmartFormatter, epilog="Example 3 channel of raw and 2 Celsius temperature:\n sudo python ./collectdata.py -c 3 -t raw ctemp ctemp"
  )
  parser.add_argument('-s', '--sleep', type=float, nargs=1, required=False,
                   help='Time (seconds) to sleep between measurements')
  parser.add_argument('-n', '--channels', type=int, nargs=1, required=False,
                 help='Number of channels to record')
  parser.add_argument('-o', '--outfile', nargs=1, required=False,
               help='Outfile to use')
  parser.add_argument('-c', '--config', nargs=1, required=False,
                            help='Config File to use')
  parser.add_argument('-g', '--gnuplot', action='store_true', required=False,
               help='Print the outputfile in gnuplot format (tabs) instead of CSV')
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

rawargs = ' '.join (sys.argv)
#print "Raw: "+ rawargs

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
if args.gnuplot: outfile = "test.dat"
if args.outfile: outfile = args.outfile[0]
if args.debug: print "Outfile: " + outfile
filewoext = re.split('(.*)\.\w', outfile)
#print filewoext[1]
metafile = filewoext[1] +".md"
if args.debug: print "Metafile: "+ metafile

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

# Config File
configfile = 'config.ini'
if args.config: config = args.config[0]
if args.debug: print "Config file: " + str(configfile)


config = ConfigParser.ConfigParser()
config.read(configfile)




if __name__ == '__main__':

  runner = True

  print 'sys:'+ str(sys.argv[0]) + ' ' + str(args)

  # Logger open CSV
  fp = open(outfile, 'w')
  fp.write('# Input parameters: '+ str(sys.argv[0]) + ' ' + str(args) + '\n')
  fp.write('# Datetime\t\t')
  for x in range(1, channels):
      fp.write("\t Ch"+str(x))
  fp.write("\n")

  cvs = None
  if args.gnuplot == False:
    writer = csv.DictWriter(fp, fieldnames = ['datetime']+ datatype, delimiter=',')
    writer.writeheader()
    csv = csv.writer(fp, delimiter=',', quoting=csv.QUOTE_ALL)
  else:
    csv = csv.writer(fp, delimiter="\t", quoting=csv.QUOTE_NONNUMERIC, quotechar='\'')

  # set up the SPI interface pins
  GPIO.setup(config.get('AD MCP3008', 'SPIMOSI', 0), GPIO.OUT)
  GPIO.setup(config.get('AD MCP3008', 'SPIMISO', 0), GPIO.IN)
  GPIO.setup(config.get('AD MCP3008', 'SPICLK', 0), GPIO.OUT)
  GPIO.setup(config.get('AD MCP3008', 'SPICS', 0), GPIO.OUT)

  try:
    while (runner == True):
      #It may take a second or two to get good data

      # Time:
      mynow = str(time.time())
      timenow = strftime("%Y-%m-%d %H:%M:%S", gmtime())
      dec = mynow.split(".")

      #this is a dumb way to get zero padded decimal seconds
      timenow += "."+format(float("."+dec[1]), '.2f').split('.')[1]
      data = [ timenow,0,0,0,0,0,0,0,0 ]
      rawvalues = [0] * 8
      values = [0] * 8
      for val in range(0,channels):
       if args.debug: print "Val:" + str(val)
       rawvalues[val] = readadc(val, config.get('AD MCP3008', 'SPICLK', 0), config.get('AD MCP3008', 'SPMOSI', 0), config.get('AD MCP3008', 'SPIMISO', 0), config.get('AD MCP3008', 'SPICS', 0))

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

      #Record to File
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
