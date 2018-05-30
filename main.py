import argparse
import networkx as nx
import pickle
import random
import sys
from collections import defaultdict, OrderedDict
from itertools import islice
from time import sleep, time


from topology import generate_ab_topology

def calculate_paths(topology):
	pass

# either use AB tree, or regular FatTree
def generate_plot(topology, tp, **kwargs):
	if tp == 'fat':
		# do some shit
		pass
	else:
		print kwargs['k']
		# retrieve data from other function


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate F10 tops.")
    parser.add_argument('--n_servers', help='Number of servers this topology uses', default=16)
    parser.add_argument('-k', help='Number of ports per switch', default=4)
    parser.add_argument('-L', help='Number of levels this topology has', default=2)
    parser.add_argument('--pickle', help='Topology pickle output path', default=None)
    args = parser.parse_args()
    ab_topo = generate_ab_topology(n_servers=args.n_servers, k=4, L=2)
    if args.pickle:
        with open(args.pickle, 'wb') as f:
            pickle.dump(ab_topo, f)

    generate_plot(ab_topo, 'ab', k='lit')
    # generate fat topology
