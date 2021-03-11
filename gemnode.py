#!/usr/bin/env python3

import os
import re
import sys
import ade.versions as pgadev

EPICS_PROD_TOP = '/gem_sw/prod/R3.14.12.8'
EPICS_WORK_TOP = '/gem_sw/work/R3.14.12.8'
PRODSUPP = '/'.join([EPICS_PROD_TOP, 'support'])
PRODIOC = '/'.join([EPICS_PROD_TOP, 'ioc'])
WORKIOC = '/'.join([EPICS_WORK_TOP, 'ioc'])

def get_deps(release_lines):
    pass

def get_deps_dir(app_root_path, type_var='(P|S)'):
    '''
    Extract dependencies list from configure/RELEASE file
    '''
    # master regex to capture only the supp package macro definitions
    reg_filt = r'^[^#]*[A-Z0-9]+ *= *\$\({0}'.format(type_var)
    # print(reg_filt)
    full_path = app_root_path+'/configure'
    if not(os.path.isdir(full_path)):
        raise IOError("Directory " + full_path +" doesn't exist")
    with open(full_path+'/RELEASE', 'r') as f:
        # list comprehension just because, catch only the lines that match the
        # regex
        deps_list = [l.split(')/')[1]
                     for l in f.read().split('\n')
                     if re.search(reg_filt, l)]
    return deps_list

class SuppNode:
    '''
    Class used to store attributes of a "support module" type node
    '''

    def __init__(self, name):
        self.name = name
        self.prod_vers = ''
        self.versions = []
        self.prod_deps = {}
        self.work_deps = {}

    def __str__(self):
        '''
        :return: string representation of SuppNode object
        '''
        name_str = '===== name: {} ====='.format(self.name)
        if not(self.versions):
            return name_str
        versions = ', '.join(self.versions)
        vers_str = 'Versions: ' + versions
        if not(self.prod_deps.keys()):
            return '\n'.join([name_str, vers_str])
        deps_list = []
        for vers in self.versions:
            deps_head = 'Ver {} dependencies:'.format(vers)
            deps = '\n'.join(self.prod_deps[vers])
            deps_list.append(deps_head + '\n' + deps)
        deps_str = '\n'.join(deps_list)
        return '\n'.join([name_str, vers_str, deps_str])

    def get_versions(self):
        '''
        Get all the versions of the node
        '''
        supp_path = '/'.join([PRODSUPP,self.name])
        if not(os.path.isdir(supp_path)):
            raise IOError("Directory " + full_path +" doesn't exist")
        self.versions = ['/'.join([self.name,v])
                         for v in os.listdir(supp_path)]

    def get_prod_deps(self):
        '''
        Get the dependecies for each version
        '''
        for vers in self.versions:
            vers_path = '/'.join([PRODSUPP, vers])
            self.prod_deps[vers] = get_deps_dir(vers_path, '(P|S)')

class GemNode:
    '''
    Class used to store attributes of a "<epics-app>/<version>" type node
    '''

    def __init__(self, name):
        self.name = name
        self.prod_deps = []
        self.tier = 0 # By default all nodes are tier 0

    def __str__(self):
        '''
        :return: string representation of SuppNode object
        '''
        name_str = '===== Node: {} ====='.format(self.name)
        tier_str = 'Node Tier Level: {}'.format(self.tier)
        if not(self.prod_deps):
            return '\n'.join([name_str, tier_str])
        deps_head = 'Node dependencies:'
        deps = '\n'.join(self.prod_deps)
        deps_str = '\n'.join([deps_head,deps])
        return '\n'.join([name_str, tier_str, deps_str])

    def get_prod_deps(self, node_root):
        '''
        Get the list of dependencies for the node
        '''
        node_path = '/'.join([node_root, self.name])
        self.prod_deps = get_deps_dir(node_path, '(P|S)')

if __name__ == '__main__':
    name = 'busy/1-7-1'
    full_path = PRODSUPP + '/' + name
    print(get_deps_dir(full_path))
    # supp_name = 'tcslib'
    # example = SuppNode(supp_name)
    # print(example)
    # example.get_versions()
    # print(example)
    # example.get_prod_deps()
    # print(example)

    # g = Digraph('TCSlib dependencies', filename='tcslib-deps.gv')
    # # g.node(tcslib.name)
    # version_name = example.versions[-1]
    # g.node(version_name)
    # for d in example.prod_deps[version_name]:
        # g.edge(version_name, d)
    # g.view()



