import argparse
import copy
import networkx as nx
import os
import pickle
import random
import sys

from collections import defaultdict
from subprocess import Popen

import matplotlib.pyplot as plt 

RNG_SEED = 0xBAEF

k = 24
p = k / 2
L = 2


def generate_topology(n_servers, k=24, L=2, debug=False):
    G = nx.Graph()
    topo = {}
    outport_mappings = {}
    topo["graph"] = G
    topo["n_ports"] = k
    topo["n_hosts"] = n_servers
    topo["outport_mappings"] = outport_mappings

    for s in range(n_servers):
        G.add_node('h'+str(s), ip = '10.6.' + str(s) + '.1') #naming scheme

    p = k / 2



    n_switches_per_layer = 2 * p ** L
    num_servers_per_switch = n_servers / n_switches_per_layer

    total_switches = n_switches_per_layer * L + n_switches_per_layer / 2

    open_ports = [k] * total_switches

    for i in range(L + 1):
        num_groups = 2 * p ** (L - i)
        num_switches_per_group = p ** i
        if i == L:
            for j in range(n_switches_per_layer / 2): # for each switch
                switch_num = i * num_groups * num_switches_per_group + j
                G.add_node('s' + str(switch_num))
                for m in range(k): # iterate over all ports, set up A subtree and B subtree
                    pass
            
        else:
            for m in range(num_groups):
                for j in range(num_switches_per_group):
                    switch_num = i * num_groups * num_switches_per_group + m * num_switches_per_group + j
                    G.add_node('s' + str(switch_num)) #update naming scheme once figured
                    if i == 0:
                        for n in range(num_servers_per_switch):
                            open_ports[switch_num] -= 1
                            curr_switch = 's' + str(switch_num)
                            curr_host = 'h' + str(switch_num * num_servers_per_switch + n)
                            G.add_edge(curr_switch, curr_host)
                            outport_mappings[(curr_switch, curr_host)] = open_ports[switch_num]
                            outport_mappings[(curr_host, curr_switch)] = 1
                        # close extra ports to ensure consistency
                        open_ports[switch_num] = p
                    else:
                        # each node at L1 has p links going down to L0
                        for n in range(p):
                            pass
                        pass
                        #add

