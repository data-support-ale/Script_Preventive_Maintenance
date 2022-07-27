#!/bin/bash
for filename in support_switch*; do
    echo "------------------------------"
    echo "                              "
    echo $filename
    sudo python3 $filename fff | grep "Traceback"
    echo "                              "
    echo "------------------------------"
done
for filename in support_wlan*; do
    echo "------------------------------"
    echo "                              "
    echo $filename
    sudo python3 $filename fff | grep "Traceback"
    echo "                              "
    echo "------------------------------"
done
for filename in support_server*; do
    echo "------------------------------"
    echo "                              "
    echo $filename
    sudo python3 $filename fff | grep "Traceback"
    echo "                              "
    echo "------------------------------"
done