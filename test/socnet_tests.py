import unittest
import numpy as np
import networkx as nx

import sys
sys.path.append("../")
from src.modelling.soc_net import *

class SocNetTest(unittest.TestCase):
    """All tests for the soc_net module."""

    def testConnectednessReport(self):
        """Test that the connectedness report outputs correctly: is_connected boolean and the connected components."""
        # report connectedness for fully connected Karate Club graph
        G = nx.karate_club_graph()
        is_connected, comps = report_connectedness(G)
        self.assertTrue(is_connected)
        self.assertTrue(len(list(comps)) == 1)
        
        # report connectedness for random disconnected Karate Club graph
        G = nx.Graph()
        G.add_edges_from([(1, 2), (1, 3), (4, 3), (5, 6), (6, 7)]) # sample disconnected graph
        is_connected, comps = report_connectedness(G)
        self.assertFalse(is_connected)
        self.assertTrue(len(list(comps)) == 2)

        
    def testTopNodes(self):
        """Test that the top nodes are generated correctly for each centrality measure."""
        G = nx.karate_club_graph()
        
        # top nodes for the Karate Club Graph
        top_def_nodes = {'degree': (33, 0, 32), 'betweenness': (0, 33, 32), 'closeness': (0, 2, 33)}
        
        top_5_nodes = {'degree': (33, 0, 32, 2, 1), 
                       'betweenness': (0, 33, 32, 2, 31), 
                       'closeness': (0, 2, 33, 31, 8)}
        
        top_all_nodes = dict()
        top_all_nodes['degree'] = (33, 0, 32, 2, 1, 3, 31, 8, 13, 23, 5, 6, 7, 27, 29, 30, 
                                   4, 10, 19, 24, 25, 28, 9, 12, 14, 15, 16, 17, 18, 20, 21, 22, 26, 11)
        
        top_all_nodes['betweenness'] = (0, 33, 32, 2, 31, 8, 1, 13, 19, 5, 6, 27, 23, 30, 3, 25, 29, 
                                        24, 28, 9, 4, 10, 7, 11, 12, 14, 15, 16, 17, 18, 20, 21, 22, 26)
        
        top_all_nodes['closeness'] = (0, 2, 33, 31, 8, 13, 32, 19, 1, 3, 27, 30, 28, 7, 9, 23, 5, 6, 29, 4, 
                                      10, 17, 21, 24, 25, 12, 14, 15, 18, 20, 22, 11, 26, 16)
        
        # test top_nodes which outputs top 3 by default
        res_dict = top_nodes(G)
        self.assertDictEqual(top_def_nodes, res_dict)
        
        # test top 5 nodes
        res_dict = top_nodes(G, k=5)
        self.assertDictEqual(top_5_nodes, res_dict)
        
        # test all top nodes
        res_dict = top_nodes(G, k=-1)
        self.assertTrue(all([top_all_nodes[k] == res_dict[k] for k in top_all_nodes.keys()]))

        
    def testTopEdges(self):
        """Test that the top edges are generated correctly."""
        G = nx.karate_club_graph()

        # top nodes for the Karate Club Graph
        top_def_edges = {'edge_betweeness': ((0, 31), (0, 6), (0, 5))}
        top_5_edges = {'edge_betweeness': ((0, 31), (0, 6), (0, 5), (0, 2), (0, 8))}
        
        top_all_edges = {'edge_betweeness': ((0, 31), (0, 6), (0, 5), (0, 2), (0, 8), (2, 32), (13, 33), (19, 33), 
                                             (0, 11), (26, 33), (31, 33), (0, 4), (0, 10), (0, 12), (0, 19), (0, 13), 
                                             (25, 31), (31, 32), (2, 27), (8, 33), (0, 17), (0, 21), (24, 31), (14, 33), 
                                             (15, 33), (18, 33), (20, 33), (22, 33), (23, 33), (1, 30), (2, 9), (27, 33),
                                             (8, 32), (29, 33), (9, 33), (5, 16), (6, 16), (30, 33), (0, 1), (2, 7), 
                                             (28, 33), (14, 32), (15, 32), (18, 32), (20, 32), (22, 32), (29, 32), (1, 2), 
                                             (0, 7), (2, 28), (2, 3), (23, 32), (0, 3), (23, 25), (1, 17), (1, 21), (24, 27), 
                                             (30, 32), (3, 13), (28, 31), (1, 19), (1, 13), (3, 12), (23, 27), (8, 30), 
                                             (2, 8), (32, 33), (1, 3), (2, 13), (1, 7), (23, 29), (4, 6), (5, 10), 
                                             (26, 29), (24, 25), (3, 7), (5, 6), (4, 10))}

        # test top_edges which outputs top 3 by default
        res_dict = top_edges(G)
        self.assertDictEqual(top_def_edges, res_dict)
        
        # test top_edges which outputs top 5 edges
        res_dict = top_edges(G, k=5)
        self.assertDictEqual(top_5_edges, res_dict)
        
        # test top_edges which outputs all edges
        res_dict = top_edges(G, k=-1)
        self.assertDictEqual(top_all_edges, res_dict)
        
    
    def testNodeSumms(self):
        """test that the node summaries are generated and output correctly."""
        # add random relation types to the Karate Club graph 
        G = nx.karate_club_graph()
        rel_types = ['work_together', 'contact', 'oppose', 'like', 'part_of']
        np.random.seed(2020)
        relations = [(u, v, rel_types[np.random.randint(0, 5)]) for (u, v) in G.edges]
        relG = nx.Graph()
        [relG.add_edge(u, v, relation=r) for u, v, r in relations]
        
        # generate summaries
        summs = summarise_nodes(relG)
        
        # test
        summary_for_node_1 = "degree: 9\n"
        summary_for_node_1 += "Relations: \n"
        summary_for_node_1 += "'work_together' (3) - 0, 2, 13\n"
        summary_for_node_1 += "'part_of' (3) - 3, 7, 17\n"
        summary_for_node_1 += "'contact' (2) - 19, 21\n"
        summary_for_node_1 += "'oppose' (1) - 30\n"
        
        self.assertTrue(len(summs) == len(G.nodes))
        self.assertTrue(summary_for_node_1 == summs[1])

        
    def testCommSumms(self):
        """test that the community summaries are generated and output correctly."""
        G = nx.karate_club_graph()
        rel_types = ['work_together', 'contact', 'oppose', 'like', 'part_of']
        np.random.seed(2020)
        relations = [(u, v, rel_types[np.random.randint(0, 5)]) for (u, v) in G.edges]
        relG = nx.Graph()
        [relG.add_edge(u, v, relation=r) for u, v, r in relations]
        
        # generate summaries
        summs = summarise_communities(relG)
        
        #test
        summary_for_comm_1 = "Bridge: 33\n"
        summary_for_comm_1 += "Members: 8, 14, 15, 18, 20, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33\n"
        summary_for_comm_1 += "Closeness: 0.5505\n"
        summary_for_comm_1 += "Relations:\n"
        summary_for_comm_1 += "'contact'- 8\n"
        summary_for_comm_1 += "'like'- 8\n"
        summary_for_comm_1 += "'oppose'- 6\n"
        summary_for_comm_1 += "'part_of'- 3\n"
        summary_for_comm_1 += "'work_together'- 9"
       
        self.assertTrue(len(summs) == 3) # there must be 3 clusters
        self.assertTrue(summs[0] == summary_for_comm_1)
        
        