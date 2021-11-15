

def plot_annotation_overview(ac, y_axis='tag', prop=None, color_prop=None):
    """
    :param ac: Catma AnnotationCollection
    :param y_axis: DataFrame column that will be mapped on y axis; default='tag'
    :param prop: CATMA Tagset Property name
    :param color_prop: can be used to define color coding in plot
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