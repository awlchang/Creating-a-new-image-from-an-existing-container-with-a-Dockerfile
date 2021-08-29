#!/bin/sh

interval=5 #second

temp_usb_device_num=$(lsusb | wc -l)
echo "The total number of USB device = "$temp_usb_device_num

while :
do
    usb_device_num=$(lsusb | wc -l)

    # echo "The total number of USB device = "$usb_device_num

    if [ $usb_device_num -gt $temp_usb_device_num ]; then
        temp_usb_device_num=$usb_device_num
        echo "device plug-in"
        pid=$(ps -ef | grep gateway | awk '{print $1}' | head -n 1)
        kill -15 $pid
    elif [ $usb_device_num -lt $temp_usb_device_num ]; then
        temp_usb_device_num=$usb_device_num
        echo "device unplug"
    fi

    sleep $interval

done &

if ! [ -f '/config.yaml' ]; then
    echo "There is no config.yaml! An example is created."
    cp /application/config.yaml.example /config.yaml.example
    exit 1
fi

cd /application
if [ "$DEBUG" = 'true' ]; then
    echo "Start in debug mode"
    python3 ./gateway.py -d
    status=$?
    echo "Gateway died..."
    exit $status
else
    echo "Start in normal mode"
    python3 ./gateway.py
fi
