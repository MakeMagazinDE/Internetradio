#!/bin/bash -x

# apply boot config
if ! diff -w sys_config/boot/config.txt /boot/config.txt > /dev/null
then
    echo "Install updated config.txt"
    sudo cp --backup=numbered sys_config/boot/config.txt /boot/config.txt
fi

# install necessary software
sudo apt install -y mpd mpc mpg321 alsa-utils python3-pip i2c-tools

# create necessary firs
mkdir -p /home/kradio/raspiradio/music

# copy config files
if ! diff -w sys_config/etc/asound.conf /etc/asound.conf > /dev/null
then
    echo "Install updated asound.conf"
    sudo cp --backup=numbered sys_config/etc/asound.conf /etc/asound.conf
fi
if ! diff -w sys_config/etc/mpd.conf /etc/mpd.conf > /dev/null
then
    echo "Install updated mpd.conf"
    sudo cp --backup=numbered sys_config/etc/mpd.conf /etc/mpd.conf
fi

# copy init script
if ! diff -w sys_config/lib/systemd/system/radio.service /etc/systemd/system/kradio.service > /dev/null
then
    echo "Install updated systemd service"
    (sudo /etc/init.d/radio stop && sudo rm /etc/init.d/radio) || true
    sudo cp --backup=numbered sys_config/lib/systemd/system/radio.service /etc/systemd/system/kradio.service
    sudo systemctl daemon-reload
    sudo systemctl enable kradio.service
    sudo systemctl start kradio.service
fi

# Python dependencies
#pip install -r requirements.txt
