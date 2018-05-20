import os
import sys
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.node import OVSController
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
sys.path.append("../../")
from pox.ext.jelly_pox import JELLYPOX
from subprocess import Popen
from time import sleep, time
import pickle

pkl = '/home/diveesh/cs244-final-project/poxStartup/pox/pox/ext/small_topo.pickle'

class JellyFishTop(Topo):
    ''' TODO, build your topology here'''

    def build(self):
        topo = pickle.load(open(pkl, 'r'))
        outport_mappings = topo['outport_mappings']
        print outport_mappings
        self.mn_hosts = []
        for h in range(topo['n_hosts']):
            hosts_from_graph = topo['graph'].nodes(data='ip')
            for host in hosts_from_graph:
                if host[0] == 'h' + str(h):
                    break
            print host
            self.mn_hosts.append(self.addHost('h' + str(h), ip=host[1]))

        self.mn_switches = []
        for s in range(topo['n_switches']):
            self.mn_switches.append(self.addSwitch('s' + str(s + 1), mac="00:00:00:00:00:" + str("{:02x}".format(s + 1))))

        for e in topo['graph'].edges():
            if e[0][0] == 'h':
                f1 = self.mn_hosts[int(e[0][1:])]
                f1_graph = f1
                switch1 = False
            else:
                f1 = self.mn_switches[int(e[0][1:])]
                f1_graph = 's' + str(int(f1[1:]) - 1)
                switch1 = True 

            if e[1][0] == 'h':
                f2 = self.mn_hosts[int(e[1][1:])]
                f2_graph = f2
                switch2 = False
            else:
                f2 = self.mn_switches[int(e[1][1:])]
                f2_graph = 's' + str(int(f2[1:]) - 1)
                switch2 = True 

            port1 = outport_mappings[(f1_graph, f2_graph)]
            port2 = outport_mappings[(f2_graph, f1_graph)]

            self.addLink(f1, f2, bw=5, port1=port1, port2=port2, use_htb=True)

        self.topo = topo

def experiment(net):
        net.start()
        sleep(3)
        net.pingAll()
        net.stop()

def main():
	topo = JellyFishTop()
	net = Mininet(topo=topo, host=CPULimitedHost, link = TCLink, controller=JELLYPOX)
	experiment(net)

if __name__ == "__main__":
	main()

