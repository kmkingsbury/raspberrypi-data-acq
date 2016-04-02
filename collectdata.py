#! /usr/bin/python
# Based off the daemon code written by Dan Mandle http://dan.mandle.me September 2012
# LCD parts from 16x2 LCD Test Script
# which is written by : Matt Hawkins 06/04/2015 (http://www.raspberrypi-spy.co.uk/)
#
# The Rest by Kevin Kingsbury: https://github.com/kmkingsbury
# License: Apache 2.0

import os
from daemon import Daemon
from subprocess import *
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

from ssc_lcd import *

version = 0.1

class SmartFormatter(argparse.HelpFormatter):

    def _split_lines(self, text, width):
        # this is the RawTextHelpFormatter._split_lines
        if text.startswith('R|'):
            return text[2:].splitlines()
        return argparse.HelpFormatter._split_lines(self, text, width)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)


# Parse Args:
def mainargs(argv):
  parser = argparse.ArgumentParser(description='Collects Data on a Raspberry Pi 2 B+.',
  formatter_class=SmartFormatter, epilog="Example 3 channel of raw and 2 Celsius temperature:\n sudo python ./collectdata.py -n 3 -t raw ctemp ctemp"
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

def run_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

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

def buttonEventHandler (pin):
    global config, fpmeta, displaymode, MKbuttonevents, data
    print "handling button event: "+str(pin)

    # Match Buttons, Log event:
    for (each_key, each_val) in config.items('buttons'):
      if pin == int(each_val):
        #print "here.\n"
        timenow = highrestime()
        fpmeta.write(""+each_key + ' Event: '+ timenow + ', '.join(map(str, data)) + '\n')
        MKbuttonevents += 1
        return

    # Match Menu
    if pin == config.getint('menu', 'up'):
      displaymode = 'Max'
      return
    elif pin == config.getint('menu', 'down'):
      displaymode = 'Min'
      return
    elif pin == config.getint('menu', 'right'):
      displaymode = 'Avg'
      return
    elif pin == config.getint('menu', 'left'):
      displaymode = 'Dev'
      return
    elif pin == config.getint('menu', 'select'):
      displaymode = 'Reg'
      return


def highrestime():
    global time
    mynow = str(time.time())
    timenow = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    dec = mynow.split(".")
    #this is a dumb way to get zero padded decimal seconds
    timenow += "."+format(float("."+dec[1]), '.2f').split('.')[1]
    return timenow

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

# Config File
configfile = 'config.ini'
if args.config: config = args.config[0]
if args.debug: print "Config file: " + str(configfile)

config = ConfigParser.ConfigParser()
config.read(configfile)

# Sleep
sleeptime = 1;
if args.sleep: sleeptime = args.sleep[0]
if args.debug: print "Sleep time: " + str(sleeptime)

# Channels
channels = 4;
if args.channels: channels = int(args.channels[0])
if args.debug: print "Channels: " + str(channels)

# Outfile
outfile = config.get('general', 'filesavedir', 0) + "data-"+strftime("%Y-%m-%d_%H%M%S", gmtime())+".csv"
if args.gnuplot: outfile = "data-"+strftime("%Y-%m-%d_%H%M%S", gmtime())+".dat"
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


# put in top level scope, reset in the loop

if __name__ == '__main__':

  runner = True

  print 'sys:'+ str(sys.argv[0]) + ' ' + str(args)

  # Logger open CSV
  fp = open(outfile, 'w')
  fpmeta = open(metafile, 'w')
  fpmeta.write('Raw parameters: '+rawargs+ '\n')
  fpmeta.write('Namespace parameters: '+ str(sys.argv[0]) + ' ' + str(args) + '\n')
  fpmeta.write('Config file: ' + str(configfile) + '\n')
  fpmeta.write('Channels: ' + str(channels)+ '\n')
  fpmeta.write('Sleeptime: ' + str(sleeptime)+ '\n')
  fpmeta.write("Types: " + '[%s]' % ', '.join(map(str, types))+ '\n')
  fpmeta.write("DataTypes: " + '[%s]' % ', '.join(map(str, datatype))+ '\n')

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
  GPIO.setup(config.getint('AD MCP3008', 'SPIMOSI'), GPIO.OUT)
  GPIO.setup(config.getint('AD MCP3008', 'SPIMISO'), GPIO.IN)
  GPIO.setup(config.getint('AD MCP3008', 'SPICLK'), GPIO.OUT)
  GPIO.setup(config.getint('AD MCP3008', 'SPICS'), GPIO.OUT)

  GPIO.setup(config.getint('lcd', 'LCD_RS'), GPIO.OUT)
  GPIO.setup(config.getint('lcd', 'LCD_E'), GPIO.OUT)
  GPIO.setup(config.getint('lcd', 'LCD_D4'), GPIO.OUT)
  GPIO.setup(config.getint('lcd', 'LCD_D5'), GPIO.OUT)
  GPIO.setup(config.getint('lcd', 'LCD_D6'), GPIO.OUT)
  GPIO.setup(config.getint('lcd', 'LCD_D7'), GPIO.OUT)


  lcd_init(config)
  lcd_string(config,"Scrapy Science",0x80)
  lcd_string(config,"Caddy v"+str(version),0xC0)
  time.sleep(2)
  lcd_string(config,strftime("%Y-%m-%d %H:%M", gmtime()),0x80)
  cmd = "ip addr show wlan0 | grep inet | awk '{print $2}' | cut -d/ -f1 | head -n 1"
  ipaddr = run_cmd(cmd).strip()
  lcd_string(config,ipaddr,0xC0)
  time.sleep(2)

  # Button Setups:
  for (each_key, each_val) in config.items('menu'):
    GPIO.setup(int(each_val), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(int(each_val),GPIO.FALLING, callback=buttonEventHandler, bouncetime=300)

  for (each_key, each_val) in config.items('buttons'):
    GPIO.setup(int(each_val), GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(int(each_val), GPIO.FALLING, callback=buttonEventHandler, bouncetime=300)

  # Reset count
  samplecount = 0
  MKbuttonevents = 0
  lastgmt = 0
  displaymode = 'Reg'
  sums = [0,0,0,0];
  mins = [None, None, None, None]
  maxs = [None, None, None, None]
  avgs = [0,0,0,0];
  try:
    while (runner == True):
      #It may take a second or two to get good data

      timenow = highrestime()
      data = [ timenow,0,0,0,0,0,0,0,0 ]
      rawvalues = [0] * 8
      values = [0] * 8
      for val in range(0,channels):
       if args.debug: print "Val:" + str(val)
       rawvalues[val] = readadc(val,
        config.getint('AD MCP3008', 'SPICLK'),
        config.getint('AD MCP3008', 'SPIMOSI'),
        config.getint('AD MCP3008', 'SPIMISO'),
        config.getint('AD MCP3008', 'SPICS'))

       # Convert raw value to something else if specificed in type option.
       if datatype[(val)] == 'ftemp':
         values[val] = CtoF(ConvertTemp(ConvertmVolts(rawvalues[val])))
       elif datatype[(val)] == 'ctemp':
         values[val] = ConvertTemp(ConvertmVolts(rawvalues[val]))
       else:
         values[val] = rawvalues[val]
       data[(val+1)] = values[val]
       sums[val] += values[val]
       if mins[val] == None : mins[val] = values[val]
       if maxs[val] == None : maxs[val] = values[val]
       if values[val] < mins[val]: mins[val] = values[val]
       if values[val] > maxs[val]: maxs[val] = values[val]
       avgs[val] = sums[val]/(samplecount+1)
      # Prepare and Print the raw values if debug flag set
      rawline = 'Raw '
      for val in range(0,channels):
        rawline += "V"+str(val+1)+":"+ str(rawvalues[val]) + " "
      if args.debug: print rawline
#      print "Vals: 1:"+ str(fahrenheittemp) + " 2:"+  str(value2) + " 3:" + str(value3)

      #trims array to correct size
      data = data[:channels+1]
      mins = mins[:channels]
      maxs = maxs[:channels]
      avgs = avgs[:channels]
      #Output converted values
      print "Data: ",
      print (data)
      samplecount += 1
      #Record to File
      csv.writerow(data)

      # Only update once per second
      if gmtime() != lastgmt:
        lcd_string(config,displaymode + " s:"+str(samplecount)+" "+"b:"+str(MKbuttonevents) ,0x80)
        ds = ''
        for i in range(0, channels):
            if displaymode == 'Reg':
              ds += '{:>4}'.format(data[i+1])
            elif displaymode == 'Max':
              ds += '{:>4}'.format(maxs[i])
            elif displaymode == 'Min':
              ds += '{:>4}'.format(mins[i])
            elif displaymode == 'Avg':
              ds += '{:>4d}'.format(sums[i]/samplecount)
            elif displaymode == 'Dev':
              ds += '{:>4d}'.format(abs((avgs)-data[i+1]))

        lcd_string(config,ds,0xC0)
        lastgmt = gmtime()

      #Sleep
      time.sleep(sleeptime)

  except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
    print "\nKilling Thread..."
    runner = False
    lcd_byte(config,0x01, config.getboolean('lcd', 'LCD_CMD'))
    lcd_string(config,"Goodbye",0x80)
    lcd_string(config,ipaddr,0xC0)
    #lcd_string(config,"Goodbye!",0xC0)
  print "Almost done."
  fpmeta.write('Samples: ' + str(samplecount)+ '\n')
  fpmeta.write('ButtonEvents: ' + str(MKbuttonevents)+ '\n')
  fpmeta.write("Avg: " + '[%s]' % ', '.join(map(str, avgs))+ '\n')
  fpmeta.write("Maxs: " + '[%s]' % ', '.join(map(str, maxs))+ '\n')
  fpmeta.write("Mins: " + '[%s]' % ', '.join(map(str, mins))+ '\n')

  fp.close()
  fpmeta.close()
  GPIO.cleanup()
  print "Done.\nExiting."
  exit();
