#!/bin/bash

# apply boot config
sudo cp --backup=numbered config/boot/config.txt /boot/config.txt

# install necessary software
sudo apt install -y mpd mpc alsa-utils

# copy config files
sudo cp --backup=numbered config/etc/asound.conf /etc/asound.conf
sudo cp --backup=numbered config/etc/mpd.conf /etc/mpd.conf