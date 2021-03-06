import argparse
import os
import pickle
import random
import simplejson as json
import subprocess
import sys
from threading import Timer
from time import sleep, time

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI

sys.path.append("../../")
from pox.ext.f10_pox import F10POX


def mac_from_value(v):
    return ':'.join(s.encode('hex') for s in ('%0.12x' % v).decode('hex'))


class F10Top(Topo):
    def build(self, pkl):
        topo = pickle.load(open(pkl, 'r'))
        outport_mappings = topo['outport_mappings']
        # print outport_mappings
        self.mn_hosts = []
        for h in range(topo['n_hosts']): 
            hosts_from_graph = topo['graph'].nodes(data='ip')
            for host in hosts_from_graph:
                if host[0] == 'h' + str(h):
                    break
            # print host
            self.mn_hosts.append(self.addHost('h' + str(h), ip=host[1]))

        self.mn_switches = []
        for s in range(topo['n_switches']):
            nodes_from_graph = topo['graph'].nodes(data='ip')
            for node in nodes_from_graph:
                if node[0] == 's' + str(s):
                    break
            # print node
            self.mn_switches.append(self.addSwitch('s' + str(s + 1), mac="00:00:00:00:00:" + str("{:02x}".format(s + 1)), ip=node[1]))

        for e in topo['graph'].edges():
            if e[0][0] == 'h':
                f1 = self.mn_hosts[int(e[0][1:])]
                f1_graph = f1
            else:
                f1 = self.mn_switches[int(e[0][1:])]
                f1_graph = 's' + str(int(f1[1:]) - 1)

            if e[1][0] == 'h':
                f2 = self.mn_hosts[int(e[1][1:])]
                f2_graph = f2
            else:
                f2 = self.mn_switches[int(e[1][1:])]
                f2_graph = 's' + str(int(f2[1:]) - 1)

            port1 = outport_mappings[(f1_graph, f2_graph)]
            port2 = outport_mappings[(f2_graph, f1_graph)]

            self.addLink(f1, f2, port1=port1, port2=port2, bw=10)

        self.topo = topo


def experiment(net, topo, mr_config_data, fail, fail_len, fail_time):
    net.start()

    sys.stdout.write("Waiting 3 seconds for Mininet to start...")
    sys.stdout.flush()
    sleep(3)
    sys.stdout.write(" done.\n")
    sys.stdout.flush()

    net.pingAll()

    def stop_switch():
        sys.stdout.write("\nStopping switch 's9'...") # left-most L = 1
        sys.stdout.flush()
        node = net.getNodeByName('s10')
        node.stop()
        sys.stdout.write(" done.\n\n")
        sys.stdout.flush()

    t = Timer(fail_time, stop_switch)
    if fail:
    	t.start()

    host_a = net.getNodeByName('h0')
    host_b = net.getNodeByName('h11')
	
    host_a.sendCmd("iperf3", "-s", "-1")
    host_b.sendCmd("iperf3", "-c", "10.0.0.1", "-t", str(int(fail_len)))
    out = host_b.waitOutput()
    print(out)

    ### MAP REDUCE ###

    if mr_config_data:

        sys.stdout.write("Running map-reduce on topology...")
        sys.stdout.flush()
    
        master_k, master_v = mr_config_data["master"].items()[0]
        master_addr_port = ":".join(master_v)

        for w, v in mr_config_data["workers"].items():
            net.get(w).sendCmd("cd", "mapreduce", "&&", "./wordcount" , "-w", "-a", ":".join(v), "-m", master_addr_port)

        master = net.get(master_k)
        master.sendCmd("cd", "mapreduce", "&&", "./wordcount", "-p", "-r", "32", "-m", master_addr_port, "./data/input/pg-*.txt")
        master.monitor()

        output = master.waitOutput()
        sys.stdout.write(" done.\n")
        sys.stdout.flush()
        print("MapReduce Output:")
        print(output)


def main(p, mr_config, fail_test, fail_len, fail_time):
    topo = F10Top(pkl=p)
    net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=F10POX("f10", cargs2=("--p=%s" % (p))))

    host_to_ip = topo.topo['host_to_ip']

    host_mac_base = len(topo.mn_switches)
    for i, h in enumerate(topo.mn_hosts):
        mn_host = net.getNodeByName(h)
        # print h, mac_from_value(host_mac_base + i + 1)
        mn_host.setMAC(mac_from_value(host_mac_base + i + 1))
        for j, h2 in enumerate(topo.mn_hosts):
            if i == j: continue
            mn_host2 = net.getNodeByName(h2)
            # print "Setting arp for host " + str(h) + ", index " + str(i) + ". j " + str(j) + ", mac is " + mac_from_value(host_mac_base + j + 1)
            mn_host.setARP(host_to_ip[j], mac_from_value(host_mac_base + j + 1))

    if mr_config:
        with open(mr_config, 'r') as f:
            mr_config_data = json.load(f)
    else:
        mr_config_data = None

    experiment(net, topo, mr_config_data, fail_test, fail_len, fail_time)


def cleanmn():
    sys.stdout.write("Cleaning Mininet...")
    sys.stdout.flush()
    FNULL = open(os.devnull, 'w')
    subprocess.call(["sudo", "mn" , "-c"], stdout=FNULL, stderr=subprocess.STDOUT)
    sys.stdout.write(" done\n")
    sys.stdout.flush()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run F10 topology.")
    parser.add_argument('--pickle', help='Topology pickle input path', default=None)
    parser.add_argument('--mr_config', help='Map-Reduce configuration', default=None)
    parser.add_argument('--fail_test', help='Run iperf TCP cwnd test with failed switch', action='store_true', default=False)
    parser.add_argument('--fail_len', help='Iperf TCP cwnd test: total length', default=20, type=int)
    parser.add_argument('--fail_time', help='Iperf TCP cwnd test: switch failure time (seconds)', default=15, type=int)
    args = parser.parse_args()

    cleanmn()

    main(args.pickle, args.mr_config, args.fail_test, args.fail_len, args.fail_time)

