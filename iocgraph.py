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

def sort_rank(diag, graph):
    tiers = {}
    for n in graph.nodes:
        n_tier = graph.nodes[n].tier
        if not(n_tier in tiers.keys()):
            tiers[n_tier] = [graph.nodes[n]]
            continue
        tiers[n_tier].append(graph.nodes[n])

    max_tier = max([t for t in tiers.keys()])

    with diag.subgraph() as sg:
        sg.attr(rank='source')
        for n in tiers[0]:
            sg.node(n.name)
            sg.node_attr.update(style='filled', color=color_gen())
    with diag.subgraph() as sg:
        sg.attr(rank='max')
        sg.node_attr.update(style='filled', color=color_gen())
        for n in tiers[max_tier]:
            sg.node(n.name)
    for t in range(1,max_tier):
        with diag.subgraph() as sg:
            sg.attr(rank='same')
            sg.node_attr.update(style='filled', color=color_gen())
            for n in tiers[t]:
                sg.node(n.name)

    print("assigning styles")
    t_style = assign_style(edge_style, max_tier)
    for n in graph.nodes:
        if not(graph.nodes[n].tier):
            continue
        for d in graph.nodes[n].prod_deps:
            diag.edge(d, n, style=t_style[graph.nodes[d].tier])
    # aux_style = []
    # for t in tiers:
        # if not(aux_style):
            # aux_style = edge_style[:]
        # tier_style = random.choice(aux_style)
        # aux_style.remove(tier_style)
        # for n in tiers[t]:
            # for d in n.prod_deps:
                # diag.edge(d, n.name, style=tier_style)

    return diag

def sort_noioc_rank(diag, graph):
    tiers = {}
    for n in graph.nodes:
        n_tier = graph.nodes[n].tier
        if not(n_tier in tiers.keys()):
            tiers[n_tier] = [graph.nodes[n]]
            continue
        tiers[n_tier].append(graph.nodes[n])

    max_tier = max([t for t in tiers.keys()])

    with diag.subgraph() as sg:
        sg.attr(rank='source')
        for n in tiers[0]:
            sg.node(n.name)
            sg.node_attr.update(shape='box', style='rounded, filled',
                                fontname='consolas', fontsize='10',
                                color=color_gen())
    for t in range(1,max_tier+1):
        with diag.subgraph() as sg:
            sg.attr(rank='same')
            sg.node_attr.update(shape='box', style='rounded, filled',
                                fontname='consolas', fontsize='10',
                                color=color_gen())
            for n in tiers[t]:
                sg.node(n.name)

    print("assigning styles")
    t_style = assign_style(edge_style, max_tier)
    for n in graph.nodes:
        if not(graph.nodes[n].tier):
            continue
        for d in graph.nodes[n].prod_deps:
            diag.edge(d, n, style=t_style[graph.nodes[d].tier])


    return diag

if __name__ == '__main__':
    sys_name = 'ag/1-13'
    # sys_name = 'tcs/lst_bug'
    ioc_diag = graphviz.Digraph(filename='ioc_graph.gv', format='svg')
    ioc_graph = SuppGraph()
    # ioc_graph.gen_ioc_diag('tcs/lst_bug')
    # ioc_graph.gen_ioc_diag('ecs/1-0-3')
    # ioc_graph.gen_ioc_diag('mcs/cp')
    ioc_graph.gen_ioc_diag(sys_name)
    # ioc_graph.gen_ioc_ranked('tcs/lst_bug')
    # ioc_graph.gen_ioc_ranked('ecs/1-0-3')
    # ioc_graph.gen_ioc_ranked('ag/1-13')
    ioc_graph.print_nodes()
    # ioc_diag = sort_rank(ioc_diag, ioc_graph)
    ioc_diag = sort_noioc_rank(ioc_diag, ioc_graph)
    ioc_diag.attr(label='Dependencies for {}'.format(sys_name), fontsize='18')
    ioc_diag.attr(ranksep='1.0')
    ioc_diag.view()
