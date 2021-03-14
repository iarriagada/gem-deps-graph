#!/usr/bin/env python3

import os
import random
import graphviz
from supportgraph import SuppGraph

edge_style = ['solid',
              'dashed',
              'dotted',
              'bold']

def color_gen():
    rn = lambda: random.randint(150,255)
    color = '#{0:02X}{1:02X}{2:02X}'.format(rn(), rn(), rn())
    return color

def assign_style(styles, maxtier):
    tier_style = {}
    styles = []
    for t in range(0, maxtier+1):
        if not(styles):
            styles = edge_style[:]
        tier_style[t] = random.choice(styles)
        styles.remove(tier_style[t])
    return tier_style

class GraphDiagram:
    '''
    Class that handles GraphViz representations of support/ioc dependencies
    graphs.
    '''
    def __init__(self, name, filename, directory='/tmp', source='svn',
                 format='svg', ranksep='1.0', focus='support', shape='box',
                 style='rounded, filled', ndfntname='consolas', ndfntsize='10',
                 label='', lblfntname='consolas', lblfntsize='12'):
        self.name = name
        # self.filename = filename
        # self.directory = directory
        # self.format = format
        self.source = source
        self.ransep = ranksep
        self.focus = focus
        self.node_style = {'shape':shape,
                           'style':style,
                           'fontname':ndfntname,
                           'fontsize':ndfntsize}
        self.label_style = {'fontname':lblfntname,
                            'fontsize':lblfntsize}
        self.diagram = graphviz.Digraph(filename=filename,
                                        directory=directory, format=format)
        self.graph = SuppGraph(self.source)
        self.tiers = {}
        self.seeds = []

    def config_single_branch(self):
        '''
        Method to draw a graph with 2 different focuses, IOC or support pkg
        '''
        # Create dictionary of nodes separated by tiers
        for n in self.graph.supp_nodes:
            n_tier = self.graph.supp_nodes[n].tier
            if not(n_tier in self.tiers.keys()):
                self.tiers[n_tier] = [self.graph.supp_nodes[n]]
                continue
            self.tiers[n_tier].append(self.graph.supp_nodes[n])

        # Get the highest tier value
        max_tier = max(self.tiers.keys())
        # Setup tier 0 section
        with self.diagram.subgraph() as sg:
            sg.attr(rank='source')
            sg.node_attr.update(**self.node_style)
                # Set random color for this section
            sg.node_attr.update(color=color_gen())
            for n in self.tiers[0]:
                sg.node(n.name)
        # Setup IOC tier section
        if self.focus == 'ioc':
            with self.diagram.subgraph() as sg:
                # The rank needs to be set to max in order to work. Don't know
                # why
                sg.attr(rank='max')
                sg.node_attr.update(**self.node_style)
                # Set random color for this section
                sg.node_attr.update(color=color_gen())
                for n in self.graph.ioc_nodes:
                    sg.node(self.graph.ioc_nodes[n].name)
        # Setup mid-tier section
        for t in range(1,max_tier+1):
            with self.diagram.subgraph() as sg:
                sg.attr(rank='same')
                sg.node_attr.update(**self.node_style)
                # Set random color for this section
                sg.node_attr.update(color=color_gen())
                for n in self.tiers[t]:
                    sg.node(n.name)
        # Create edge style dictionary
        t_style = assign_style(edge_style, max_tier+1)
        for n in self.graph.supp_nodes:
            # Don't try to draw edges for Tier 0 nodes
            if not(self.graph.supp_nodes[n].tier):
                continue
            for d in self.graph.supp_nodes[n].prod_deps:
                self.diagram.edge(d, n,
                                  style=\
                                  t_style[self.graph.supp_nodes[d].tier])
        # Draw the IOC nodes (highest tier)
        if self.focus == 'ioc':
            for n in self.graph.ioc_nodes:
                for d in self.graph.ioc_nodes[n].prod_deps:
                    self.diagram.edge(d, n,
                                      style=\
                                      t_style[self.graph.supp_nodes[d].tier])
        return

    def draw_graph(self):
        '''
        Setup general graph diagram attributes, then draw it
        '''
        self.diagram.attr(**self.label_style)
        self.diagram.view()
        return

    def spawn_graph(self, app_list):
        '''
        Spawn graph for all applications in the list
        '''
        for app in app_list:
            self.graph.gen_ioc_graph(app)
        return

def draw_graph(diag, graph, pov='support'):
    tiers = {}
    for n in graph.supp_nodes:
        n_tier = graph.supp_nodes[n].tier
        if not(n_tier in tiers.keys()):
            tiers[n_tier] = [graph.supp_nodes[n]]
            continue
        tiers[n_tier].append(graph.supp_nodes[n])

    max_tier = max([t for t in tiers.keys()])

    with diag.subgraph() as sg:
        sg.attr(rank='source')
        for n in tiers[0]:
            sg.node(n.name)
            sg.node_attr.update(shape='box', style='rounded, filled',
                                fontname='consolas', fontsize='10')
                                # fontname='consolas', fontsize='10',
                                # color=color_gen())
            sg.node_attr.update(color=color_gen())
    if pov == 'ioc':
        with diag.subgraph() as sg:
            sg.attr(rank='max')
            # sg.node_attr.update(style='filled', color=color_gen())
            sg.node_attr.update(shape='box', style='rounded, filled',
                                fontname='consolas', fontsize='10',
                                color=color_gen())
            for n in graph.ioc_nodes:
                sg.node(graph.ioc_nodes[n].name)
    for t in range(1,max_tier+1):
        with diag.subgraph() as sg:
            sg.attr(rank='same')
            sg.node_attr.update(shape='box', style='rounded, filled',
                                fontname='consolas', fontsize='10',
                                color=color_gen())
            for n in tiers[t]:
                sg.node(n.name)

    t_style = assign_style(edge_style, max_tier+1)
    for n in graph.supp_nodes:
        if not(graph.supp_nodes[n].tier):
            continue
        for d in graph.supp_nodes[n].prod_deps:
            diag.edge(d, n, style=t_style[graph.supp_nodes[d].tier])
    if pov == 'ioc':
        for n in graph.ioc_nodes:
            for d in graph.ioc_nodes[n].prod_deps:
                diag.edge(d, n, style=t_style[graph.supp_nodes[d].tier])

    return diag

if __name__ == '__main__':
    # sys_name = 'ag/1-13'
    # sys_name = 'ag/cp/1-13'
    sys_name = 'ag/cp/1-15'
    ioc_graph = GraphDiagram('Dependecies', 'ioc_graph', focus='ioc')
    ioc_graph.spawn_graph([sys_name, 'tcs/cp/2-7-1'])
    ioc_graph.config_single_branch()
    ioc_graph.draw_graph()

    # ioc_diag = graphviz.Digraph(filename='ioc_graph.gv', directory='/tmp', format='svg')
    # ioc_diag.attr(label='Dependencies for {}'.format(sys_name), fontsize='18')
    # ioc_diag.attr(ranksep='1.0')
    # ioc_graph = SuppGraph(source='svn')
    # ioc_graph.gen_ioc_graph(sys_name)
    # # ioc_graph.gen_ioc_graph('tcs/lst_bug')
    # # ioc_graph.gen_ioc_graph('ecs/1-0-3')
    # # ioc_graph.gen_ioc_graph'mcs/cp')
    # # ioc_graph.gen_ioc_graph('ag/cp/1-13')
    # # ioc_graph.print_nodes()
    # # ioc_diag = draw_graph(ioc_diag, ioc_graph, pov='ioc')
    # ioc_diag = draw_graph(ioc_diag, ioc_graph, pov='support')
    # ioc_diag.view()
