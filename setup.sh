#!/bin/bash

# apply boot config
sudo cp --backup=numbered sys_config/boot/config.txt /boot/config.txt

# install necessary software
sudo apt install -y mpd mpc alsa-utils

# copy config files
sudo cp --backup=numbered sys_config/etc/asound.conf /etc/asound.conf
sudo cp --backup=numbered sys_config/etc/mpd.conf /etc/mpd.conf

# copy init script
sudo cp --backup=numbered sys_config/etc/init.d/radio /etc/init.d/radio
sudo chmod 755 /etc/init.d/radio
sudo update-rc.d radio defaults
