cd ..
git clone git://github.com/mininet/mininet.git
cd mininet
git checkout 2.2.2
util/install.sh -a
cd ../cs244-final-project
sudo apt install python-pip
sudo apt install iperf3
sudo pip install networkx
sudo pip install matplotlib
sudo pip install simplejson 

