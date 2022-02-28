from matplotlib.pyplot import legend, plot
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from gitma.annotation_collection import duplicate_rows


# list of catma related colors
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


def update_figure(fig: go.Figure):
    fig.update_layout(
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(
                color="#5A98A1",
                size=10
            )
        ),
        # legend_title_text=None,
    )
    return fig


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


def plot_annotations(ac, y_axis: str = 'tag', color_prop: str = 'tag'):
    """Creates interactive [Plotly Scatter Plot](https://plotly.com/python/line-and-scatter/) to a explore a annotation collection.

    Args:
        ac (AnnotationCollection): gitma.AnnotationCollection
        y_axis (str, optional): The columns in AnnotationCollection DataFrame used for y axis. Defaults to 'tag'.
        color_prop (str, optional): A Property's name used in the AnnotationCollection . Defaults to None.

    Returns:
        go.Figure: Plotly scatter plot.
    """

    if 'prop' in y_axis:
        ac.df = ac.duplicate_by_prop(prop=y_axis)
    if 'prop' in color_prop:
        ac.df = ac.duplicate_by_prop(prop=color_prop)

    plot_df = ac.df.copy()
    plot_df['size'] = plot_df['end_point'] - plot_df['start_point']
    plot_df['ANNOTATION'] = plot_df['annotation'].apply(format_annotation_text)
    prop_list = [item for item in plot_df.columns if 'prop:' in item]
    hover_cols = ['ANNOTATION'] + prop_list

    fig = px.scatter(
        plot_df,
        x='start_point',
        y=y_axis,
        size='size',
        hover_data=hover_cols,
        color=color_prop,
        color_discrete_map=get_color_dict(plot_df, color_col=color_prop),
        opacity=0.7,
        marginal_x='histogram',
        size_max=10
    )
    fig.update_xaxes(matches=None)
    fig = update_figure(fig)

    return fig


def plot_annotation_progression(project) -> go.Figure:
    """Plot the annotation progression for every annotator in a CATMA project.

    Args:
        project (CatmaProject): The plotted CATMA project.

    Returns:
        go.Figure: Plotly scatter plot.
    """
    plot_df = project.merge_annotations()
    plot_df['ANNOTATION'] = plot_df['annotation'].apply(format_annotation_text)
    fig = px.scatter(
        plot_df,
        x='start_point',
        y='date',
        color='annotator',
        hover_data=['ANNOTATION'],
        color_discrete_map=get_color_dict(plot_df, color_col='annotator'),
        marginal_y='histogram',
        facet_row='document',
        height=len(plot_df.document.unique()) * 300
    )
    fig.update_xaxes(matches=None, showticklabels=True, col=1)
    fig.update_xaxes(matches=None, col=2)
    fig.update_yaxes(matches=None, col=1)
    fig.update_yaxes(matches=None, col=2)
    fig = update_figure(fig)
    fig.update_layout(
        legend=dict(title='<b>Annotators:</b><br>')
    )
    return fig


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


def plot_interactive(catma_project, color_col: str = 'annotation collection') -> go.Figure:
    """This function generates one Plotly scatter plot per annotated document in a CATMA project.
    By default the colors represent the annotation collections.
    By that they can't be deactivated with the interactive legend.

    Args:
        catma_project (CatmaProject): The plotted project.
        color_col (str, optional): 'annotation collection', 'annotator', 'tag' or any property with the prefix 'prop:'. Defaults to 'annotation collection'.

    Returns:
        go.Figure: Plotly scatter plot.
    """
    merged_acs = pd.concat(
        ac.df for ac in catma_project.annotation_collections)
    merged_acs.loc[:, 'size'] = merged_acs.end_point - merged_acs.start_point
    merged_acs.loc[:, 'ANNOTATION'] = merged_acs.annotation.apply(
        format_annotation_text)

    if 'prop:' in color_col:
        merged_acs = duplicate_rows(
            ac_df=merged_acs,
            property_col=color_col
        )

    fig = px.scatter(
        merged_acs,
        x='start_point',
        y='tag',
        hover_data=['ANNOTATION'],
        color=color_col,
        facet_row='document',
        color_discrete_map=get_color_dict(merged_acs, color_col=color_col)
    )

    height = 300 + len(merged_acs.document.unique()) * \
        len(merged_acs.tag.unique()) * 15
    fig.update_layout(
        height=height,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    fig.update_xaxes(matches=None, showticklabels=True, col=1)
    fig = update_figure(fig)

    return fig


def compare_annotation_collections(
        catma_project,
        annotation_collections: list,
        color_col: str = 'tag') -> go.Figure:
    """Plots annotations of multiple annotation collections of the same texts as line plot.

    Args:
        catma_project (CatmaProject): _description_
        annotation_collections (list): A list of annotation collection names. 
        color_col (str, optional): Either 'tag' or one property name with prefix 'prop:'. Defaults to 'tag'.

    Raises:
        ValueError: If one of the annotation collection's names does not exist.

    Returns:
        go.Figure: Plotly Line Plot.
    """
    try:
        color_dict = get_color_dict(
            annotation_df=pd.concat(
                [catma_project.ac_dict[ac].duplicate_by_prop(prop=color_col)
                 if 'prop:' in color_col else catma_project.ac_dict[ac].df
                 for ac in annotation_collections]
            ),
            color_col=color_col
        )
    except ValueError:
        raise ValueError(
            f"""One of the given annotation collections does not exists.
            These are the existing annotation collections:
            {[ac.name for ac in catma_project.annotation_collections]}
            """
        )
    fig = go.Figure()
    used_tags = []
    for ac in annotation_collections:
        if 'prop:' in color_col:
            plot_df = catma_project.ac_dict[ac].duplicate_by_prop(
                prop=color_col.replace('prop:', '')
            )
        else:
            plot_df = catma_project.ac_dict[ac].df
        for _, row in plot_df.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row['start_point'], row['end_point']],
                    y=[ac, ac],
                    text=format_annotation_text(row['annotation']),
                    mode='lines + markers',
                    marker=dict(color=color_dict[row[color_col]]),
                    name=row[color_col],
                    legendgroup=row[color_col],
                    showlegend=False if row[color_col] in used_tags else True
                )
            )
            used_tags.append(row[color_col])
    fig.update_layout(
        title=f'Annotation Comparison by Text Span',
        height=len(annotation_collections) * 120)
    fig = update_figure(fig)

    return fig
