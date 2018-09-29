from collections import defaultdict
import networkx as nx
from conf import GROUP_LIM
from conf import INVALID_NO
from conf import MIN_PATH_LEN

def get_range_index(deg, ranges):
    i = 0
    while ranges[i][1] < deg:
        i += 1
    return i

def get_node_cluster_by_degree_range(G, ranges):
	"""
	Returns(defaultdict): A dictionary of (lf, rt) : list which have their degree
	in window represented by it's key[lf, rt].
	"""
	last = -1; deg_dist = defaultdict(list)
	for n, d in G.degree(): last = max(last, d)
	for x in ranges: deg_dist[x] = list()
	for n, d in G.degree(): deg_dist[ranges[get_range_index(d, ranges)]].append(n)
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


def get_properties_by_group(G, adjacent_node_pairs_with_sign, ranges):
	"""
	Returns(defaultdict): Each key has list of tuples(edge, (p1, p2, p3, p4, p5)) of 
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
		union = set_2.union(set(list_1))
		union_len = len(union)
		prop_1 = float(len(intersection)) / \
                    union_len if union_len > 0 else INVALID_NO

		balanced_triangles = 0
		for x in intersection:
			e1 = G.get_edge_data(edge[0], x, default='#')
			e2 = G.get_edge_data(edge[1], x, default='#')
			if e1 == '#' or e2 == '#':
				raise Exception("!(~.~)!")
			sm = sum([edge[2], e1['sign'], e2['sign']])
			balanced_triangles += (1 if sm == 3 or sm == -1 else 0)

		prop_2 = float(balanced_triangles) / \
                    len(intersection) if len(intersection) > 0 else INVALID_NO
		pos_x = 0
		neg_x = 0
		for x in intersection:
			e1 = G.get_edge_data(edge[0], x)['sign']
			e2 = G.get_edge_data(edge[1], x)['sign']
			if e1 == e2:
				if e1 == 1:
					pos_x += 1
				elif e1 == -1:
					neg_x += 1
		prop_3 = float(pos_x - neg_x) / union_len if union_len > 0 else INVALID_NO
		return (prop_1, prop_2, prop_3)

	count = defaultdict(int)
	properties_by_group = defaultdict(list)
	for k in adjacent_node_pairs_with_sign:
		properties_by_group[k] = list()
		for edge in adjacent_node_pairs_with_sign[k]:
			g1 = get_range_index(G.degree(edge[0]), ranges)
			g2 = get_range_index(G.degree(edge[1]), ranges)
			sign = edge[2]
			if g1 > g2: g1, g2 = g2, g1
			if count[(g1, g2, sign)] > GROUP_LIM: continue
	
			G.remove_edge(*edge[:2])
			try:
				if nx.shortest_path_length(G, edge[0], edge[1]) > MIN_PATH_LEN:
					raise Exception("INVALID_NO")
				paths = nx.all_shortest_paths(G, edge[0], edge[1])
				(prop_1, prop_2) = get_properties_from_paths(G, paths)
			except:
				(prop_1, prop_2) = (INVALID_NO, INVALID_NO)
			(prop_3, prop_4, prop_5) = get_clustering_coeff(G, edge)
			G.add_edge(*edge[:2], sign=sign)
			properties_by_group[k].append(
				(edge, (prop_1, prop_2, prop_3, prop_4, prop_5))
			)
			count[(g1, g2, sign)] += 1
	return properties_by_group


def get_inter_cluster_props(G, node_cluster, ranges):
	"""
	Returns(list): A 2-d list 
	"""
	inter_cluster_props = list()
	for i in xrange(len(ranges)):
		res = list()	
		for node in node_cluster[ranges[i]]:
			prop = [node, G.degree(node)]
			prop = prop + list([0] * len(ranges))
			for x in G.neighbors(node):
				prop[get_range_index(G.degree(x), ranges) + 2] += 1
			res.append(prop)
		inter_cluster_props.append(res)
	return inter_cluster_props


def get_inter_group_adjacent_node_pairs_with_sign(G, ranges):
	"""
	Returns(defaultdict): A dict of list of tuples (n1, n2, sign).
	"""
	edges_with_sign = list()
	for e in G.edges(data=True):
		g1 = get_range_index(G.degree(e[0]), ranges); g2 = get_range_index(G.degree(e[1]), ranges)
		if g1 == g2: continue
		if g1 > g2: g1, g2 = g2, g1
		edges_with_sign.append((e[0], e[1], e[2]['sign']))
	res = defaultdict(list)
	res[0] = edges_with_sign
	return res
