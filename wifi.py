import ConfigParser
import os
import time

from time import gmtime, strftime
from subprocess import *
import RPi.GPIO as GPIO

from ssc_lcd import *

configfile = 'config.ini'

config = ConfigParser.ConfigParser()
config.read(configfile)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(config.getint('lcd', 'LCD_RS'), GPIO.OUT)
GPIO.setup(config.getint('lcd', 'LCD_E'), GPIO.OUT)
GPIO.setup(config.getint('lcd', 'LCD_D4'), GPIO.OUT)
GPIO.setup(config.getint('lcd', 'LCD_D5'), GPIO.OUT)
GPIO.setup(config.getint('lcd', 'LCD_D6'), GPIO.OUT)
GPIO.setup(config.getint('lcd', 'LCD_D7'), GPIO.OUT)


def run_cmd(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    output = p.communicate()[0]
    return output

try:
    while (1 == 1):
      lcd_string(config,strftime("%Y-%m-%d %H:%M", gmtime()),0x80)
      cmd = "ip addr show wlan0 | grep inet | awk '{print $2}' | cut -d/ -f1 | head -n 1"
      ipaddr = run_cmd(cmd).strip()
      lcd_string(config,ipaddr,0xC0)
      time.sleep(2)

except (KeyboardInterrupt, SystemExit): #when you press ctrl+c
  print "\nKilling Thread..."
  lcd_byte(config,0x01, config.getboolean('lcd', 'LCD_CMD'))
  lcd_string(config,"Goodbye",0x80)
  lcd_string(config,ipaddr,0xC0)
  GPIO.cleanup()
  exit();
