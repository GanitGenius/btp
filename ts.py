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
node_cluster_by_degree_range = util.get_node_cluster_by_degree_range(G, ranges)
print 3
adjacent_node_pairs_with_sign = util.get_adjacent_node_pairs_with_sign(G, node_cluster_by_degree_range)
print 4
properties_by_group = util.get_properties_by_group(G, adjacent_node_pairs_with_sign, ranges)
print 5
# inter_cluster_props = util.get_inter_cluster_props(G, node_cluster_by_degree_range, ranges)
# print inter_cluster_props

# for inter-cluster props.
""" # make directory if not exists.
if not os.path.isdir("./props"):
        os.makedirs("./props")

for i, g in enumerate(inter_cluster_props):
        with open("./props/grp_%s-%s" % (ranges[i][0], ranges[i][1]), "w") as f:
                for node_props in g:
                        node = node_props[0]; deg = node_props[1]
                        f.write('%s\t%s\t' % (str(node), str(deg)))
                        for j in xrange(2, len(node_props)):
                                f.write('%s\t' % str(float(node_props[j]) / deg))
                        f.write('\n')

exit(0)
 """# make directory if not exists.

# for intra-cluster props.
if not os.path.isdir("./out"):
        os.makedirs("./out")

for g in properties_by_group:
        with open("./out/%s-%s_pos.txt" % (g[0], g[1]), "w") as pf:
                with open("./out/%s-%s_neg.txt" % (g[0], g[1]), "w") as nf:
                        for e_prop in properties_by_group[g]:
                                edge = e_prop[0]
                                prop = e_prop[1]
                                out = "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                                        str(edge[0]), str(edge[1]), str(prop[0]), str(prop[1]), 
                                        str(prop[2]), str(prop[3]), str(prop[4])
                                )
                                # there is no edge with sign 0. only {-1, 1} are present.
                                (pf if edge[2] == 1 else nf).write(out)
print 6


# print node_cluster_by_degree_range
# print adjacent_node_pairs_with_sign
# print properties_by_group
