#!/usr/bin/env python3

import os
import re
import sys
from graphviz import Digraph

PRODSUPP = '/gem_sw/prod/R3.14.12.8/support'

def extract_deps(app_root_path, type_var='P'):
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
        # list comprehension just because
        if type_var == 'P':
            deps_list = [[d[-2],d[-1]]
                          for l in f.read().split('\n')
                          if re.search(reg_filt, l)
                          for d in [l.split('/')]]
        if type_var == 'W':
            deps_list = [d[-1]
                          for l in f.read().split('\n')
                          if re.search(reg_filt, l)
                          for d in [l.split('/')]]
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
        name_str = 'name: ' + self.name
        if not(self.versions):
            return name_str
        versions = ', '.join(self.versions)
        vers_str = 'Versions: ' + versions
        if not(self.prod_deps.keys()):
            return '\n'.join([name_str, vers_str])
        deps_list = []
        for vers in self.versions:
            deps_head = 'Ver {} dependencies:'.format(vers)
            deps = '\n'.join(['/'.join([d[0] ,d[1]])
                              for d in self.prod_deps[vers]])
            deps_list.append(deps_head + '\n' + deps)
        deps_str = '\n'.join(deps_list)
        return '\n'.join([name_str, vers_str, deps_str])

    def get_versions(self):
        supp_path = '/'.join([PRODSUPP,self.name])
        if not(os.path.isdir(supp_path)):
            raise IOError("Directory " + full_path +" doesn't exist")
        self.versions = os.listdir(supp_path)

    def get_prod_deps(self):
        for vers in self.versions:
            vers_path = '/'.join([PRODSUPP, self.name, vers])
            self.prod_deps[vers] = extract_deps(vers_path, 'P')

if __name__ == '__main__':
    # name = 'tcslib/1-0-23'
    # full_path = PRODSUPP + '/' + name
    # print(extract_deps(full_path))
    supp_name = 'tcslib'
    example = SuppNode(supp_name)
    print(example)
    example.get_versions()
    print(example)
    example.get_prod_deps()
    print(example)

    g = Digraph('TCSlib dependencies', filename='tcslib-deps.gv')
    # g.node(tcslib.name)
    version = example.versions[-1]
    example_name = '/'.join([example.name, version])
    g.node(example_name)
    for d in example.prod_deps[version]:
        node_name = '/'.join([d[0],d[1]])
        # g.node(node_name)
        g.edge(example_name, node_name)
    g.view()



