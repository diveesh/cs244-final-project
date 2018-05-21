import argparse
import copy
import networkx as nx
import os
import pickle
import random
import sys

from collections import defaultdict
from subprocess import Popen
import math
import struct
import socket

import matplotlib.pyplot as plt 

RNG_SEED = 0xBAEF

k = 24
p = k / 2
L = 2


def generate_topology(n_servers, k=24, L=2, debug=False):
    G = nx.Graph()
    topo = {}
    outport_mappings = {}
    switch_to_ip = {}
    host_to_ip = {}
    topo["graph"] = G
    topo["n_ports"] = k
    topo["n_hosts"] = n_servers
    topo["outport_mappings"] = outport_mappings
    topo["switch_to_ip"] = switch_to_ip
    topo["host_to_ip"] = host_to_ip

    p = k / 2

    location_bit_length = int(2 * math.ceil(math.log(p, 2))) + 1
    padding = 16 - location_bit_length
    n_switches_per_layer = 2 * p ** L
    num_servers_per_switch = n_servers / n_switches_per_layer

    total_switches = n_switches_per_layer * L + n_switches_per_layer / 2

    open_ports = [k] * total_switches

    topo["n_switches"] = total_switches 


    for loc in range(2 ** location_bit_length):
        for c in range(num_servers_per_switch):
            ip = socket.inet_ntoa(struct.pack('!L', 10 << 24 | loc << 10 | (c + 1)))
            host_num = loc * num_servers_per_switch + c
            host_to_ip[host_num] = ip
            G.add_node('h'+str(host_num), ip=ip) #naming scheme

    print 'switches'
    #likely only works for L=2
    for i in range(L, -1, -1):
        num_groups = 2 * p ** (L - i)
        num_switches_per_group = p ** i

        # add nodes for L2
        if i == L:
            for j in range(n_switches_per_layer / 2): # for each switch on L2
                switch_num = i * num_groups * num_switches_per_group + j
                ip = socket.inet_ntoa(struct.pack('!L', 10 << 24 | i << 8 | j))
                switch_to_ip['s' + str(switch_num)] = ip
                G.add_node('s' + str(switch_num), ip=ip)
        else:
            for m in range(num_groups): # group num
                for j in range(num_switches_per_group): # index within group
                    switch_num = i * num_groups * num_switches_per_group + m * num_switches_per_group + j
                    loc = m * p ** i
                    ip = socket.inet_ntoa(struct.pack('!L', 10 << 24 | loc << 10 | i << 8 | j))
                    switch_to_ip['s' + str(switch_num)] = ip
                    G.add_node('s' + str(switch_num), ip=ip) #update naming scheme once figured

                    if i == 0: # from L0 to servers
                        for n in range(num_servers_per_switch):
                            curr_switch = 's' + str(switch_num)
                            curr_host = 'h' + str(switch_num * num_servers_per_switch + n)
                            G.add_edge(curr_switch, curr_host)
                            outport_mappings[(curr_switch, curr_host)] = open_ports[switch_num]
                            outport_mappings[(curr_host, curr_switch)] = 1
                            open_ports[switch_num] -= 1

                    for n in range(p):
                        if i == 0: #L0 to L1
                            to_switch_num = (switch_num / p) * p + n_switches_per_layer * (i + 1) + n
                        else: #L1 to L2
                            if m % 2 == 0: #A subtree
                                to_switch_num = (i + 1) * n_switches_per_layer + j * p + n
                            else: #B subtree
                                to_switch_num = (i + 1) * n_switches_per_layer + n * p ** i + j
                        from_switch = 's' + str(switch_num)
                        to_switch = 's' + str(to_switch_num)
                        G.add_edge(from_switch, to_switch)
                        outport_mappings[(from_switch, to_switch)] = open_ports[switch_num]
                        outport_mappings[(to_switch, from_switch)] = open_ports[to_switch_num]
                        open_ports[switch_num] -= 1
                        open_ports[to_switch_num] -= 1
    return topo
                            
                        

    

