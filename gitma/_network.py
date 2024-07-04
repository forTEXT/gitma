import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from typing import List, Dict
from dataclasses import dataclass
from IPython.display import display
from gitma.annotation_collection import AnnotationCollection, duplicate_rows


# define CATMA related 
COLORS = [
    '#093658', '#A64B21', '#A68500', '#843AF2', '#F92F6A',
    '#5A98A1', '#EDA99D', '#EDC56D', '#274E54'
] * 100


def get_color_dict(annotation_df: pd.DataFrame, color_col: str = 'tag', colors: list = None) -> Dict[str, str]:
    """Creates a color dict where every tag get a single color.

    Args:
        annotation_df (pd.DataFrame): DataFrame in the AnnotationCollection.df format.
        color_col (str): 'tag' or another column in the annotation_df. Defaults to 'tag'.
        colors (list, optional): List of colors as hex value. Defaults to None.

    Returns:
        Dict[str, str]: Dictionary with tag names as keys and colors as hex value.
    """
    if not colors:
        colors = COLORS
    color_dict = {
        prop: colors[index] for index, prop
        in enumerate(list(annotation_df[color_col].unique()))
    }
    return color_dict


@dataclass
class Edge:
    """Class that represents an network edge.
    """
    source: str
    target: str
    weight: int

    def to_tuple(self) -> tuple:
        return (self.source, self.target, self.weight)
    
    def __getitem__(self, index: int):
        return [self.source, self.target, self.weight][index]


def cooccurrent_annotations(
    ac_df: pd.DataFrame,
    character_distance: int = 100,
    level='tag') -> dict:
    """Function to find coocurrent annotation within one document.

    Args:
        ac_df (pd.DataFrame): Pandas DataFrame in the format of gitma.AnnotationCollection.df .
        character_distance (int, optional): The maximal distance between two annotations considered coocurrent. Defaults to 100.
        level (str, optional): 'Tag' or any property used in the gitma.AnnotationCollection.df with the prefix 'prop:'. Defaults to 'tag'.

    Returns:
        dict: A dictionary with cooccurency frequency in the format:
        {
            'tag1': {
                'tag2': 4,
                'tag3': 2
            },
            'tag2':{
                'tag1': 4,
                'tag3': 1
            }
        }
    """
    tag_dict = {
        tag: {
            t: 0 for t in ac_df[level].unique()
        } for tag in ac_df[level].unique()
    }

    for _, row in ac_df.iterrows():
        filtered_df = ac_df[
            (ac_df.end_point > row.start_point - character_distance) &
            (ac_df.start_point < row.end_point + character_distance) &
            (ac_df['document'] == row['document'])
        ].copy()

        tag_count = dict(filtered_df[level].value_counts())

        for tag in tag_count:
            tag_dict[row[level]][tag] += tag_count[tag]

    return tag_dict


def overlapping_annotations(
    ac_df: pd.DataFrame,
    level: str = 'tag',
    only_different_acs: bool = True) -> dict:
    """Searches for overlapping annotations and returns frequency of overlapping pairs.

    Args:
        ac_df (pd.DataFrame): DataFrame in the format of gitma.AnnotationCollection.df
        level (str, optional): Tag' or any property used in the gitma.AnnotationCollection.df with the prefix 'prop:'. Defaults to 'tag'.
        only_different_acs (bool, optional): If True only overlapping annotatiosn from different annotation collections\
            are considered. Defaults to True.

    Returns:
        dict: A dictionary with cooccurency frequency in the format:
        {
            'tag1': {
                'tag2': 4,
                'tag3': 2
            },
            'tag2':{
                'tag1': 4,
                'tag3': 1
            }
        }
    """
    tag_dict = {
        tag: {
            t: 0 for t in ac_df[level].unique()
        } for tag in ac_df[level].unique()
    }

    for _, row in ac_df.iterrows():
        document_df = ac_df[
            ac_df['document'] == row['document']
        ].copy()

        embedded_annotations = document_df[
            (row.start_point <= document_df.start_point) &
            (row.end_point >= document_df.end_point)
        ].copy()

        overlapping_annotations = document_df[
            (row.start_point < document_df.end_point) |
            (row.end_point > document_df.start_point)
        ].copy()

        filtered_df = pd.concat([
            embedded_annotations,
            overlapping_annotations
        ])

        if only_different_acs:
            filtered_df = filtered_df[
                filtered_df['annotation collection'] != row['annotation collection']
            ]

        tag_count = dict(filtered_df[level].value_counts())

        for tag in tag_count:
            tag_dict[row[level]][tag] += tag_count[tag]

    return tag_dict


def edge_generator(tag_dict: dict):
    for tag in tag_dict:
        for t in tag_dict[tag]:
            # not recursive edges, only edges with weigt >= 1
            if tag != t and tag_dict[tag][t] > 0:
                yield Edge(
                    source=tag,
                    target=t,
                    weight=tag_dict[tag][t]
                )



def create_network_from_edges(edge_list: List[Edge]) -> nx.Graph:
    """Creates networkX from Edge object.

    Args:
        edge_list (List[Edge]): List of edges.

    Returns:
        nx.Graph: A nedworkX graph.
    """
    edges = [edge.to_tuple() for edge in edge_list]
    graph = nx.Graph()
    graph.add_weighted_edges_from(edges)
    return graph


def norm_col(value: float, values: pd.Series) -> float:
    """Normalizes value in a pandas series.

    Args:
        value (float): Cell value.
        value (pd.Series): Column value.

    Returns:
        float: Normalized cell value.
    """
    return value / sum(values)


def get_node_data(
        pos_dict: dict,
        node_size_dict: dict,
        node_factor: int,
        node_alpha: int) -> Dict[str, list]:
    """Creates dictionary with 

    Args:
        pos_dict (dict): _description_
        node_size_dict (dict): _description_
        node_factor (int): _description_
        node_alpha (int): _description_

    Returns:
        Dict[str, list]: The node's x and y axis positions, their size and their label.
    """
    nodes = list(node_size_dict)
    x_positions = [pos_dict[node][0] for node in nodes]
    y_positions = [pos_dict[node][1] for node in nodes]
    marker_sizes = [node_size_dict[node] *
                    node_factor + node_alpha for node in nodes]

    return {
        'x_pos': x_positions,
        'y_pos': y_positions,
        'marker_size': marker_sizes,
        'node_label': nodes,
    }


class Network:
    """Class to draw annotation coocurrence network graphs.
    
    Args:
            annotation_collections (List[AnnotationCollection]): List of included annotation collections.
            character_distance (int, optional): Cooccurrence span. Defaults to 100.
            edge_func (str, optional): Keyword for the function that identifies connected annotation.\
                Either `'cooccurent'` or `'overlapping'`. Defaults to cooccurrent_annotation. 
            included_tags (list, optional): Included tag. If `None` and excluded_tags `None` all tags are included.\
                Defaults to None.
            excluded_tags (list, optional): Excluded tag. Defaults to None.
            level (str, optional): Whether the annotation tag or the value of the given property gets included.
            network_layout (callable, optional): NetworkX Drawing Layout. Defaults to nx.drawing.layout.kamada_kawai_layout.
    """

    def __init__(
            self,
            annotation_collections: List[AnnotationCollection],
            character_distance: int = 100,
            edge_func: str = 'cooccurrent',
            included_tags: list = None,
            excluded_tags: list = None,
            level: str = 'tag',
            network_layout: callable = nx.drawing.layout.kamada_kawai_layout):
        #: The edge function.
        self.edge_func: callable = edge_func
        
        #: The annotation level.
        self.level: str = level
        
        #: Merged annotation dataframe
        self.df: pd.DataFrame = pd.concat(
            [ac.df for ac in annotation_collections if not ac.df.empty]
        )
        if level != 'tag':
            self.df = duplicate_rows(self.df, property_col=level)
            self.df = self.df[
                self.df[level] != 'NOT ANNOTATED'
            ].copy()

        # filter annotation by tag
        if included_tags:
            self.df = self.df[
                self.df.tag.isin(included_tags)
            ].copy()

        if excluded_tags:
            self.df = self.df[
                ~self.df.tag.isin(excluded_tags)
            ].copy()

        # get tag dict for edge weights
        if edge_func == 'overlapping':
            tag_dict = overlapping_annotations(
                ac_df=self.df,
                level=level
            )
        else:
            tag_dict = cooccurrent_annotations(
                ac_df=self.df,
                character_distance=character_distance,
                level=level
            )

        # create networkx graph
        #: List of edge objects.
        self.edges: List[Edge] = list(edge_generator(tag_dict=tag_dict))
        
        #: The networkX graph object.
        self.network_graph: nx.Graph = create_network_from_edges(edge_list=self.edges)

        #: The node position
        self.pos: dict = network_layout(self.network_graph, weight='weight')

    def to_gexf(self, filename: str = 'catma_network', directory: str = './') -> None:
        """Writes Network Graph to a GEPHI xml file.

        Args:
            filename (str, optional): The name of the gexf file. Defaults to 'catma_network'.
            directory (str, optional): The file's directory. Defaults to './'.
        """
        nx.write_gexf(self.network_graph, f'{directory}{filename}.gexf')

    def stats(self) -> pd.DataFrame:
        """Creates network stats data frame.

        Returns:
            pd.DataFrame: degree, weighted_degree, betweenness centrality, weighted betweenness centrality
        """
        bc = nx.betweenness_centrality(self.network_graph, normalized=True)
        bc_weighted = nx.betweenness_centrality(
            self.network_graph, normalized=True, weight='weight')
        degree = self.network_graph.degree()
        weighted_degree = self.network_graph.degree(weight='weight')
        network_df = pd.DataFrame(
            {
                'degree': dict(degree),
                'weighted_degree': dict(weighted_degree),
                'betweenness': dict(bc),
                'betweenness_weighted': dict(bc_weighted),
            }
        )
        network_df = network_df[network_df.degree > 0]
        return network_df.sort_values(by='betweenness', ascending=False).fillna(value=0)

    def plot(
            self,
            node_size: str = 'weighted_degree',
            node_factor: float = 100.0,
            node_alpha: int = 15,
            plot_stats: bool = False):
        """Plots network as plotly graph.

        Args:
            node_size (str, optional): Which network metric to use as node size. Defaults to 'betweenness'.
            node_factor (float, optional): Customize the node size. Defaults to 100.0.
            node_alpha (int, optional): Minimal node size. Defaults to 3.
            plot_stats (bool, optional): Whether to plot the stats as `pandas.DataFrame`. Defaults to True.
        """

        stats = self.stats()

        # get normalized node sizes
        node_size_dict = dict(
            stats[node_size].apply(
                norm_col,
                args=(stats[node_size],)
            )
        )

        color_dict = get_color_dict(
            annotation_df=self.df,
            color_col=self.level
        )
        fig = go.Figure()

        # plot edges
        sum_edges = sum([edge.weight for edge in self.edges])
        for index, edge in enumerate(self.edges):
            x_values = [self.pos[edge.source][0], self.pos[edge.target][0]]
            y_values = [self.pos[edge.source][1], self.pos[edge.target][1]]
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    opacity=0.5,
                    mode='lines',
                    line=dict(
                        width=1 + (50 * edge.weight / sum_edges),    # normalized edge weight
                        color='grey'
                    ),
                    name='Edges',
                    legendgroup='edges',
                    showlegend=True if index == 0 else False,
                )
            )

        # plot nodes
        node_data = get_node_data(
            pos_dict=self.pos,
            node_size_dict=node_size_dict,
            node_factor=node_factor,
            node_alpha=node_alpha
        )
        fig.add_trace(
            go.Scatter(
                x=node_data['x_pos'],
                y=node_data['y_pos'],
                marker={
                    'size': node_data['marker_size'],
                    'color': [color_dict[tag] for tag in node_data['node_label']],
                    'opacity': 0.65
                },
                text=node_data['node_label'],
                textposition='top center',
                mode='markers + text',
                showlegend=False,
                hoverinfo='text',
                textfont_size=[0.5 * item for item in node_data['marker_size']]
            )
        )

        title = 'Cooccurence' if self.edge_func == 'cooccurrent' else 'Disagreement'
        fig.update_layout(
            template="simple_white",
            xaxis={'ticks': '', 'showticklabels': False,
                   'showgrid': False, 'visible': False},
            yaxis={'ticks': '', 'showticklabels': False,
                   'showgrid': False, 'visible': False},
            # height=600,
            # width=1000,
            title=f'{title} Network for {self.level.upper()}'
        )

        if len(self.edges) > 0: # prevents: ValueError: min() arg is an empty sequence
            fig.update_xaxes(
                range=[
                    min(node_data['x_pos']) - 0.5 * max(node_data['x_pos']),
                    max(node_data['x_pos']) + 0.5 * max(node_data['x_pos'])
                ]
            )
            fig.update_yaxes(
                range=[
                    min(node_data['y_pos']) - 0.5 * max(node_data['y_pos']),
                    max(node_data['y_pos']) + 0.7 * max(node_data['y_pos'])
                ]
            )

        if plot_stats:
            display(stats.head(5))
        
        return fig
