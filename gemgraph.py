#!/usr/bin/env python3

import sys
import threading
import time
from gemnode import GemNode

def progress_mon(dep_nds, gen_nds, name, run_flag):
    '''
    Function to monitor graph generation progress
    '''
    print('Generating nodes for {} from SVN'.format(name))
    # Lambda to generate the progress bar. The '\r' character prints the
    # message overriding the same line
    mess = lambda x,y: '\rFetching dependencies ({1:2d}/{0:2d})'.format(x,y)
    acc_dps = lambda x,y,z: len(set(x[z].prod_deps) & set(y.keys()))
    tot_dps = lambda x,y: len(x[y].prod_deps)
    while run_flag[0]:
        sys.stdout.write(mess(tot_dps(dep_nds, name),
                              acc_dps(dep_nds, gen_nds, name)))
        time.sleep(0.001)
    sys.stdout.write(mess(tot_dps(dep_nds, name),
                          acc_dps(dep_nds, gen_nds, name)))
    sys.stdout.write('\nDone!\n')
    # Set the flag to True in order for the main thread to continue
    # (Since getting the info from svn is so slow, I don't mind adding 1 ms to
    # the whole process)
    run_flag[0] = True

def supp_prog_mon(name, run_flag):
    '''
    Function that shows a progress icon for impacient users
    '''
    prog_icon = ['\\', '|', '/', '-']
    i = 0
    print('Generating node {} from SVN'.format(name))
    while run_flag[0]:
        i %= 4
        sys.stdout.write('\rExtracting node dependencies [{}]'.format(prog_icon[i]))
        i += 1
        time.sleep(0.05)
    sys.stdout.write('\nDone!\n')
    run_flag[0] = True

class GemGraph:
    '''
    Class that generates and stores all graphs of supp pkgs dependencies
    '''
    def __init__(self, rel_src='svn'):
        self.dep_nodes = {}
        self.src_nodes = {}
        self.rel_src = rel_src

    def gen_all_graph(self):
        '''
        Construct the entire graph and add the tier level for each node
        '''
        for sp in GemNode.list_supp('support', self.rel_src):
            sp_dir = '/'.join(['support', sp])
            for v in GemNode.list_supp(sp_dir, self.rel_src):
                node = '/'.join([sp,v])
                # Skip to next node if it exists in the list
                if node in self.dep_nodes.keys():
                    continue
                # Generate node
                self.dep_nodes[node] = GemNode(node)
                self.dep_nodes[node].get_deps(self.rel_src)
                # If node has no dependencies, skip to next node. This is done
                # in order to catch the Tier 0 nodes
                if not(self.dep_nodes[node].prod_deps):
                    continue
                # If node has dependencies, generate the whole branch
                self._gen_branches(node)
        return

    def gen_branch_graph(self, ioc_name, app_type='ioc'):
        '''
        Generate interdependency graph for the support packages of an ioc
        '''
        self.src_nodes[ioc_name] = GemNode(ioc_name, app_type)
        self.src_nodes[ioc_name].get_deps(self.rel_src)
        if not(self.src_nodes[ioc_name].prod_deps):
            raise UserWarning('IOC has no dependencies... kinda sus')
        # Since getting the info from svn is so slow, I added a progress bar.
        # The following are variables initilized for the progress bar
        start = [True]
        # The progress bar only shows up when the source is svn.
        if self.rel_src == 'svn':
            threading.Thread(target=progress_mon,
                             kwargs={'dep_nds':self.src_nodes,
                                     'gen_nds':self.dep_nodes,
                                     'name':ioc_name,
                                     'run_flag':start}).start()
        # Generate the branch for each dependecy
        for ioc_d in self.src_nodes[ioc_name].prod_deps:
            if not(ioc_d in self.dep_nodes.keys()):
                self.dep_nodes[ioc_d] = GemNode(ioc_d)
                self.dep_nodes[ioc_d].get_deps(self.rel_src)
            if not(self.dep_nodes[ioc_d].prod_deps):
                continue
            self._gen_branches(ioc_d)
        # Flag the progress bar to stop
        start[0] = False
        # Wait until Done! is printed on screen to continue
        if self.rel_src == 'svn':
            while not(start[0]):
                time.sleep(0.001)
        # Set tier level of all IOC nodes to be highest supp node tier +1
        max_tier = max([self.dep_nodes[n].tier for n in self.dep_nodes])
        for i in self.src_nodes:
            self.src_nodes[i].tier = max_tier + 1
        return

    def gen_supp_graph(self, supp_name):
        '''
        Generate dependency graph for a support module
        '''
        self.dep_nodes[supp_name] = GemNode(supp_name)
        self.dep_nodes[supp_name].get_deps(self.rel_src)
        start = [True]
        # The progress bar only shows up when the source is svn.
        if self.rel_src == 'svn':
            threading.Thread(target=progress_mon,
                             kwargs={'dep_nds':self.dep_nodes,
                                     'gen_nds':self.dep_nodes,
                                     'name':supp_name,
                                     'run_flag':start}).start()
        self._gen_branches(supp_name)
        start[0] = False
        # Wait until Done! is printed on screen to continue
        if self.rel_src == 'svn':
            while not(start[0]):
                time.sleep(0.001)
        return

    # TODO: Not sure if this method will be used. But you never know
    def gen_all_unranked(self):
        '''
        Spawn all nodes without ranking them
        '''
        for sp in GemNode.list_supp('support', self.source):
            sp_dir = '/'.join(['support', sp])
            for v in GemNode.list_supp(sp_dir, self.source):
                node = '/'.join([sp,v])
                self.dep_nodes[node] = GemNode(node)
                self.dep_nodes[node].get_deps(self.source)
        return

    # TODO: Not sure if this method will be used. But you never know
    def _set_tiers(self, dependant):
        '''
        Set tiers for a branch that ends in the 'dependant' node
        '''
        if not(self.dep_nodes[dependant].prod_deps):
            self.dep_nodes[dependant].tier = 1
            return
        for dep in self.dep_nodes[dependant].prod_deps:
            self._set_tiers(dep)
            dependant_tier = self.dep_nodes[dep].tier + 1
            if self.dep_nodes[dependant].tier < dependant_tier:
                self.dep_nodes[dependant].tier = dependant_tier
        # Checked all dependencies in the loop, unwind
        return

    def _gen_branches(self, dependant):
        '''
        Recursive method that generates a graph branch starting with
        'dependant', setting the tier level for each node as it is generated
        '''
        # If node tier level > 0, it means it has been visited.
        if self.dep_nodes[dependant].tier > 0:
            return
        # If no dependencies, set tier level to 1 and start unwinding recursion
        if not(self.dep_nodes[dependant].prod_deps):
            self.dep_nodes[dependant].tier = 1
            return
        # Loop that traverses all dependecies
        for dep in self.dep_nodes[dependant].prod_deps:
            # If dep node doesn't exist, create it
            if not(dep in self.dep_nodes.keys()):
                self.dep_nodes[dep] = GemNode(dep)
                self.dep_nodes[dep].get_deps(self.rel_src)
            # Start traveling down until level 1 or visited node is reached
            self._gen_branches(dep)
            # Returning here means a Tier 1 node was reached or all
            # dependencies where checked.
            # Calculate new dependant node tier level
            dependant_tier = self.dep_nodes[dep].tier + 1
            # Assign new tier level only if higher than current level
            if self.dep_nodes[dependant].tier < dependant_tier:
                self.dep_nodes[dependant].tier = dependant_tier
        # Checked all dependencies in the loop, unwind
        return

    def print_nodes(self):
        '''
        Print all nodes in the graph
        '''
        if self.src_nodes:
            for ni in self.src_nodes:
                print(self.src_nodes[ni])
        for ns in self.dep_nodes:
            print(self.dep_nodes[ns])
        return

    def print_node(self, node_name):
        '''
        Print single node
        '''
        if node_name in self.src_nodes.keys():
            print(self.src_nodes[node_name])
            return
        print(self.dep_nodes[node_name])
        return

# Main body of the script for testing purposes
if __name__ == '__main__':
    graph = GemGraph()

    # # Test generating things step by step
    # graph.spawn_all_nodes()
    # graph.set_tiers('astlib/1-6-18')
    # graph.set_tiers('tcslib/1-0-23')

    # Test generating graph and tiers all at once
    # graph.gen_ioc_ranked('gis/cwrap-chans')

    # graph.print_nodes()

