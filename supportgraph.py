#!/usr/bin/env python3

import os
import sys
import subprocess as sp
from gemnode import SuppNode, GemNode, PRODSUPP, PRODIOC, WORKIOC

class SuppGraph:
    '''
    Class that generates and stores all graphs of supp pkgs dependencies
    '''
    def __init__(self, source='local'):
        self.supp_nodes = {}
        self.ioc_nodes = {}
        self.source = source

    def gen_ranked(self):
        '''
        Construct the entire graph and add the tier level for each node
        '''
        for sp in os.listdir(PRODSUPP):
            sp_dir = '/'.join([PRODSUPP,sp])
            for v in os.listdir(sp_dir):
                node = '/'.join([sp,v])
                # Skip to next node if it exists in the list
                if node in self.supp_nodes.keys():
                    continue
                # Generate node
                self.supp_nodes[node] = GemNode(node)
                self.supp_nodes[node].get_prod_deps(PRODSUPP)
                # If node has no dependencies, skip to next node. This is done
                # in order to catch the Tier 0 nodes
                if not(self.supp_nodes[node].prod_deps):
                    continue
                # If node has dependencies, generate the whole branch
                self._gen_branches(node)

    def gen_ioc_ranked(self, ioc_name):
        '''
        Generate graph for a branch spawning from an ioc
        '''
        self.supp_nodes[ioc_name] = GemNode(ioc_name)
        self.supp_nodes[ioc_name].get_prod_deps(WORKIOC)
        if not(self.supp_nodes[ioc_name].prod_deps):
            raise UserWarning('IOC has no dependencies... kinda sus')
        for ioc_d in self.supp_nodes[ioc_name].prod_deps:
            if not(ioc_d in self.supp_nodes.keys()):
                self.supp_nodes[ioc_d] = GemNode(ioc_d)
                self.supp_nodes[ioc_d].get_prod_deps(PRODSUPP)
            if not(self.supp_nodes[ioc_d].prod_deps):
                continue
            self._gen_branches(ioc_d)
        max_tier = max([self.supp_nodes[n].tier for n in self.supp_nodes])
        self.supp_nodes[ioc_name].tier = max_tier + 1

    def gen_ioc_diag(self, ioc_name):
        '''
        Generate interdependency graph for the support packages of an ioc
        '''
        i = 1
        self.ioc_nodes[ioc_name] = GemNode(ioc_name, 'ioc')
        self.ioc_nodes[ioc_name].get_prod_deps(WORKIOC)
        # self.ioc_nodes[ioc_name].get_deps(self.source)
        if not(self.ioc_nodes[ioc_name].prod_deps):
            raise UserWarning('IOC has no dependencies... kinda sus')
        for ioc_d in self.ioc_nodes[ioc_name].prod_deps:
            nu_deps = len(self.ioc_nodes[ioc_name].prod_deps)
            sys.stdout.write('\rGenerating dependency ({1:2d}/{0:2d})'.format(nu_deps, i))
            i += 1
            if not(ioc_d in self.supp_nodes.keys()):
                self.supp_nodes[ioc_d] = GemNode(ioc_d)
                self.supp_nodes[ioc_d].get_deps(self.source)
                # self.supp_nodes[ioc_d].get_prod_deps(PRODSUPP)
            if not(self.supp_nodes[ioc_d].prod_deps):
                continue
            self._gen_branches(ioc_d)
        # sys.stdout.write('\rGenerating dependency({0:2d}/{0:2d}) Done!\n'.format(nu_deps))
        sys.stdout.write('\nDone!\n')
        max_tier = max([self.supp_nodes[n].tier for n in self.supp_nodes])
        for i in self.ioc_nodes:
            self.ioc_nodes[i].tier = max_tier + 1

    def gen_supp_diag(self, supp_name):
        '''
        Generate dependency graph for a support module
        '''
        self.supp_nodes[supp_name] = GemNode(supp_name)
        self.supp_nodes[supp_name].get_deps(self.source)
        self._gen_branches(supp_name)

    def gen_unranked(self):
        '''
        Spawn all nodes without ranking them
        '''
        for sp in os.listdir(PRODSUPP):
            sp_dir = '/'.join([PRODSUPP,sp])
            for v in os.listdir(sp_dir):
                node = '/'.join([sp,v])
                self.supp_nodes[node] = GemNode(node)
                self.supp_nodes[node].get_prod_deps(PRODSUPP)

    def set_tiers(self, dependant):
        '''
        Set tiers for a branch that ends in the 'dependant' node
        '''
        if not(self.supp_nodes[dependant].prod_deps):
            self.supp_nodes[dependant].tier = 1
            return
        for dep in self.supp_nodes[dependant].prod_deps:
            self._set_tiers(dep)
            dependant_tier = self.supp_nodes[dep].tier + 1
            if self.supp_nodes[dependant].tier < dependant_tier:
                self.supp_nodes[dependant].tier = dependant_tier
        # Checked all dependencies in the loop, unwind
        return

    def _gen_branches(self, dependant):
        '''
        Recursive method that generates a graph branch starting with
        'dependant', setting the tier level for each node as it's generated
        '''
        # If node tier level > 0, it means it has been visited.
        if self.supp_nodes[dependant].tier > 0:
            return
        # If no dependencies, set tier level to 1 and start unwinding recursion
        if not(self.supp_nodes[dependant].prod_deps):
            self.supp_nodes[dependant].tier = 1
            return
        # Loop that traverses all dependecies
        for dep in self.supp_nodes[dependant].prod_deps:
            # If dep node doesn't exist, create it
            if not(dep in self.supp_nodes.keys()):
                self.supp_nodes[dep] = GemNode(dep)
                self.supp_nodes[dep].get_prod_deps(PRODSUPP)
            # Start traveling down until level 1 or visited node is reached
            self._gen_branches(dep)
            # Returning here means a Tier 1 node was reached or all
            # dependencies where checked.
            # Calculate new dependant node tier level
            dependant_tier = self.supp_nodes[dep].tier + 1
            # Assign new tier level only if higher than current level
            if self.supp_nodes[dependant].tier < dependant_tier:
                self.supp_nodes[dependant].tier = dependant_tier
        # Checked all dependencies in the loop, unwind
        return

    def print_nodes(self):
        '''
        Print all nodes in the graph
        '''
        for n in self.supp_nodes:
            print(self.supp_nodes[n])

    def print_node(self, node_name):
        '''
        Print single node
        '''
        print(self.supp_nodes[node_name])

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

