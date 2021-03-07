#!/usr/bin/env python3

import os
import supportnode as sn
from supportnode import SuppNode, GemNode, PRODSUPP

class SuppGraph:
    '''
    Class that generates and stores all graphs of supp pkgs dependencies
    '''
    def __init__(self):
        self.scope = 'all'
        self.seed_node = ''
        self.nodes = {}

    def gen_ranked(self):
        '''
        Construct the entire graph and add the tier level for each node
        '''
        for sp in os.listdir(PRODSUPP):
            sp_dir = '/'.join([PRODSUPP,sp])
            for v in os.listdir(sp_dir):
                node = '/'.join([sp,v])
                # Skip to next node if it exists in the list
                if node in self.nodes.keys():
                    continue
                # Generate node
                self.nodes[node] = GemNode(node)
                self.nodes[node].get_prod_deps()
                # If node has no dependencies, skip to next node. This is done
                # in order to catch the Tier 0 nodes
                if not(self.nodes[node].prod_deps):
                    continue
                # If node has dependencies, generate the whole branch
                self._gen_ranked_branch(node)

    def gen_unranked(self):
        '''
        Spawn all nodes without ranking them
        '''
        for sp in os.listdir(PRODSUPP):
            sp_dir = '/'.join([PRODSUPP,sp])
            for v in os.listdir(sp_dir):
                node = '/'.join([sp,v])
                self.nodes[node] = GemNode(node)
                self.nodes[node].get_prod_deps()

    def set_tiers(self, dependant):
        '''
        Set tiers for a branch that ends in the 'dependant' node
        '''
        if not(self.nodes[dependant].prod_deps):
            self.nodes[dependant].tier = 1
            return
        for dep in self.nodes[dependant].prod_deps:
            self._set_tiers(dep)
            dependant_tier = self.nodes[dep].tier + 1
            if self.nodes[dependant].tier < dependant_tier:
                self.nodes[dependant].tier = dependant_tier

    def _gen_ranked_branch(self, dependant):
        '''
        Internal recursive method that generates a graph branch starting with
        'dependant', setting the tier for each node as it's generated
        '''
        # Generate node and its dependencies
        self.nodes[dependant] = GemNode(dependant)
        self.nodes[dependant].get_prod_deps()
        # If no dependencies, set tier level to 1 and start unwinding recursion
        if not(self.nodes[dependant].prod_deps):
            self.nodes[dependant].tier = 1
            return
        # Loop that traverses all dependecies
        for dep in self.nodes[dependant].prod_deps:
            # Start traveling down until level 1 node is reached
            self._gen_ranked_branch(dep)
            # Returning here means a Tier 1 node was reached. Calculate new
            # dependant node tier level
            dependant_tier = self.nodes[dep].tier + 1
            # Assign new tier level only if higher than current level
            if self.nodes[dependant].tier < dependant_tier:
                self.nodes[dependant].tier = dependant_tier

    def print_nodes(self):
        '''
        Print all nodes in the graph
        '''
        for n in self.nodes:
            print(self.nodes[n])

if __name__ == '__main__':
    graph = SuppGraph()

    # # Test generating things step by step
    # graph.spawn_all_nodes()
    # graph.set_tiers('astlib/1-6-18')
    # graph.set_tiers('tcslib/1-0-23')

    # Test generating graph and tiers all at once
    graph.gen_ranked()

    graph.print_nodes()
    # graph.tier_sorter()
    # for n in graph.nodes:
        # print(n.keys())
    # for t in graph.tiers:
        # print('Tier {}:'.format(t))
        # print(graph.tiers[t])

