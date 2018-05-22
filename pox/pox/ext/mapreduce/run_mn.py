import argparse
import simplejson as json
import os
import pickle
import random
import subprocess
import sys
from time import sleep, time

from collections import defaultdict
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI


class TestTop(Topo):

    def build(self, config):

        self.addSwitch('s0')
        '''
        self.addHost('h0', ip='10.0.0.1')
        self.addHost('h1', ip='10.0.0.2')
        self.addHost('h2', ip='10.0.0.3')

        self.addLink('h0', 's0')
        self.addLink('h1', 's0')
        self.addLink('h2', 's0')
        '''
        hosts = []
        for h in config["master"]: # should only be one
            self.addHost(h, ip=config["master"][h][0])
            hosts.append(h)

        for h in config["workers"]:
            self.addHost(h, ip=config["workers"][h][0])
            hosts.append(h)
        
        for h in hosts:
            self.addLink(h, 's0')


def cleanmn():
    sys.stdout.write("Cleaning Mininet...")
    sys.stdout.flush()
    FNULL = open(os.devnull, 'w')
    subprocess.call(["sudo", "mn" , "-c"], stdout=FNULL, stderr=subprocess.STDOUT)
    sys.stdout.write(" done\n")
    sys.stdout.flush()


def experiment(net, config):
    net.start()
    sleep(3)
    net.pingAll()

    master_k, master_v = config["master"].items()[0]
    master_addr_port = ":".join(master_v)

    # CLI(net)
    for w, v in config["workers"].items():
        net.get(w).sendCmd("./wordcount" , "-w", "-a", ":".join(v), "-m", master_addr_port)

    master = net.get(master_k)
    master.sendCmd("./wordcount", "-p", "-r", "10", "-m", master_addr_port, "./data/input/pg-*.txt")

    print(master.waitOutput())

def build_and_run(config_path):

    with open(config_path, 'r') as f:
        config = json.load(f)

    topo = TestTop(config)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink)

    experiment(net, config)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run mapreduce in simple mininet topology.")
    parser.add_argument('--config', help='Config file path', default=None)
    '''
    parser.add_argument('--algo', help='Path algorithm', default='kshort', choices=['kshort', 'ecmp'])
    parser.add_argument('--nflows', help='Number of flows between two servers', choices=['1', '8'], default='1')
    parser.add_argument('--output', help='Output data pickle path', default=None)
    '''
    args = parser.parse_args()

    cleanmn()
    build_and_run(args.config)

