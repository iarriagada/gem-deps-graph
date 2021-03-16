#!/usr/bin/env python3

import random
import graphviz
from gemgraph import GemGraph

edge_style = ['solid',
              'dashed',
              'dotted',
              'bold']

def color_gen():
    rn = lambda: random.randint(150,255)
    color = '#{0:02X}{1:02X}{2:02X}'.format(rn(), rn(), rn())
    return color

class GraphDiagram:
    '''
    Class that handles GraphViz representations of support/ioc dependencies
    graphs.
    '''
    def __init__(self, name, filename, directory='/tmp', source='svn',
                 format='svg', ranksep='1.0', focus='deps', shape='box',
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
        self.graph = GemGraph(self.source)
        self.tiers = {}
        self.seeds = []

    def gen_graph_tiers(self, nodes):
        '''
        Method to configure each tier of the graph
        '''
        for n in nodes:
            t = nodes[n].tier
            # Create tier diagram if it doesn't exist
            if not(t in self.tiers.keys()):
                # Start by creating the tier group diagram
                self.tiers[t] = graphviz.Digraph()
                # Set the node styles associated with the tier
                self.tiers[t].node_attr.update(**self.node_style)
                # Set random color for this section
                self.tiers[t].node_attr.update(color=color_gen())
            # Finally assign the node to its tier
            self.tiers[t].node(nodes[n].name)
        # Calculate the max tier and assign hierarchy levels
        max_tier = max(self.tiers.keys())
        for t in self.tiers:
            if t == 0:
                self.tiers[t].attr(rank='source')
            elif t == max_tier:
                self.tiers[t].attr(rank='max')
            else:
                self.tiers[t].attr(rank='same')
            self.diagram.subgraph(self.tiers[t])
        return

    def gen_graph_edges(self, nodes, t_style):
        '''
        Method to configure the edges of the graph
        '''
        for n in nodes:
            for d in nodes[n].prod_deps:
                self.diagram.edge(d, nodes[n].name,
                                    style=t_style[nodes[d].tier])
        return

    def gen_graph_diag(self):
        '''
        Method to generate the dependecies diagram for one EPICS app
        '''
        tot_nodes = self.graph.dep_nodes
        # If the focus of the graph is an ioc, add the corresponding nodes
        if self.focus == 'src':
            tot_nodes.update(self.graph.src_nodes)
        self.gen_graph_tiers(tot_nodes)
        # Generate edge styles
        t_style = self._assign_style(edge_style, max(self.tiers.keys()))
        self.gen_graph_edges(tot_nodes, t_style)
        return

    def draw_graph_diag(self):
        '''
        Setup general graph diagram attributes, then draw it
        '''
        self.diagram.attr(**self.label_style)
        self.diagram.view()
        return

    def spawn_graph(self, *app_list):
        '''
        Spawn graph for all applications in the list
        '''
        for app in app_list:
            if app[1] == 'ioc':
                self.graph.gen_branch_graph(app[0], app[1])
            if app[1] == 'support':
                self.graph.gen_supp_graph(app[0])
        return

    @staticmethod
    def _assign_style(styles, maxtier):
        '''
        Method to calculate the edge style dictionary
        '''
        tier_style = {}
        styles = []
        for t in range(0, maxtier):
            if not(styles):
                styles = edge_style[:]
            tier_style[t] = random.choice(styles)
            styles.remove(tier_style[t])
        return tier_style

if __name__ == '__main__':
    # sys_name = 'ag/1-13'
    # sys_name = 'ag/cp/1-13'
    # sys_name = 'ecs/cp/1-0-3'
    sys_name = 'ag/cp/1-0-1'
    ioc_graph = GraphDiagram('Dependecies', 'dual_graph',
                             directory='.', focus='src', source='svn')
    ioc_graph.spawn_graph([sys_name, 'ioc'], ['tcs/cp/2-7-1', 'ioc'])
    # ioc_graph.spawn_graph(['tcs/cp/2-7-1', 'ioc'])
    # ioc_graph.spawn_graph(['tcslib/1-0-23', 'support'])
    # ioc_graph.config_single_branch()
    # ioc_graph.config_diag()
    ioc_graph.gen_graph_diag()
    ioc_graph.draw_graph_diag()

