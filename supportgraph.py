#!/usr/bin/env python3

import os
from gemnode import SuppNode, GemNode, PRODSUPP, PRODIOC, WORKIOC

class SuppGraph:
    '''
    Class that generates and stores all graphs of supp pkgs dependencies
    '''
    def __init__(self):
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
                self.nodes[node].get_prod_deps(PRODSUPP)
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
                self.nodes[node].get_prod_deps(PRODSUPP)

    def gen_ioc_ranked(self, ioc_name):
        '''
        Generate graph for a branch spawning from an ioc
        '''
        self.nodes[ioc_name] = GemNode(ioc_name)
        self.nodes[ioc_name].get_prod_deps(WORKIOC)
        if not(self.nodes[ioc_name].prod_deps):
            raise UserWarning('IOC has no dependencies... kinda sus')
        for ioc_d in self.nodes[ioc_name].prod_deps:
            if not(ioc_d in self.nodes.keys()):
                self.nodes[ioc_d] = GemNode(ioc_d)
                self.nodes[ioc_d].get_prod_deps(PRODSUPP)
            if not(self.nodes[ioc_d].prod_deps):
                continue
            self._gen_ranked_branch(ioc_d)
        max_tier = max([self.nodes[n].tier for n in self.nodes])
        self.nodes[ioc_name].tier = max_tier + 1

    def gen_ioc_diag(self, ioc_name):
        '''
        Generate graph for a branch spawning from an ioc
        '''
        ioc_node = GemNode(ioc_name)
        ioc_node.get_prod_deps(WORKIOC)
        if not(ioc_node.prod_deps):
            raise UserWarning('IOC has no dependencies... kinda sus')
        for ioc_d in ioc_node.prod_deps:
            if not(ioc_d in self.nodes.keys()):
                self.nodes[ioc_d] = GemNode(ioc_d)
                self.nodes[ioc_d].get_prod_deps(PRODSUPP)
            if not(self.nodes[ioc_d].prod_deps):
                continue
            self._gen_ranked_branch(ioc_d)

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
        # Checked all dependencies in the loop, unwind
        return

    def _gen_ranked_branch(self, dependant):
        '''
        Internal recursive method that generates a graph branch starting with
        'dependant', setting the tier level for each node as it's generated
        '''
        # If no dependencies, set tier level to 1 and start unwinding recursion
        if not(self.nodes[dependant].prod_deps):
            self.nodes[dependant].tier = 1
            return
        # Loop that traverses all dependecies
        for dep in self.nodes[dependant].prod_deps:
            # If dep node doesn't exist, create it
            if not(dep in self.nodes.keys()):
                self.nodes[dep] = GemNode(dep)
                self.nodes[dep].get_prod_deps(PRODSUPP)
            # If dep node tier level > 0, it means it has been visited.
            # Continue with next dep
            if self.nodes[dep].tier > 0:
                # Calculate new tier level for dependant
                dependant_tier = self.nodes[dep].tier + 1
                # Assign new tier level only if higher than current level
                if self.nodes[dependant].tier < dependant_tier:
                    self.nodes[dependant].tier = dependant_tier
                continue
            # Start traveling down until level 1 or visited node is reached
            self._gen_ranked_branch(dep)
            # Returning here means a Tier 1 node was reached or all
            # dependencies where checked.
            # Calculate new dependant node tier level
            dependant_tier = self.nodes[dep].tier + 1
            # Assign new tier level only if higher than current level
            if self.nodes[dependant].tier < dependant_tier:
                self.nodes[dependant].tier = dependant_tier
        # Checked all dependencies in the loop, unwind
        return

    def print_nodes(self):
        '''
        Print all nodes in the graph
        '''
        for n in self.nodes:
            print(self.nodes[n])

    def print_node(self, node_name):
        '''
        Print single node
        '''
        print(self.nodes[node_name])

if __name__ == '__main__':
    graph = SuppGraph()

    # # Test generating things step by step
    # graph.spawn_all_nodes()
    # graph.set_tiers('astlib/1-6-18')
    # graph.set_tiers('tcslib/1-0-23')

    # Test generating graph and tiers all at once
    # graph.gen_ranked()
    graph.gen_ioc_ranked('gis/cwrap-chans')

    graph.print_nodes()
    # graph.tier_sorter()
    # for n in graph.nodes:
        # print(n.keys())
    # for t in graph.tiers:
        # print('Tier {}:'.format(t))
        # print(graph.tiers[t])

