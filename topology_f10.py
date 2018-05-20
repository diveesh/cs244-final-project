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

    #likely only works for L=2
    for i in range(L, -1, -1):
        num_groups = 2 * p ** (L - i)
        num_switches_per_group = p ** i

        # add nodes for L2
        if i == L:
            for j in range(n_switches_per_layer / 2): # for each switch on L2
                switch_num = i * num_groups * num_switches_per_group + j
                G.add_node('s' + str(switch_num))
            
        else:
            for m in range(num_groups): # group num
                for j in range(num_switches_per_group): # index within group
                    switch_num = i * num_groups * num_switches_per_group + m * num_switches_per_group + j
                    G.add_node('s' + str(switch_num)) #update naming scheme once figured

                    if i == 0: # from L0 to servers
                        for n in range(num_servers_per_switch):
                            open_ports[switch_num] -= 1
                            curr_switch = 's' + str(switch_num)
                            curr_host = 'h' + str(switch_num * num_servers_per_switch + n)
                            G.add_edge(curr_switch, curr_host)
                            outport_mappings[(curr_switch, curr_host)] = open_ports[switch_num]
                            outport_mappings[(curr_host, curr_switch)] = 1

                    for n in range(p):
                        if i == 0: #L0 to L1
                            to_switch_num = (switch_num / p) * p + n_switches_per_layer * (i + 1) + n
                        else: #L1 to L2
                            if m % 2 == 0: #A subtree
                                to_switch_num = (i + 1) * n_switches_per_layer + j * p + n
                            else: #B subtree
                                to_switch_num = (i + 1) * n_switches_per_layer + n * p + j
                        open_ports[switch_num] -= 1
                        open_ports[to_switch_num] -= 1
                        from_switch = 's' + str(switch_num)
                        to_switch = 's' + str(to_switch_num)
                        G.add_edge(from_switch, to_switch)
                        outport_mappings[(from_switch, to_switch)] = open_ports[switch_num]
                        outport_mappings[(to_switch, from_switch)] = open_ports[to_switch_num]
    return topo

                    # if i == 0:
                        
                    #     #links from L0 to L1
                    #     for n in range(p):
                    #         to_switch_num = (switch_num / p) * p + n_switches_per_layer * (i + 1) + n
                    #         open_ports[switch_num] -= 1
                    #         open_ports[to_switch_num] -= 1
                    #         from_switch = 's' + str(switch_num)
                    #         to_switch = 's' + str(to_switch_num)
                    #         G.add_edge(from_switch, to_switch)
                    #         outport_mappings[(from_switch, to_switch)] = open_ports[switch_num]
                    #         outport_mappings[(to_switch, from_switch)] = open_ports[to_switch_num]

                    #     # close extra ports to ensure consistency
                    #     # open_ports[switch_num] = num_servers_per_switch
                    #     # links from L0 to servers
                    #     for n in range(num_servers_per_switch):
                    #         open_ports[switch_num] -= 1
                    #         curr_switch = 's' + str(switch_num)
                    #         curr_host = 'h' + str(switch_num * num_servers_per_switch + n)
                    #         G.add_edge(curr_switch, curr_host)
                    #         outport_mappings[(curr_switch, curr_host)] = open_ports[switch_num]
                    #         outport_mappings[(curr_host, curr_switch)] = 1
                        
                        
                    # else:
                    #     #L1 to L2
                    #     for n in range(p):
                    #         if m % 2 == 0: #A subtree
                    #             to_switch_num = ((i + 1) * n_switches_per_layer + j * p + n)
                    #         else: #B subtree
                    #             pass

                    #         open_ports[switch_num] -= 1
                    #         open_ports[to_switch_num] -= 1
                    #         from_switch = 's' + str(switch_num)
                    #         to_switch = 's' + str(to_switch_num)
                    #         G.add_edge(from_switch, to_switch)
                    #         outport_mappings[(from_switch, to_switch)] = open_ports[switch_num]
                    #         outport_mappings[(to_switch, from_switch)] = open_ports[to_switch_num]
                            
                        

    

