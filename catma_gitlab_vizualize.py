import plotly.express as px
from pandas import DataFrame


def plot_scatter_bar(ac_df: DataFrame, y_axis='tag', prop=None, color_prop=None):
    """
    :param ac_df: AnnotationCollection.df
    :param y_axis: DataFrame column that will be mapped on y axis; default=tag
    :param prop: CATMA Tagset Property name
    :param color_prop: can be used to define color coding in plot
    """

    plot_df = ac_df

    split_by_y = y_axis if not prop else f'prop:{prop}'
    color = 'tag' if not color_prop else f'prop:{color_prop}'

    if prop:
        plot_df[f'prop:{prop}'] = [str(item) for item in plot_df[f'prop:{prop}']]
    if color_prop:
        plot_df[f'prop:{color_prop}'] = [str(item) for item in plot_df[f'prop:{color_prop}']]

    prop_list = [item for item in plot_df.columns if 'prop:' in item]
    hover_cols = ['annotation'] + prop_list

    fig = px.scatter(
        plot_df,
        x='start_point',
        y=split_by_y,
        hover_data=hover_cols,
        color=color,
        opacity=0.7
    )

    fig.show()
