import pandas as pd
import networkx as nx
import plotly.graph_objects as go
from IPython.display import display
from gitma.annotation_collection import AnnotationCollection as ac


def affiliated_annotations(ac_df: pd.DataFrame, character_distance: int = 100) -> dict:
    tag_dict = {
        tag: {
            t: 0 for t in ac_df.tag.unique()
        } for tag in ac_df.tag.unique()
    }

    for _, row in ac_df.iterrows():
        filtered_df = ac_df[
            (ac_df.end_point > row.start_point - character_distance) &
            (ac_df.start_point < row.end_point + character_distance)
        ].copy()

        tag_count = dict(filtered_df.value_counts('tag'))

        for tag in tag_count:
            tag_dict[row.tag][tag] += tag_count[tag]

    return tag_dict


def edge_generator(tag_dict: dict):
    for tag in tag_dict:
        for t in tag_dict[tag]:
            if tag != t and tag_dict[tag][t] > 0:
                yield (tag, t, tag_dict[tag][t])


def create_network_from_edges(edge_list: list) -> nx.Graph:
    graph = nx.Graph()
    graph.add_weighted_edges_from(edge_list)
    return graph


def format_network_stats(stats_df: pd.DataFrame, character: str) -> str:
    stats_html_string = f'{character.upper().replace("_", " ")}<br>'
    for key in dict(stats_df.loc[character]):
        stats_html_string += '<b>' + key.upper() + '</b>' + ' = '
        stats_html_string += str(dict(stats_df.loc[character])[key]) + '<br>'
    return stats_html_string


def norm_col(value: float, values: pd.Series) -> float:
    return value / sum(values)


def get_node_data(
        pos_dict: dict,
        node_size_dict: dict,
        node_factor: int,
        node_alpha: int,
        stats: pd.DataFrame):
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


colors = [
    '#093658', '#A64B21', '#A68500', '#843AF2', '#F92F6A',
    '#5A98A1', '#EDA99D', '#EDC56D', '#274E54'
] * 100


def get_color_dict(annotation_df: pd.DataFrame, color_col: str, colors: list = colors):
    color_dict = {
        prop: colors[index] for index, prop
        in enumerate(list(annotation_df[color_col].unique()))
    }
    return color_dict


class Network:
    """Class to draw annotation coocurrence network graphs.
    """

    def __init__(
            self,
            annotation_collection: ac,
            character_distance: int = 100,
            start_point: float = 0,
            end_point: int = 1.0,
            included_tags: list = None,
            excluded_tags: list = None,
            network_layout: callable = nx.drawing.layout.kamada_kawai_layout):
        """Initiate Graph by

        Args:
            annotation_collection (ac): _description_
            character_distance (int, optional): _description_. Defaults to 100.
            start_point (float, optional): _description_. Defaults to 0.
            end_point (int, optional): _description_. Defaults to 1.0.
            included_tags (list, optional): _description_. Defaults to None.
            excluded_tags (list, optional): _description_. Defaults to None.
            network_layout (callable, optional): _description_. Defaults to nx.drawing.layout.kamada_kawai_layout.
        """
        self.title = annotation_collection.name
        self.df = annotation_collection.df

        # filter annotations by text position
        if start_point > 0 or end_point < 1:
            text_len = len(ac.Text)
            min_point = start_point * text_len
            max_point = end_point * text_len
            self.df = self.df[
                (self.df.start_point > min_point) &
                (self.df.end_point < max_point)
            ].copy()

        # filter annotations by tag
        if included_tags:
            self.df = self.df[
                self.df.tag.isin(included_tags)
            ].copy()

        if excluded_tags:
            self.df = self.df[
                ~self.df.tag.isin(excluded_tags)
            ].copy()

        # create networkx graph
        self.edges = list(
            edge_generator(
                tag_dict=affiliated_annotations(
                    ac_df=self.df,
                    character_distance=character_distance
                )
            )
        )
        self.network_graph = create_network_from_edges(edge_list=self.edges)

        self.pos = network_layout(self.network_graph, weight='weight')

    def stats(self) -> pd.DataFrame:
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
            plot_stats: bool = True):
        """Plots network as plotly graph.

        Args:
            node_size (str, optional): Which network metric to use as node size. Defaults to 'betweenness'.
            node_factor (float, optional): Customize the node size. Defaults to 100.0.
            node_alpha (int, optional): Minimal node size. Defaults to 3.
            plot_stats (bool, optional): Whether to plot the stats as `pandas.DataFrame`. Defaults to True.
        """

        stats = self.stats()

        node_size_dict = dict(
            stats[node_size].apply(
                norm_col,
                args=(stats[node_size],)
            )
        )

        color_dict = get_color_dict(
            annotation_df=self.df,
            color_col='tag'
        )

        fig = go.Figure()

        # plot edges
        for index, edge in enumerate(self.edges):
            x_values = [self.pos[edge[0]][0], self.pos[edge[1]][0]]
            y_values = [self.pos[edge[0]][1], self.pos[edge[1]][1]]
            fig.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    opacity=0.5,
                    mode='lines',
                    line=dict(
                        width=0.3 * edge[2],
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
            node_alpha=node_alpha,
            stats=stats
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

        fig.update_layout(
            template="simple_white",
            xaxis={'ticks': '', 'showticklabels': False,
                   'showgrid': False, 'visible': False},
            yaxis={'ticks': '', 'showticklabels': False,
                   'showgrid': False, 'visible': False},
            height=600,
            width=1000,
            title=f'Cooccurrence Tag Network for {self.title}'
        )

        fig.update_xaxes(
            range=[
                min(node_data['x_pos']) - 0.5 * max(node_data['x_pos']),
                max(node_data['x_pos']) + 0.5 * max(node_data['x_pos'])
            ]
        )
        fig.update_yaxes(
            range=[
                min(node_data['y_pos']) - 0.5 * max(node_data['y_pos']),
                max(node_data['y_pos']) + 0.5 * max(node_data['y_pos'])
            ]
        )

        fig.show()

        if plot_stats:
            display(stats.head(5))


if __name__ == "__main__":
    pass
