import os
from collections import defaultdict
import networkx as nx
import util

# read graph
print 1
G = nx.read_edgelist('./datasets/soc-sign-epinions.txt/data',
                     nodetype=int, data=(('sign', int),))
last = -1
for n, d in G.degree():
	last = max(last, d)
ranges = [(0, 5), (6, 50), (51, 200), (201, 500), (501, 1000), (1001, last)]
print 2 
adjacent_node_pairs_with_sign = util.get_inter_group_adjacent_node_pairs_with_sign(G, ranges)
print 3
properties_by_group = util.get_properties_by_group(G, adjacent_node_pairs_with_sign, ranges)
print 4

# make directory if not exists.
if not os.path.isdir("./out"): os.makedirs("./out")

f = dict()
for e_prop in properties_by_group[0]:
	edge = e_prop[0]
	prop = e_prop[1]
	sign = edge[2]
	g1 = util.get_range_index(G.degree(edge[0]), ranges)
	g2 = util.get_range_index(G.degree(edge[1]), ranges)
	if g1 > g2: g1, g2 = g2, g1
	tmp = "pos" if sign == 1 else "neg"
	if not f.has_key((g1, g2, sign)): f[(g1, g2, sign)] = open('./out/%s-%s-%s' % (g1, g2, tmp), 'w')
	out = "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
		str(edge[0]), str(edge[1]), str(prop[0]), str(prop[1]), 
		str(prop[2]), str(prop[3]), str(prop[4])
	)
	f[(g1, g2, sign)].write(out)
print 5
