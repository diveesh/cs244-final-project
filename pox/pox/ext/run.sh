#!/bin/bash

echo "Cleaning files..."
rm data.out 2>/dev/null
rm *.csv 2>/dev/null
sudo rmmod tcp_probe 2>/dev/null

echo
echo "Installing tcp_probe module..."
sudo modprobe tcp_probe
sudo chmod 444 /proc/net/tcpprobe

PWD="$(pwd)"
# Run 20 second tests like in the F10 paper

echo
echo "** Running cwnd test(20, 15) with no failed switches **"
cat /proc/net/tcpprobe > data.out &
CAT_PID=$!
sudo python build_topology.py --pickle $PWD/test.pickle
sudo kill $CAT_PID
echo
echo "    saving output to 'cwnd.csv'"
python parse.py > cwnd.csv

echo
echo "** Running cwnd test(20, 15) with a failed switch **"
cat /proc/net/tcpprobe > data.out &
CAT_FAIL_PID=$!
sudo python build_topology.py --pickle $PWD/test.pickle --fail_test
sudo kill $CAT_FAIL_PID
echo "    saving output to 'fail_cwnd.csv'"
echo
python parse.py > fail_cwnd.csv

# Run longer test to see more behavior

echo
echo "** Running cwnd test(45, 30) with no failed switches **"
cat /proc/net/tcpprobe > data.out &
CAT_PID=$!
sudo python build_topology.py --pickle $PWD/test.pickle --fail_len 45 --fail_time 30
sudo kill $CAT_PID

echo
echo "    saving output to 'cwnd_long.csv'"
python parse.py > cwnd_long.csv

echo
echo "** Running cwnd test(45, 30) with a failed switch **"
cat /proc/net/tcpprobe > data.out &
CAT_FAIL_PID=$!
sudo python build_topology.py --pickle $PWD/test.pickle --fail_test --fail_len 45 --fail_time 30
sudo kill $CAT_FAIL_PID
echo "    saving output to 'fail_cwnd_long.csv'"
echo
python parse.py > fail_cwnd_long.csv

echo
echo "Generating graphs"
python graph6.py cwnd.csv fail_cwnd.csv fig6.eps --fail_time 15
python graph6.py cwnd_long.csv fail_cwnd_long.csv fig6_long.eps --fail_time 30

echo
echo "Done"
