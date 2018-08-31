#!/usr/bin/python
#
# Author : Matt Hawkins
# Date   : 06/04/2015
# http://www.raspberrypi-spy.co.uk/
#
# Author : Robert Coward/Paul Carpenter (based on driver by Matt Hawkins/)
# https://www.raspberrypi.org/forums/viewtopic.php?f=63&t=68055
# Date   : 02/03/2014
#
# Author : Audiophonics
# Date   : 23/09/2015 (V1.0)
# http://www.audiophonics.fr
# http://forum.audiophonics.fr/viewtopic.php?f=4&t=1492
#--------------------------------------

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND

#import
import RPi.GPIO as GPIO
import time
import subprocess;
import os;
from decimal import Decimal, ROUND_DOWN
process_name= "mpdlcd"

# Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 15


# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.001

def main():
  # Main program block

  GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
  GPIO.setup(LCD_E, GPIO.OUT)  # E
  GPIO.setup(LCD_RS, GPIO.OUT) # RS
  GPIO.setup(LCD_D4, GPIO.OUT) # DB4
  GPIO.setup(LCD_D5, GPIO.OUT) # DB5
  GPIO.setup(LCD_D6, GPIO.OUT) # DB6
  GPIO.setup(LCD_D7, GPIO.OUT) # DB7


  # Initialise display
  lcd_init()
  
  
  while True:

    cmdA = "mpc | head -2 | tail -1 | awk '{print $1}'" # gets the player state ie paused playing etc
    process = subprocess.Popen(cmdA, stdout=subprocess.PIPE , shell=True)
    os.waitpid(process.pid, 0)[1]
    mpc_state = process.stdout.read().strip()
    
    cmdB = "hostname -I"  #gets the current ip
    process2 = subprocess.Popen(cmdB, stdout=subprocess.PIPE , shell=True)
    os.waitpid(process2.pid, 0)[1]
    ip_addr = process2.stdout.read().strip()


    if mpc_state != "[playing]": 
    
        lcd_string("Ready",LCD_LINE_1)
        lcd_string(ip_addr,LCD_LINE_2)        
        time.sleep(3) # 3 second delay
    
    else :
    
        cmd1 = "mpc | head -1 | cut -d'-' -f2"        # Titre
        process = subprocess.Popen(cmd1, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_song = process.stdout.read().strip()
    
        cmd2 = "mpc | head -1 | cut -d'-' -f1"  # Artist
        process = subprocess.Popen(cmd2, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_artist = process.stdout.read().strip()
        
        cmd4 = "mpc | head -2 | tail -1 | cut -d' ' -f5"  # 00:00/00:00
        process = subprocess.Popen(cmd4, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_time = process.stdout.read().strip()
        
        cmd5 = "mpc | head -2 | tail -1 | cut -d' ' -f2 | cut -c 2-8" # 00/00
        process = subprocess.Popen(cmd5, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_pos = process.stdout.read().strip()    
        
        mpc_timepos = mpc_pos + " " + mpc_time
    
        # Song / Position - Time
        lcd_string(mpc_song,LCD_LINE_1)
        lcd_string(mpc_timepos,LCD_LINE_2)

        # Time refresh
        cmd4 = "mpc | head -2 | tail -1 | cut -d' ' -f5"  # 00:00/00:00
        process = subprocess.Popen(cmd4, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_time = process.stdout.read().strip()
        mpc_timepos = mpc_pos + " " + mpc_time
    
        lcd_string(mpc_timepos,LCD_LINE_2)
    
        # Time refresh
        cmd4 = "mpc | head -2 | tail -1 | cut -d' ' -f5"  # 00:00/00:00
        process = subprocess.Popen(cmd4, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_time = process.stdout.read().strip()
        mpc_timepos = mpc_pos + " " + mpc_time
    
        lcd_string(mpc_timepos,LCD_LINE_2)
        
        # Time refresh
        cmd4 = "mpc | head -2 | tail -1 | cut -d' ' -f5"  # 00:00/00:00
        process = subprocess.Popen(cmd4, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_time = process.stdout.read().strip()
        mpc_timepos = mpc_pos + " " + mpc_time
        
        # Artist / Position - Time
        lcd_string(mpc_artist,LCD_LINE_1)
        lcd_string(mpc_timepos,LCD_LINE_2)
        
        # Time refresh
        cmd4 = "mpc | head -2 | tail -1 | cut -d' ' -f5"  # 00:00/00:00
        process = subprocess.Popen(cmd4, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_time = process.stdout.read().strip()
        mpc_timepos = mpc_pos + " " + mpc_time
    
        lcd_string(mpc_timepos,LCD_LINE_2)
    
        # Time refresh
        cmd4 = "mpc | head -2 | tail -1 | cut -d' ' -f5"  # 00:00/00:00
        process = subprocess.Popen(cmd4, stdout=subprocess.PIPE , shell=True)
        os.waitpid(process.pid, 0)[1]
        mpc_time = process.stdout.read().strip()
        mpc_timepos = mpc_pos + " " + mpc_time
    
        lcd_string(mpc_timepos,LCD_LINE_2)    
    
        time.sleep(1)

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction  
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x08,LCD_CMD) # Display off OLED ADD
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(0.01)
  # extra steps required for OLED initialisation (no effect on LCD)
  lcd_byte(0x17, LCD_CMD)    # character mode, power on      OLED ADD

  # now turn on the display, ready for use - IMPORTANT!
  lcd_byte(0x0C, LCD_CMD)    # display on, cursor/blink off     OLED ADD

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  #        False for command

  GPIO.output(LCD_RS, mode) # RS

  # High bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  lcd_toggle_enable()

  # Low bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  lcd_toggle_enable()

def lcd_toggle_enable():
  # Toggle enable
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display




  message = message.center(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

if __name__ == '__main__':

  try:
    main()
  except KeyboardInterrupt:
    pass
  finally:
    lcd_byte(0x01, LCD_CMD)
    lcd_string("Goodbye!",LCD_LINE_1)
    GPIO.cleanup()
