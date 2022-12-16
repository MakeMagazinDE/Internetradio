#!/usr/bin/python coding=utf-8

# Shutdown für RaspiRadio

from lcd_display import lcd

my_lcd=lcd()
my_lcd.display_string("--------------------", 1)
my_lcd.display_string(" Bitte kurz warten, ", 2)
my_lcd.display_string(" dann ausschalten.  ", 3)
my_lcd.display_string("--------------------", 4)


