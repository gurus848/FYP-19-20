import plotly.graph_objects as go
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from .models import ExtractedRelation, Source
import pandas as pd
import os
import sys
proj_path = os.path.abspath(os.path.dirname(__file__)).split("FewRel")[0]
sys.path.insert(1, proj_path + 'src/modelling/')
import soc_net
# visualization related stuff will be done in this file

class VizualizationManager:
    @staticmethod
    def construct_nx_graph(request, dataset_type):
        """
            Constructs a networkx multigraph from the data and returns it
        """
        unique_ents = set()
        edges = []
        rels = set()
        if dataset_type == "db":
            source_objs = Source.objects.filter(user=request.user)
            objs = []
            for s in source_objs:
                objs.extend(ExtractedRelation.objects.filter(source=s))
            for obj in objs:
                if obj.pred_relation == 'NA':  #ignore NA relations
                    continue
                unique_ents.add(obj.head)
                unique_ents.add(obj.tail)
                edges.append((obj.head, obj.tail, obj.pred_relation))
                rels.add(obj.pred_relation)
        elif dataset_type == "uploaded":
            df = pd.read_csv("temp/sna_viz/sna_viz_dataset.csv")
            for i, row in df.iterrows():
                if row['Predicted Relation'] == 'NA':  #ignore NA relations
                    continue
                unique_ents.add(row['Head'])
                unique_ents.add(row['Tail'])
                edges.append((row['Head'], row['Tail'], row['Predicted Relation']))
                rels.add(row['Predicted Relation'])
        elif dataset_type == "specific_timestamp":
            source_id = request.POST.get('source_id')

            objs = ExtractedRelation.objects.filter(source=source_id)
            for obj in objs:
                if obj.pred_relation == 'NA':  #ignore NA relations
                    continue
                unique_ents.add(obj.head)
                unique_ents.add(obj.tail)
                edges.append((obj.head, obj.tail, obj.pred_relation))
                rels.add(obj.pred_relation)
        
        rels = list(rels)
        
        G = nx.MultiGraph()

        for i in unique_ents:
            G.add_node(i, node_type='Entity')

        for e in edges:
            G.add_edge(e[0], e[1], typ=e[2])
            
        return G
    
    @staticmethod
    def make_node_link(request, dataset_type):
        """
            Constructs a node link graph as a html file using plotly and the info in the database.
        """
        
        G = VizualizationManager.construct_nx_graph(request, dataset_type)

        pos = graphviz_layout(G, prog='neato')   
        traces = []
        colors = ['deeppink', 'dodgerblue', 'darkturquoise', 'black',
            'darkviolet', 'darkslategrey',
             'deepskyblue',
            'dimgray']

        gleg = set() #to store whether that relation has been added to the legend yet
        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            if edge[2]['typ'] in gleg:
                edge_trace = go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    line=dict(width=1,color=colors[rels.index(edge[2]['typ'])]),
                    hoverinfo='none',
                    mode='lines',
                    legendgroup=edge[2]['typ'],
                    showlegend=False)
            else:
                edge_trace = go.Scatter(
                    x=[x0, x1, None],
                    y=[y0, y1, None],
                    line=dict(width=1,color=colors[rels.index(edge[2]['typ'])]),
                    hoverinfo='none',
                    mode='lines',
                    legendgroup=edge[2]['typ'],
                    name=edge[2]['typ'],
                    showlegend=True)
                gleg.add(edge[2]['typ'])
            traces.append(edge_trace)
        

        entity_nodes = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=False,
                colorscale='YlGnBu',
                color=1,
                size=10,
                line=dict(width=2),
                symbol='circle'),
            name='Entity')


        for node in G.nodes():
            x, y = pos[node]

            entity_nodes['x'] += tuple([x])
            entity_nodes['y'] += tuple([y])
            entity_nodes['text'] += tuple([node])


        traces.append(entity_nodes)

        fig = go.Figure(data=traces,
                     layout=go.Layout(
#                         title='Relationship between different Entities',
#                         titlefont=dict(size=16),
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        fig.write_html("static/node_link_viz.html")
    
    @staticmethod
    def get_SNA_metrics(G):
        """
        """
        pass