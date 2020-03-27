import plotly.graph_objects as go
from networkx.drawing.nx_agraph import graphviz_layout
import networkx as nx
from .models import ExtractedRelation, Source
# visualization related stuff will be done in this file

class VizualizationManager:
    @staticmethod
    def make_node_link(request):
        """
            Constructs a node link graph as a html file using plotly and the info in the database.
        """
        source_objs = Source.objects.filter(user=request.user)
        objs = []
        for s in source_objs:
            objs.extend(ExtractedRelation.objects.filter(source=s))
        unique_ents = set()
        edges = []
        rels = set()
        for obj in objs:
            if obj.pred_relation == 'NA':
                continue
            unique_ents.add(obj.head)
            unique_ents.add(obj.tail)
            edges.append((obj.head, obj.tail, obj.pred_relation))
            rels.add(obj.pred_relation)
        
        rels = list(rels)
        
        G = nx.Graph()

        for i in unique_ents:
            G.add_node(i, node_type='Entity')

        for e in edges:
            G.add_edge(e[0], e[1], typ=e[2])

        pos = graphviz_layout(G, prog='neato')   
        traces = []
        colors = ['deeppink', 'dodgerblue', 'aquamarine', 'azure',
            'darkviolet', 'black', 'darkslategrey',
            'darkturquoise', 'deepskyblue',
            'dimgray']

        for edge in G.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=1,color=colors[rels.index(edge[2]['typ'])]),
                hoverinfo='none',
                mode='lines',
                name='Entity-Entity Connection',
                showlegend=False)
            traces.append(edge_trace)
        
        for r in rels:
            print("{}: {}".format(r, colors[rels.index(r)]))

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
                        title='Relationship between different Entities',
                        titlefont=dict(size=16),
                        hovermode='closest',
                        margin=dict(b=20,l=5,r=5,t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        fig.write_html("static/node_link_viz.html")
        