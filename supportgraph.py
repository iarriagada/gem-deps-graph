#!/usr/bin/env python3

import os
import supportnode as sn
from supportnode import SuppNode, PRODSUPP

class SuppGraph:
    '''
    Class that generates and stores a graph of all supp pkgs dependencies
    '''
    def __init__(self):
        self.scope = 'all'
        self.seed_node = ''
        self.nodes = []
        self.tiers = {}

    def generate_all(self):
        for sp in os.listdir(PRODSUPP):
            supp_pkg = SuppNode(sp)
            supp_pkg.get_versions()
            supp_pkg.get_prod_deps()
            self.nodes.append(supp_pkg.prod_deps)

    def tier_sorter(self):
        self.tiers['0'] = []
        for n in self.nodes:
            for v in n.versions:
                if not(n.prod_deps[v]):
                    self.tiers['0'].append(v)


if __name__ == '__main__':
    graph = SuppGraph()
    graph.generate_all()
    # graph.tier_sorter()
    for n in graph.nodes:
        print(n.keys())
    # for t in graph.tiers:
        # print('Tier {}:'.format(t))
        # print(graph.tiers[t])

