import collections
from collections import defaultdict
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# read graph
G = nx.read_edgelist('./datasets/soc-sign-Slashdot090221.txt/data.s', nodetype=int, data=(('sign', int),))
max_degree = G.number_of_nodes() - 1

# l1 = G.neighbors(0)
# l2 = G.neighbors(7)
# s2 = set(l2)

# print [val for val in l1 if val in s2]
# exit(0)

def get_deg_window_sizes(mx):
	"""
	Returns(list): An array of sizes for each group using an
	exponential function.
	"""
	res = []
	x = 0
	base = 2
	while base ** x < mx:
		res.append(base ** x)
		x += 1
	return res

def get_node_cluster_by_degree_range(G, window_size):
	"""
	Returns(defaultdict): A dictionary of lists which have their degree 
	in window represented by it's key.
	"""
	def get_window(n):
		start = 0
		for i, x in enumerate(window_size):
			if x <= 0:
				raise Exception("size should always be +ve")
			start += x - 1
			if(n <= start):
				return i
			start += 1
		raise Exception("Input exceeds maximum allowed value.")

	node_cluster_by_degree_range = defaultdict(list)
	for n, d in G.degree():
		node_cluster_by_degree_range[get_window(d)].append(n)
	return node_cluster_by_degree_range

def get_window_range(window_sizes, initial = 0):
	"""
	Returns(list): A list of tuples (l, r) indicating a range, both inclusive.
	"""
	window_ranges = []
	for x in window_sizes:
		window_ranges.append((initial, initial + x - 1))
		initial = initial + x
	return window_ranges

def get_adjacent_node_pairs_with_sign(G, node_cluster):
	"""
	Returns(defaultdict): A dict of list of tuples (n1, n2, sign).
	"""
	adjacent_node_pairs = defaultdict(list)
	# For each group/window get adjacent nodes.
	for group in node_cluster:
		nodes = node_cluster[group]
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
	Returns(defaultdict): A tuple of properties corresponding to each
	value in "adjacent_node_pairs_with_sign".
	"""
	def get_properties_from_paths(G, paths):
		"""
		Returns(tuple): (prop_1, prop_2)
		For a path:
		prop_1(signed average length) = sum of signs of edges on the path / path length.
		prop_2(random walk sum) = sum 1 / deg(nodes), for all nodes in the path.
		"""
		prop_1 = 0.
		prop_2 = 0.
		count = 0
		for p in paths:
			count += 1
			p1 = 0
			p2 = sum(1.0 / d for _, d in G.degree(p))
			for i in xrange(1, len(p)):
				p1 += G.get_edge_data(p[i - 1], p[i])['sign']
			prop_1 += float(p1) / len(p)
			prop_2 += float(p2) / len(p)
		return ((float(prop_1) / count if count > 0 else 0.), (float(prop_2) / count if count > 0 else 0.))

	def get_clustering_coeff(G, edge):
		"""
		Returns(tuple): 
		Property 1: Clustering Coefficient of an edge. `list_1` and `list_2` should be
		neighbours of the two end-points. cc = (list_1 ^ list_2) / (list_1 U list_2).
		Property 2: Finds all structurally balanced triangles which 
		contain the given edge. 
		"""
		list_1 = G.neighbors(edge[0])
		list_2 = G.neighbors(edge[1])
		set_2 = set(list_2)
		intersection = [val for val in list_1 if val in set_2]
		union = len(set_2.union(set(list_1)))
		prop_1 = 0. if union == 0 else float(len(intersection)) / union

		balanced_triangles = 0
		for x in intersection:
			e1 = G.get_edge_data(edge[0], x, default='#')
			e2 = G.get_edge_data(edge[1], x, default='#')
			if e1 == '#' or e2 == '#':
				raise Exception("!!!")
			sm = sum([edge[2], e1['sign'], e2['sign']])
			balanced_triangles += (1 if sm == 3 or sm == -1 else 0)
		
		prop_2 = float(balanced_triangles) / len(intersection) if len(intersection) > 0 else 0.
		return (prop_1, prop_2)

	properties_by_group = defaultdict(list)
	for k in adjacent_node_pairs_with_sign:
		for edge in adjacent_node_pairs_with_sign[k]:
			G.remove_edge(*edge[:2])
			try:
				paths = nx.all_shortest_paths(G, edge[0], edge[1])			
				(prop_1, prop_2) = get_properties_from_paths(G, paths)
			except:
				(prop_1, prop_2) = (0., 0.)
			(prop_3, prop_4) = get_clustering_coeff(G, edge)
			G.add_edge(*edge[:2], sign = edge[2])
			properties_by_group[k].append((prop_1, prop_2, prop_3, prop_4))
	return properties_by_group


deg_window_size = get_deg_window_sizes(max_degree)
window_range = get_window_range(deg_window_size)
node_cluster_by_degree_range = get_node_cluster_by_degree_range(G, deg_window_size)
adjacent_node_pairs_with_sign = get_adjacent_node_pairs_with_sign(G, node_cluster_by_degree_range)
properties_by_group = get_properties_by_group(G, adjacent_node_pairs_with_sign)

print adjacent_node_pairs_with_sign
print properties_by_group
