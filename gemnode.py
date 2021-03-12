#!/usr/bin/env python3

import os
import re
import sys
from ade.versions import Macro

EPICS_PROD_TOP = '/gem_sw/prod/R3.14.12.8'
EPICS_WORK_TOP = '/gem_sw/work/R3.14.12.8'
PRODSUPP = EPICS_PROD_TOP + '/support'
PRODIOC = EPICS_PROD_TOP + '/ioc'
WORKIOC = EPICS_WORK_TOP + '/ioc'

SVN_ROOT = 'http://sbfsvn02/gemini-sw/gem'
SVN_PRODSUPP = SVN_ROOT + '/release/support'
SVN_PRODIOC = SVN_ROOT + '/release/ioc'
RELEASE_LOC = 'configure/RELEASE'


def extract_deps(app_root_path, type_var='(P|S)'):
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
            self.prod_deps[vers] = extract_deps(vers_path, '(P|S)')

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
        self.prod_deps = extract_deps(node_path, '(P|S)')

    @staticmethod
    def _get_svn_rel(sys_name):
        '''
        Generate an array with the contents of configure/RELEASE, via SVN
        '''

        svn_ref = '/'.join([SVN_PRODSUPP, sys_name, RELEASE_LOC])
        svn_cmd = 'svn cat '
        svn_cat = sp.run([svn_cmd+svn_ref], shell=True,
                         stdout=sp.PIPE, stderr=sp.PIPE,
                         encoding='utf-8')
        if svn_cat.stderr:
            for l in svn_cat.stderr.split('\n')
            print(l)
            sys.exit()
        rel_raw = svn_cat.stdout.split('\n')
        rel_lines = [l for l in rel_raw if m.search(l)]
        return rel_lines

    def _get_loc_rel(sys_name):
        # TODO: Get this from local directories
        pass

    @staticmethod
    def extract_deps(release):
        '''
        Extract dependencies list from configure/RELEASE file
        '''
        filt = re.compile(r'^[ ]*[^#]+')

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

if __name__ == '__main__':
    name = 'busy/1-7-1'
    full_path = PRODSUPP + '/' + name
    print(extract_deps(full_path))
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



