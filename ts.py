import os
from collections import defaultdict
import networkx as nx

MIN_DEGREE_RANGE = 500
INVALID_NO = 1000.

def get_node_cluster_by_degree_range(G):
	"""
	Returns(defaultdict): A dictionary of (lf, rt) : list which have their degree
	in window represented by it's key[lf, rt].
	"""
	last = -1; deg_dist = defaultdict(list)
	for n, d in G.degree():
		last = max(last, d)
	ranges = [(0, 5), (6, 50), (51, 200), (201, 500), (501, 1000), (1001, last)]
	for x in ranges: deg_dist[x] = list()
	def get(deg, i=0):
		while ranges[i][1] < deg: i += 1
		return i
	for n, d in G.degree(): deg_dist[ranges[get(d)]].append(n)
	# print deg_dist
	return deg_dist

def get_adjacent_node_pairs_with_sign(G, node_cluster):
	"""
	Returns(defaultdict): A dict of list of tuples (n1, n2, sign).
	"""
	adjacent_node_pairs = defaultdict(list)
	# For each group/window get adjacent nodes.
	for group in node_cluster:
		nodes = node_cluster[group]
		adjacent_node_pairs[group] = list()
		for i in range(len(nodes) - 1):
			j = i + 1
			while(j < len(nodes)):
				# check edge details
				a = nodes[i]
				b = nodes[j]
				j += 1
				e = G.get_edge_data(a, b, default='#')
				if e == '#':
					continue
				adjacent_node_pairs[group].append((a, b, e['sign']))
	return adjacent_node_pairs

def get_properties_by_group(G, adjacent_node_pairs_with_sign):
	"""
	Returns(defaultdict): Each key has list of tuples(edge, (p1, p2, p3, p4)) of 
	properties corresponding to each edge in "adjacent_node_pairs_with_sign".
	"""
	def get_properties_from_paths(G, paths):
		"""
		Returns(tuple): (prop_1, prop_2)
		For a path:
		prop_1(signed average length) = sum of signs of edges on the path / path length.
		prop_2(random walk sum) = sum 1 / deg(nodes), for all nodes in the path.
		If no path is found between them then it equals to INVALID_NO.
		"""
		prop_1 = 0.; prop_2 = 0.; count = 0
		for p in paths:
			count += 1
			p1 = 0; p2 = sum(1.0 / d for _, d in G.degree(p))
			for i in xrange(1, len(p)):
				p1 += G.get_edge_data(p[i - 1], p[i])['sign']
			prop_1 += float(p1) / len(p)
			prop_2 += float(p2) / len(p)
		return ((float(prop_1) / count if count > 0 else INVALID_NO), (float(prop_2) / count if count > 0 else INVALID_NO))

	def get_clustering_coeff(G, edge):
		"""
		Returns(tuple): 
		Property 1: Clustering Coefficient of an edge. `list_1` and `list_2` calculated are
		neighbours of the two end-points. cc = (list_1 ^ list_2) / (list_1 U list_2).
		Property 2: Finds all structurally balanced triangles which 
		contain the given edge. 
		"""
		list_1 = G.neighbors(edge[0])
		list_2 = G.neighbors(edge[1])
		set_2 = set(list_2)
		intersection = [val for val in list_1 if val in set_2]
		union = len(set_2.union(set(list_1)))
		prop_1 = float(len(intersection)) / union if union > 0 else INVALID_NO

		balanced_triangles = 0
		for x in intersection:
			e1 = G.get_edge_data(edge[0], x, default='#')
			e2 = G.get_edge_data(edge[1], x, default='#')
			if e1 == '#' or e2 == '#':
				raise Exception("!(~.~)!")
			sm = sum([edge[2], e1['sign'], e2['sign']])
			balanced_triangles += (1 if sm == 3 or sm == -1 else 0)
		
		prop_2 = float(balanced_triangles) / len(intersection) if len(intersection) > 0 else INVALID_NO
		return (prop_1, prop_2)

	properties_by_group = defaultdict(list)	
	for k in adjacent_node_pairs_with_sign:
		properties_by_group[k] = list()
		for edge in adjacent_node_pairs_with_sign[k]:
			G.remove_edge(*edge[:2])
			try:
				paths = nx.all_shortest_paths(G, edge[0], edge[1])			
				(prop_1, prop_2) = get_properties_from_paths(G, paths)
			except:
				(prop_1, prop_2) = (0., 0.)
			(prop_3, prop_4) = get_clustering_coeff(G, edge)
			G.add_edge(*edge[:2], sign = edge[2])
			properties_by_group[k].append(
				(edge, (prop_1, prop_2, prop_3, prop_4))
			)
	return properties_by_group

# read graph
G = nx.read_edgelist('./datasets/soc-sign-Slashdot090221.txt/data',
                     nodetype=int, data=(('sign', int),))
node_cluster_by_degree_range = get_node_cluster_by_degree_range(G)
adjacent_node_pairs_with_sign = get_adjacent_node_pairs_with_sign(G, node_cluster_by_degree_range)
properties_by_group = get_properties_by_group(G, adjacent_node_pairs_with_sign)

# make directory if not exists.
if not os.path.isdir("./out_%s" % (MIN_DEGREE_RANGE,)):
	os.makedirs("./out_%s" % (MIN_DEGREE_RANGE,))

for g in properties_by_group:
	with open("./out_%s/%s-%s_pos.txt" % (MIN_DEGREE_RANGE, g[0], g[1]), "w") as pf:
		with open("./out_%s/%s-%s_neg.txt" % (MIN_DEGREE_RANGE, g[0], g[1]), "w") as nf:
			for e_prop in properties_by_group[g]:
				edge = e_prop[0]; prop = e_prop[1]
				out = "%s\t%s\t%s\t%s\t%s\t%s\n" % (
					str(edge[0]), str(edge[1]), str(prop[0]), str(prop[1]), str(prop[2]), str(prop[3])
				)
				# there is no edge with sign 0. only {-1, 1} are present.
				(pf if edge[2] == 1 else nf).write(out)

exit(0)


# print node_cluster_by_degree_range
# print adjacent_node_pairs_with_sign
# print properties_by_group

