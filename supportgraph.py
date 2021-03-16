#!/usr/bin/env python3

import os
import sys
import threading
import time
import subprocess as sp
from gemnode import GemNode, PRODSUPP, PRODIOC, WORKIOC

def progress_mon(tot, acc, name, run_flag):
    '''
    Function to monitor graph generation progress
    '''
    print('Generating for {} from SVN'.format(name))
    # Lambda to generate the progress bar. The '\r' character prints the
    # message overriding the same line
    mess = lambda x, y:'\rFetching dependencies ({1:2d}/{0:2d})'.format(x,y)
    while run_flag[0]:
        sys.stdout.write(mess(tot[0],acc[0]))
        time.sleep(0.001)
    sys.stdout.write(mess(tot[0],acc[0]))
    sys.stdout.write('\nDone!\n')
    # Set the flag to True in order for the main thread to continue
    # (Since getting the info from svn is so slow, I don't mind adding 1 ms to
    # the whole process)
    run_flag[0] = True

class SuppGraph:
    '''
    Class that generates and stores all graphs of supp pkgs dependencies
    '''
    def __init__(self, source='svn'):
        self.supp_nodes = {}
        self.ioc_nodes = {}
        self.source = source

    def gen_all_graph(self):
        '''
        Construct the entire graph and add the tier level for each node
        '''
        # for sp in os.listdir(PRODSUPP):
        for sp in GemNode.list_supp('support', self.source):
            sp_dir = '/'.join(['support', sp])
            for v in GemNode.list_supp(sp_dir, self.source):
                node = '/'.join([sp,v])
                # Skip to next node if it exists in the list
                if node in self.supp_nodes.keys():
                    continue
                # Generate node
                self.supp_nodes[node] = GemNode(node)
                self.supp_nodes[node].get_prod_deps(self.source)
                # If node has no dependencies, skip to next node. This is done
                # in order to catch the Tier 0 nodes
                if not(self.supp_nodes[node].prod_deps):
                    continue
                # If node has dependencies, generate the whole branch
                self._gen_branches(node)
        return

    def gen_ioc_graph(self, ioc_name):
        '''
        Generate interdependency graph for the support packages of an ioc
        '''
        self.ioc_nodes[ioc_name] = GemNode(ioc_name, 'ioc')
        # self.ioc_nodes[ioc_name].get_prod_deps(WORKIOC)
        self.ioc_nodes[ioc_name].get_deps(self.source)
        if not(self.ioc_nodes[ioc_name].prod_deps):
            raise UserWarning('IOC has no dependencies... kinda sus')
        # Since getting the info from svn is so slow, I added a progress bar.
        # The following are variables initilized for the progress bar
        i = [0]
        start = [True]
        nu_deps = [len(self.ioc_nodes[ioc_name].prod_deps)]
        # The progress bar only shows up when the source is svn.
        if self.source == 'svn':
            threading.Thread(target=progress_mon,
                             kwargs={'tot':nu_deps,
                                     'acc':i,
                                     'name':ioc_name,
                                     'run_flag':start}).start()
        # Generate the branch for each dependecy
        for ioc_d in self.ioc_nodes[ioc_name].prod_deps:
            i[0] += 1
            if not(ioc_d in self.supp_nodes.keys()):
                self.supp_nodes[ioc_d] = GemNode(ioc_d)
                self.supp_nodes[ioc_d].get_deps(self.source)
            if not(self.supp_nodes[ioc_d].prod_deps):
                continue
            self._gen_branches(ioc_d)
        # Flag the progress bar to stop
        start[0] = False
        # Wait until Done! is printed on screen to continue
        if self.source == 'svn':
            while not(start[0]):
                time.sleep(0.001)
        # Set tier level of all IOC nodes to be highest supp node tier +1
        max_tier = max([self.supp_nodes[n].tier for n in self.supp_nodes])
        for i in self.ioc_nodes:
            self.ioc_nodes[i].tier = max_tier + 1
        return

    def gen_supp_graph(self, supp_name):
        '''
        Generate dependency graph for a support module
        '''
        self.supp_nodes[supp_name] = GemNode(supp_name)
        self.supp_nodes[supp_name].get_deps(self.source)
        self._gen_branches(supp_name)
        return

    def gen_all_unranked(self):
        '''
        Spawn all nodes without ranking them
        '''
        for sp in GemNode.list_supp('support', self.source):
            sp_dir = '/'.join(['support', sp])
            for v in GemNode.list_supp(sp_dir, self.source):
                node = '/'.join([sp,v])
                self.supp_nodes[node] = GemNode(node)
                self.supp_nodes[node].get_prod_deps(self.source)
        return

    def _set_tiers(self, dependant):
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
        'dependant', setting the tier level for each node as it is generated
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
                self.supp_nodes[dep].get_deps(self.source)
                # self.supp_nodes[dep].get_prod_deps(PRODSUPP)
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
        if self.ioc_nodes:
            for ni in self.ioc_nodes:
                print(self.ioc_nodes[ni])
        for ns in self.supp_nodes:
            print(self.supp_nodes[ns])
        return

    def print_node(self, node_name):
        '''
        Print single node
        '''
        if node_name in self.ioc_nodes.keys():
            print(self.ioc_nodes[node_name])
            return
        print(self.supp_nodes[node_name])
        return

# Main body of the script for testing purposes
if __name__ == '__main__':
    graph = SuppGraph()

    # # Test generating things step by step
    # graph.spawn_all_nodes()
    # graph.set_tiers('astlib/1-6-18')
    # graph.set_tiers('tcslib/1-0-23')

    # Test generating graph and tiers all at once
    # graph.gen_ioc_ranked('gis/cwrap-chans')

    # graph.print_nodes()

