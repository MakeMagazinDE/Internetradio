#!/bin/bash

# apply boot config
sudo cp --backup=numbered boot/config.txt /boot/config.txt

# install necessary software
sudo apt install -y mpd mpc alsa-utils

# copy config files
sudo cp --backup=numbered etc/asound.conf /etc/asound.conf
sudo cp --backup=numbered etc/mpd.conf /etc/mpd.conf