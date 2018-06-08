#!/bin/bash

rm data.out
sudo rmmod tcp_probe

sudo modprobe tcp_probe
sudo chmod 444 /proc/net/tcpprobe
cat /proc/net/tcpprobe > data.out &
CAT_PID=$!
sudo python build_topology.py --pickle /home/jeanluc.watson/cs244-final-project/pox/pox/ext/test.pickle
sudo kill $CAT_PID
python parse.py > cwnd.csv

