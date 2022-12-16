#!/bin/bash

# apply boot config
sudo cp --backup=numbered boot/config.txt /boot/config.txt

# install necessary software
sudo apt install -y mpd mpc alsa-utils