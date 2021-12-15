
"""
    :param ac: Catma AnnotationCollection
    :param y_axis: DataFrame column that will be mapped on y axis; default='tag'
    :param prop: CATMA Tagset Property name
    :param color_prop: can be used to define color coding in plot
    """


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
