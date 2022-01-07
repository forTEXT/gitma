import pandas as pd
from plotly.subplots import make_subplots


def format_annotation_text(text: str) -> str:
    """Format the text of an annotation for plotting.

    Args:
        text (str): annotation_string

    Returns:
        str: html formatted string
    """
    while '  ' in text:
        text = text.replace('  ', ' ')

    text_list = text.split(' ')
    output_string = "<I><br>"
    max_iter = len(text_list) if len(text_list) <= 60 else 60
    for item in range(0, max_iter, 10):
        output_string += ' '.join(text_list[item: item + 10]) + '<br>'

    if len(text_list) > 60:
        output_string += '[...]'

    output_string += "</I>"

    return output_string


def plot_annotation_overview(ac, y_axis: str = 'tag', prop: str = None, color_prop: str = None):
    """Creates interactive [Plotly Scatter Plot](https://plotly.com/python/line-and-scatter/) to a explore a annotation collection.

    Args:
        ac (AnnotationCollection): catma_gitlab.AnnotationCollection
        y_axis (str, optional): The columns in AnnotationCollection DataFrame used for y axis. Defaults to 'tag'.
        prop (str, optional): A Property's name used in the AnnotationCollection. Defaults to None.
        color_prop (str, optional): A Property's name used in the AnnotationCollection . Defaults to None.
    """
    import plotly.express as px

    plot_df = ac.df.copy()

    split_by_y = y_axis if not prop else f'prop:{prop}'
    color = 'tag' if not color_prop else f'prop:{color_prop}'

    if prop:
        plot_df[f'prop:{prop}'] = [str(item)
                                   for item in plot_df[f'prop:{prop}']]
    if color_prop:
        plot_df[f'prop:{color_prop}'] = [
            str(item) for item in plot_df[f'prop:{color_prop}']]

    plot_df['ANNOTATION'] = plot_df['annotation'].apply(format_annotation_text)
    prop_list = [item for item in plot_df.columns if 'prop:' in item]
    hover_cols = ['ANNOTATION'] + prop_list

    fig = px.scatter(
        plot_df,
        x='start_point',
        y=split_by_y,
        hover_data=hover_cols,
        color=color,
        opacity=0.7,
        marginal_x='histogram'
    )

    fig.show()


def plot_annotation_progression(project, ac_filter: list = None):
    import matplotlib.pyplot as plt

    acs = project.annotation_collections
    if ac_filter:
        acs = [
            ac for ac in acs
            if ac.name in ac_filter
        ]
    else:
        acs = project.annotation_collections

    fig, ax = plt.subplots(
        nrows=len(acs),
        figsize=[6, 10]
    )

    for index, ac in enumerate(acs):
        x_values = ac.df['date']
        y_values = range(len(ac.df))
        ax[index].scatter(x_values, y_values, alpha=0.3, label=ac.name)
        ax[index].legend()
        ax[index].set_ylabel('Annotations')

    ax[len(acs) - 1].set_xlabel('Date')
    fig.tight_layout()
    plt.show()


def plot_scaled_annotations(ac, tag_scale: dict = None, bin_size: int = 50, smoothing_window: int = 100):
    import plotly.graph_objects as go

    if tag_scale:
        plot_df = ac.df[ac.df.tag.isin(list(tag_scale))].copy()

        if len(plot_df) < 0:
            raise Exception(
                'None of the given tags have been used in the Annotation Collection!')

        plot_df.loc[:, 'abs_tag_values'] = [tag_scale[tag_item]
                                            for tag_item in plot_df.tag]
    else:
        plot_df = ac.df.copy()
        plot_df.loc[:, 'abs_tag_values'] = [1 for _ in plot_df.tag]

    bin_tag_values = []
    for item in range(0, len(ac.text.plain_text), bin_size):
        bin_tag_values.append(
            plot_df[
                (plot_df['start_point'] >= item) &
                (plot_df['end_point'] <= item + bin_size)
            ]['abs_tag_values'].sum()
        )

    fig = go.Figure(
        data=go.Scatter(
            x=list(range(0, len(ac.text.plain_text), bin_size)),
            y=bin_tag_values
        )
    )

    fig.show()


def plot_interactive(catma_project: "CatmaProject", color_col: str = 'annotator') -> None:
    import plotly.express as px

    plot_df = pd.DataFrame()
    text_counter = {text.title: 0 for text in catma_project.texts}
    for ac in catma_project.annotation_collections:
        text_counter[ac.text.title] += 1
        new_df = ac.df
        new_df.loc[:, 'AnnotationCollectionID'] = [
            text_counter[ac.text.title]] * len(ac.df)
        plot_df = plot_df.append(new_df, ignore_index=True)

    plot_df['ANNOTATION'] = plot_df['annotation'].apply(format_annotation_text)
    prop_list = [item for item in plot_df.columns if 'prop:' in item]
    hover_cols = ['ANNOTATION'] + prop_list

    width = len([item for item in text_counter if text_counter[item] > 0]) * 800
    height = max([text_counter[item] for item in text_counter]) * 400

    fig = px.scatter(
        plot_df,
        x='start_point',
        y='tag',
        hover_data=hover_cols,
        color=color_col,
        opacity=0.7,
        marginal_x='histogram',
        facet_col='document',
        facet_row='AnnotationCollectionID',
        height=height,
        width=width
    )

    fig.show()
