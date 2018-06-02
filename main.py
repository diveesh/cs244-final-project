import argparse
import networkx as nx
import pickle
import random
import sys
from collections import defaultdict, OrderedDict, Counter
from itertools import islice
from time import sleep, time
import copy 
import numpy as np
import math

from topology import generate_ab_topology

fail_switches = [0, 1, 5]

def ip_to_val(ip):
    byte_list = ip.split('.')
    val = 0
    for i in range(len(byte_list)):
        idx = len(byte_list) - i - 1 
        val |= (int(byte_list[idx]) << (i * 8))

    return val


def index(ip_val):
    return ip_val & 0xff

def level(ip_val):
    return (ip_val >> 8) & 0b11

def location(ip_val):
    return (ip_val >> 10) & 0x3fff

def get_neighbor_ips(topology, s, switch_to_ip):
    neighbors = topology.neighbors(s)
    m = {}
    for n in neighbors:
        if n[0] == 's':
            m[n] = switch_to_ip[n]
    return m

def find_fat_path(modified_topo, i, j, L, failed_switches):
    pass

def find_ab_path(topo_map, i, j, p, L, failed_switches):

    topology = topo_map['graph']
    host_to_ip = topo_map['host_to_ip']
    switch_to_ip = topo_map['switch_to_ip']
    opm = topo_map['outport_mappings']
    spm = topo_map['switch_port_mappings']
    n_ports = topo_map['n_ports']
    num_switches_per_layer = 2 * p ** L
    num_hosts_per_switch = topo_map['n_hosts'] / num_switches_per_layer
    print num_hosts_per_switch

    dstip = host_to_ip[j]
    dest_location = location(ip_to_val(dstip))
    b = int(math.ceil(math.log((topo_map['n_ports'] / 2), 2)))
    
    curr_switch = 's' + str(i / num_hosts_per_switch)
    dest_switch = 's' + str(j / num_hosts_per_switch)

    path = []
    print 'destination switch is ' + dest_switch
    prev_lvl = -1
    prev_switch = None
    failure_group_nodes = set()

    print "Finding path between " + str(i) + " and " + str(j) + ". Failed switches are " + str(failed_switches)
    while True:

        path.append(curr_switch)
        if curr_switch == dest_switch:
            break

        ip_val = ip_to_val(switch_to_ip[curr_switch])

        lvl, idx, loc = level(ip_val), index(ip_val), location(ip_val)
        sw_prefix, dest_prefix = (loc >> (b * lvl)), (dest_location >> (b * lvl)) 
        neighbor_ips = get_neighbor_ips(topology, curr_switch, switch_to_ip)

        print "Currently at level " + str(lvl) + ". Curr switch is " + curr_switch + ". "

        if sw_prefix == dest_prefix or lvl == 2: #route down for sure cuz either at highest level, or our destination is in subtree
            print "In the main routing down case"
            # don't need to explicitly send to host because we only care about the switch that the host is connected to
            next_prefix = dest_location >> (b * (lvl - 1))
            if lvl == 2:
                next_bits = next_prefix & ((2 ** (b+1)) - 1)
            else:
                next_bits = next_prefix & ((2 ** b) - 1)

            # find neighbors that are directly on the path to destination node
            print "Current switch name: " + str(curr_switch) + ", lvl: " + str(lvl) + ", idx: " + str(idx) + ", loc: " + str(loc)
            print "This is the next prefix " + str(next_prefix) 
            print "Final dest loc is " + str(dest_location)
            print "b is " + str(b)
            print "This is all the neighbors info:"
            for k, v in neighbor_ips.items():
                k_ip_val = ip_to_val(switch_to_ip[k])
                k_lvl, k_idx, k_loc = level(k_ip_val), index(k_ip_val), location(k_ip_val)
                print "\tNeighbor switch name: " + str(k) + ", lvl: " + str(k_lvl) + ", idx: " + str(k_idx) + ", loc: " + str(k_loc)

            valid_neighbors = [k for k,v in neighbor_ips.items() if (location(ip_to_val(v)) >> (b * (lvl - 1))) == next_prefix]
            print "The OG valid neighbors are " + str(valid_neighbors)
            invalid_ports = set()
            if len(valid_neighbors) == 1:
                k = valid_neighbors[0]
                outport = opm[(curr_switch, k)] #indicates "intended" subtree, based on odd or even value

                if k in failed_switches: # the switch we want to send to has failed

                    # update failure group with all parents of failed switch
                    k_lvl = level(ip_to_val(switch_to_ip[k]))
                    if k_lvl == 1:
                        for up_port_num in range(n_ports / 2, n_ports):
                            failure_group_nodes.add(spm[(k, up_port_num + 1)])
                    print "After updating the failure group, its " + str(failure_group_nodes)

                    temp_invalid_ports = set()
                    if outport % 2 == 0: # if intended is B subtree, temporarily invalidate all other paths to B subtrees
                        for i in range(n_ports / 2):
                            temp_invalid_ports.add(i * 2 + 2)
                    if outport % 2 == 1: # if intended is A subtree, temporarily invalidate all other paths to A subtrees
                        for i in range(n_ports / 2):
                            temp_invalid_ports.add(i * 2 + 1)
                    for fs in failed_switches:
                        if (curr_switch, fs) in opm:
                            invalid_ports.add(opm[(curr_switch, fs)])

                    print "Here are the temp_invalid_ports (should be all of one subtree) " + str(temp_invalid_ports)
                    print "Here are the actual invalid ports (due to failed switches) " + str(invalid_ports)

                    # we've "invalidated" all paths to subtrees that are of the same type as the intended one, plus all the actual failed
                    # if there are none left, this means the following
                    # if the intended subtree was A, and the intended node is dead, and all paths to B subtrees are dead (and vice versa)
                    # now we must send out of the A subtree, but not to the node that is dead (5 hop)
                    if len(invalid_ports | temp_invalid_ports) == n_ports:
                        potential_ports = temp_invalid_ports - invalid_ports
                           
                    else: # we have the potential to send to the other subtree, so we do (3-hop)
                        potential_ports = set(range(1, n_ports + 1)) - (invalid_ports | temp_invalid_ports) # eliminate all ports that point to the same type as intended subtree

                    if len(potential_ports) == 0:
                        print "we're done for"
                        sys.exit() 
                    print "Here are the potential ports to send out of " + str(potential_ports)
                    print "Remember, don't send to the previous switch " + str(prev_switch)
                    while True:
                        port = random.sample(potential_ports, 1)[0]
                        next_switch = spm[(curr_switch, port)]
                        if next_switch != prev_switch:
                            break
                else: #we can just route to the intended switch no problems
                    next_switch = k

            elif len(valid_neighbors) == 0:
                print "no valid neighbors, why is this a thing"
                
            else:
                print "is this supposed to happen? more than 1 valid neighbor... just route down by default"
                lower_level = [spm[(curr_switch, i)] for i in range(1, n_ports / 2 + 1) if spm[(curr_switch, i)] not in failed_switches \
                                and spm[(curr_switch, i)] != prev_switch and spm[(curr_switch, i)] in valid_neighbors]
                next_switch = random.choice(lower_level)
                
        else: #route down or up depending
            print "At level " + str(lvl) + " and in the route up/down case. Which will we choose???"
            upper_level = [k for k,v in neighbor_ips.items() if level(ip_to_val(v)) == lvl + 1 and k not in failed_switches and k != prev_switch]

            # every parent node is in the failure group (or is in failed switches), so we must route down
            if len(set(upper_level) - failure_group_nodes) == 0:
                print "Looks like we're routing down cuz the failure group is " + str(failure_group_nodes) + " and we can't send to those."
                lower_level = [spm[(curr_switch, i)] for i in range(1, n_ports / 2 + 1) if spm[(curr_switch, i)] not in failed_switches \
                                and spm[(curr_switch, i)] != prev_switch]
                next_switch = random.choice(lower_level)
            else: #regular route up
                print "Looks like we're routing up!!"
                next_switch = random.choice(upper_level)

            # try going up
            # if all up nodes are in a failure group or are dead, then route down to random node that's not broken
            # else, regular route up scheme
        print "At level " + str(lvl) + ", the current switch is " + curr_switch + " and we're routing to the next switch " + next_switch
        print "----------"
        prev_switch = curr_switch
        curr_switch = next_switch
        prev_lvl = lvl
    print "FINAL PATH BETWEEN " + str(i) + " and " + str(j) + " is " + str(path)
    print "---------------------------------------"
    return path



def calculate_paths(topo_map, n_servers, num_switches_to_fail, total_switches, p, L, tp):
    paths = {}

    failed_switches = np.random.choice(topo_map['n_switches'] - 2 * p ** L, size=num_switches_to_fail, replace=False) + 2 * p ** L
    failed_switches = ['s' + str(s) for s in failed_switches] # stringify
    print failed_switches
    for i in range(n_servers):
        for j in range(n_servers):
            if i == j:
                continue
            if tp == 'fat':
                path = find_fat_path(topo_map, i, j, p, L, failed_switches)
            else:
                path = find_ab_path(topo_map, i, j, p, L, failed_switches)
            paths[(i, j)] = len(path)
    print paths
    for x in paths:
        if paths[x] > 5:
            print x
    return paths


# either use AB tree, or regular FatTree
def generate_plot(topo_map, n_servers, k, L, tp, **kwargs):
    results = {}
    p = k / 2
    total_switches = 2 * L * p ** L + p ** L
    original_path_lengths = {}
    for num_switches_to_fail in fail_switches:
        path_lengths = calculate_paths(topo_map, n_servers, num_switches_to_fail, total_switches, p, L, tp)
        if num_switches_to_fail == 0:
            original_path_lengths = path_lengths
            continue
        results[num_switches_to_fail] = Counter()

        # compare each new path and see how much longer each one is
        # results[num_switches_to_fail] stores (num_additional_hops -> num host pairs)
        for k in path_lengths:
            orig_len = original_path_lengths[k]
            results[num_switches_to_fail][path_lengths[k] - orig_len] += 1
        print results



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate F10 tops.")
    parser.add_argument('--n_servers', help='Number of servers this topology uses', default=16)
    parser.add_argument('-k', help='Number of ports per switch', default=4)
    parser.add_argument('-L', help='Number of levels this topology has', default=2)
    parser.add_argument('--pickle', help='Topology pickle output path', default=None)
    args = parser.parse_args()
    ab_topo = generate_ab_topology(n_servers=int(args.n_servers), k=int(args.k), L=int(args.L))
    if args.pickle:
        with open(args.pickle, 'wb') as f:
            pickle.dump(ab_topo, f)

    generate_plot(ab_topo, int(args.n_servers), int(args.k), int(args.L), 'ab')
    # generate fat topology
