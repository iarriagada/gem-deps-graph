#!/usr/bin/env python3

import os
import re
import sys
import subprocess as sp
from ade.versions import Macro

EPICS_PROD_TOP = '/gem_sw/prod/R3.14.12.8'
EPICS_WORK_TOP = '/gem_sw/work/R3.14.12.8'
PRODSUPP = EPICS_PROD_TOP + '/support'
# PRODIOC = EPICS_PROD_TOP + '/ioc'
PRODIOC = EPICS_WORK_TOP + '/ioc'
WORKIOC = EPICS_WORK_TOP + '/ioc'

SVN_ROOT = 'http://sbfsvn02/gemini-sw/gem'
SVN_PROD = SVN_ROOT + '/release'
SVN_PRODSUPP = SVN_ROOT + '/release/support'
SVN_PRODIOC = SVN_ROOT + '/release/ioc'
RELEASE_LOC = 'configure/RELEASE'

# Filter to handle commented lines
CMNT_FILT = re.compile(r'^[ ]*[^#]+')

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

def run_svn_cmd(cmd, arg):
    cmd_exec = sp.run([cmd+arg], shell=True,
                     stdout=sp.PIPE, stderr=sp.PIPE,
                     encoding='utf-8')
    # If svn command returns an error, raise OS exception. kinda harsh
    if cmd_exec.stderr:
        raise OSError(cmd_exec.stderr)
    cmd_out = cmd_exec.stdout.split('\n')
    return cmd_out

class GemNode:
    '''
    Class used to store attributes of a "<epics-app>/<version>" type node
    '''

    def __init__(self, name, app_type='support'):
        self.name = name
        self.app_type = app_type
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
        return

    def get_deps(self, source='svn'):
        '''
        Get the list of dependencies from 'source'.
        '''
        app_root = '/'.join([self.app_type, self.name])
        if source == 'svn':
            release_file = self._get_svn_rel(app_root)
        else:
            release_file = self._get_loc_rel(app_root)
        self.prod_deps = self._extract_deps(release_file)
        return

    @staticmethod
    def _get_svn_rel(app_loc):
        '''
        Generate an array with the contents of configure/RELEASE, via SVN
        '''
        # Generate svn command to read RELEASE file
        svn_ref = '/'.join([SVN_PROD, app_loc, RELEASE_LOC])
        svn_cmd = 'svn cat '
        rel_raw = run_svn_cmd(svn_cmd, svn_ref)
        rel_lines = [l for l in rel_raw if CMNT_FILT.search(l)]
        return rel_lines

    @staticmethod
    def _get_loc_rel(app_loc):
        '''
        Generate an array with the contents of configure/RELEASE, from local
        production directory
        '''
        app_path = '/'.join([EPICS_PROD_TOP, app_loc])
        if not(os.path.isdir(app_path)):
            raise OSError("Directory " + app_path +" doesn't exist")
        rel_file = '/'.join([app_path, RELEASE_LOC])
        with open(rel_file, 'r') as f:
            rel_lines = [l.strip('\n')
                         for l in f.readlines() if CMNT_FILT.search(l)]
        return rel_lines

    @staticmethod
    def _extract_deps(release):
        '''
        Extract dependencies list from configure/RELEASE file
        '''
        # Using master P.Gigoux RELEASE file macro handler
        macro_handler = Macro()
        proc_rel = [macro_handler.process_line(l) for l in release]
        # Filter lines that contain 'support/' as part of the path, and extract
        # the dependency to the right
        deps_list = [r.split('support/')[1]
                        for l,r in proc_rel if len(r.split('support/')) > 1]
        return deps_list

    @staticmethod
    def list_supp(dir_name, source='svn'):
        if source == 'svn':
            path = '/'.join([SVN_PROD, dir_name])
            svn_cmd = 'svn list '
            svn_ls = run_svn_cmd(svn_cmd, path)
            return [l.strip('/') for l in svn_ls if l]
        else:
            path = '/'.join([EPICS_PROD_TOP, dir_name])
            os_ls = os.listdir(path)
            return os_ls

if __name__ == '__main__':
    name = 'busy/6-6-6'
    # name = 'busy/1-7-1'
    # name = 'tcs/cp/2-7-1'
    # full_path = PRODSUPP + '/' + name
    # print(extract_deps(full_path))
    example = GemNode(name)
    # example = GemNode(name, 'ioc')
    print(example)
    example.get_deps('svn')
    # example.get_deps('local')
    print(example)
    # example.get_prod_deps()
    # print(example)




