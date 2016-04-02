import RPi.GPIO as GPIO
import time

def lcd_init(config):

   # Initialise display
   lcd_byte(config,0x33,config.getboolean('lcd', 'LCD_CMD')) # 110011 Initialise
   lcd_byte(config,0x32,config.getboolean('lcd', 'LCD_CMD')) # 110010 Initialise
   lcd_byte(config,0x06,config.getboolean('lcd', 'LCD_CMD')) # 000110 Cursor move direction
   lcd_byte(config,0x0C,config.getboolean('lcd', 'LCD_CMD')) # 001100 Display On,Cursor Off, Blink Off
   lcd_byte(config,0x28,config.getboolean('lcd', 'LCD_CMD')) # 101000 Data length, number of lines, font size
   lcd_byte(config,0x01,config.getboolean('lcd', 'LCD_CMD')) # 000001 Clear display
   time.sleep(config.getfloat('lcd', 'E_DELAY'))


def lcd_byte(config,bits, mode):

   # Send byte to data pins
   # bits = data
   # mode = True  for character
   #        False for command

   GPIO.output(config.getint('lcd', 'LCD_RS'), mode) # RS

   # High bits
   GPIO.output(config.getint('lcd', 'LCD_D4'), False)
   GPIO.output(config.getint('lcd', 'LCD_D5'), False)
   GPIO.output(config.getint('lcd', 'LCD_D6'), False)
   GPIO.output(config.getint('lcd', 'LCD_D7'), False)
   if bits&0x10==0x10:
     GPIO.output(config.getint('lcd', 'LCD_D4'), True)
   if bits&0x20==0x20:
     GPIO.output(config.getint('lcd', 'LCD_D5'), True)
   if bits&0x40==0x40:
     GPIO.output(config.getint('lcd', 'LCD_D6'), True)
   if bits&0x80==0x80:
     GPIO.output(config.getint('lcd', 'LCD_D7'), True)

   # Toggle 'Enable' pin
   lcd_toggle_enable(config)

   # Low bits
   GPIO.output(config.getint('lcd', 'LCD_D4'), False)
   GPIO.output(config.getint('lcd', 'LCD_D5'), False)
   GPIO.output(config.getint('lcd', 'LCD_D6'), False)
   GPIO.output(config.getint('lcd', 'LCD_D7'), False)
   if bits&0x01==0x01:
     GPIO.output(config.getint('lcd', 'LCD_D4'), True)
   if bits&0x02==0x02:
     GPIO.output(config.getint('lcd', 'LCD_D5'), True)
   if bits&0x04==0x04:
     GPIO.output(config.getint('lcd', 'LCD_D6'), True)
   if bits&0x08==0x08:
     GPIO.output(config.getint('lcd', 'LCD_D7'), True)

   # Toggle 'Enable' pin
   lcd_toggle_enable(config)

def lcd_toggle_enable(config):

 # Toggle enable
 time.sleep(config.getfloat('lcd', 'E_DELAY'))
 GPIO.output(config.getint('lcd', 'LCD_E'), True)
 time.sleep(config.getfloat('lcd', 'E_PULSE'))
 GPIO.output(config.getint('lcd', 'LCD_E'), False)
 time.sleep(config.getfloat('lcd', 'E_DELAY'))

def lcd_string(config,message,line):

 # Send string to display
 message = message.ljust(config.getint('lcd', 'LCD_WIDTH')," ")

 lcd_byte(config,line, config.getboolean('lcd', 'LCD_CMD'))

 for i in range(config.getint('lcd', 'LCD_WIDTH')):
   lcd_byte(config,ord(message[i]),config.getboolean('lcd', 'LCD_CHR'))
