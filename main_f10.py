import argparse
import networkx as nx
import pickle
import random
import sys
from collections import defaultdict, OrderedDict
from itertools import islice
from time import sleep, time


from topology_f10 import generate_topology


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate F10 tops.")
    parser.add_argument('--pickle', help='Topology pickle output path', default=None)
    args = parser.parse_args()
    topo = generate_topology(n_servers=144, k=12, L=2)
    if args.pickle:
        with open(args.pickle, 'wb') as f:
            pickle.dump(topo, f)