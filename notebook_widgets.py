"""
Function to access Catma Annotation Collection by ipywidgets.
"""

import os
from catma_gitlab.catma_gitlab_classes import AnnotationCollection
from ipywidgets import interact, Dropdown, Layout
import plotly.express as px
from IPython.display import display


def select_annotation_collection(projects_direction):
    if projects_direction[:-1] not in os.getcwd():
        os.chdir(projects_direction)

    project = Dropdown(
        options=os.listdir(),
        value=os.listdir()[0],
        description='Project:',
        layout=Layout(width='80%')
    )

    def select_project(project_direction):
        annotation_collection = Dropdown(
            options=os.listdir(f'{project_direction}/collections/'),
            value=os.listdir(f'{project_direction}/collections/')[0],
            description='Annotation Collection:',
            layout=Layout(width='80%')
        )

        def select_ac(ac_id):
            ac = AnnotationCollection(project_direction, catma_id=ac_id)
            df = ac.df
            for col in df.columns:
                if 'prop:' in col:
                    df[col] = df[col].astype(str)
            df['short_annotations'] = [
                item[:40] + '[...]' if len(item) > 40 else item for item in df['annotation']
            ]
            tag = Dropdown(
                options=list(df.tag.unique()) + ['all'],
                value='all',
                description='Tag:'
            )

            def select_tag(tag):
                if tag != 'all':
                    tag_df = df[df.tag == tag]
                else:
                    tag_df = df

                prop = Dropdown(
                    options=[c for c in df.columns if 'prop:' in c] + ['all'],
                    value='all',
                    description='Property:'
                )

                def select_property(prop):
                    ac_title = ac.name
                    document_title = ac.text.title

                    plot = True
                    if prop == 'all':
                        prop_df = tag_df
                        if tag == 'all':
                            fig = px.scatter(
                                prop_df, x='start_point', y='tag',
                                color='tag', opacity=0.5, marginal_x='histogram',
                                hover_data=['pretext', 'short_annotations', 'posttext'],
                                title=f'Tags in "{document_title}" (AC: {ac_title})'.upper()
                            )
                        else:
                            fig = px.scatter(
                                prop_df, x='start_point', y='tag', height=300,
                                color='tag', opacity=0.5, marginal_x='histogram',
                                hover_data=['pretext', 'short_annotations', 'posttext'],
                                title=f'<{tag}> in "{document_title}" (AC: {ac_title})'.upper()
                            )
                    else:
                        prop_df = tag_df[tag_df[prop] != 'nan']
                        if tag == 'all':
                            fig = px.scatter(
                                prop_df, x='start_point', y=prop, facet_row='tag',
                                color='tag', opacity=0.5, height=800,
                                hover_data=['pretext', 'short_annotations', 'posttext', prop],
                                title=f'{prop} in "{document_title}" (AC: {ac_title})'.upper())
                        else:
                            if len(prop_df) == 0:
                                plot = False
                            else:
                                values = prop_df[prop].unique()
                                fig = px.scatter(
                                    prop_df, x='start_point',
                                    y=prop, color='tag', opacity=0.5, height=len(values)*100,
                                    hover_data=['pretext', 'short_annotations', 'posttext', prop],
                                    title=f'Values of {prop} in <{tag}> in "{document_title}" \
                                    (AC: {ac_title})'.upper())

                    if plot:
                        fig.update_layout(font=dict(size=10))
                        fig.show()
                        return prop_df
                    else:
                        print(
                            'No annotation matches the selected tag property combination.'.upper())
                    

                interact(select_property, prop=prop)

            interact(select_tag, tag=tag)

        interact(select_ac, ac_id=annotation_collection)

    interact(select_project, project_direction=project)
