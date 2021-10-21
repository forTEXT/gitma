import json
import os
import pandas as pd
from catma_gitlab.text import Text
from catma_gitlab.annotation import Annotation


def load_annotations():
    pass


def ac_to_dataframe():
    pass


def split_property_dict_to_column(ac_df):
    """
    Creates Pandas DataFrame columns for each property in annotation collection.
    """
    properties_dict = {}

    for index, item in enumerate(ac_df['properties']):
        for key in item:
            if key not in properties_dict:
                prev_list = index * [['nan']]
                prev_list.append(item[key])
                properties_dict[key] = prev_list
            else:
                properties_dict[key].append(item[key])

        for prop in properties_dict:
            if prop not in item:
                properties_dict[prop].append(['nan'])

    for prop in properties_dict:
        ac_df[f'prop:{prop}'] = properties_dict[prop]

    return ac_df.drop(columns='properties')


def duplicate_rows(ac_df, property_col):
    """
    Duplicates rows in AnnotationCollection DataFrame if multiple property values exist in defined porperty column.
    """
    def duplicate_generator(df):
        for index, row in df.iterrows():
            if len(row[property_col]) > 1:
                for item in row[property_col]:
                    row_dict = dict(row)
                    row_dict[property_col] = item
                    yield row_dict
            else:
                row_dict = dict(row)
                if len(row[property_col]) > 0:
                    row_dict[property_col] = row[property_col][0]
                    yield dict(row_dict)
                else:
                    row_dict[property_col] = 'nan'
                    yield dict(row_dict)

    df_new = pd.DataFrame(list(duplicate_generator(ac_df)))
    return df_new


class AnnotationCollection:
    def __init__(self, project_uuid: str, catma_id: str):
        """
        Class which represents a CATMA annotation collection.
        :param project_uuid:  directory of a CATMA gitlab root folder
        :param catma_id: uuid of the collection (folder)
        """
        self.uuid = catma_id

        with open(project_uuid + '/collections/' + self.uuid + '/header.json') as header_json:
            self.header = json.load(header_json)

        self.name = self.header['name']

        self.plain_text_id = self.header['sourceDocumentId']
        self.text = Text(project_uuid=project_uuid,
                         catma_id=self.plain_text_id)
        self.text_version = self.header['sourceDocumentVersion']

        print(
            f"Loaded Annotation Collection '{self.name}' for {self.text.title}")

        if os.path.isdir(project_uuid + '/collections/' + self.uuid + '/annotations/'):
            self.annotations = [
                Annotation(
                    directory=project_uuid + '/collections/' +
                    self.uuid + '/annotations/' + annotation,
                    plain_text=self.text.plain_text
                ) for annotation in os.listdir(project_uuid + '/collections/' + self.uuid + '/annotations/')
            ]
            self.annotations = sorted(
                self.annotations, key=lambda a: a.start_point)
            self.tags = [an.tag for an in self.annotations]

            # create pandas data frame for annotation collection
            self.df = pd.DataFrame(
                [
                    (self.text.title, self.name, a.tag.name, a.properties, a.pretext,
                     a.text, a.posttext, a.start_point, a.end_point, a.date)
                    for a in self.annotations
                ], columns=['document', 'annotation collection', 'tag', 'properties', 'pretext',
                            'annotation', 'posttext', 'start_point', 'end_point', 'date']
            )
            self.df = split_property_dict_to_column(self.df)
        else:
            self.annotations = []
            self.df = pd.DataFrame(columns=['document', 'annotation collection', 'tag', 'properties', 'pretext',
                                            'annotation', 'posttext', 'start_point', 'end_point', 'date'])

        print(f"\t-> with {len(self.annotations)} Annotations.")

    def __repr__(self):
        return self.name

    from catma_gitlab._vizualize import plot_annotation_overview

    from catma_gitlab._export_annotations import to_stanford_tsv

    def tag_stats(self):
        return self.df.tag.value_counts()

    def property_stats(self):
        return pd.DataFrame(
            {col: duplicate_rows(self.df, col)[col].value_counts(
            ) for col in self.df.columns if 'prop:' in col}
        ).T

    def get_annotation_by_tag(self, tag_name: str):
        return [
            annotation for annotation in self.annotations
            if annotation.tag.name == tag_name
            or annotation.tag.parent.name == tag_name
        ]

    def annotate_properties(self, tag: str, prop: str, value: list):
        for an in self.annotations:
            an.set_property_values(tag=tag, prop=prop, value=value)

    def rename_property_value(self, tag: str, prop: str, old_value: str, new_value: str):
        for an in self.annotations:
            an.modify_property_value(
                tag=tag, prop=prop, old_value=old_value, new_value=new_value)

    def delete_properties(self, tag: str, prop: str):
        for an in self.annotations:
            an.delete_property(tag=tag, prop=prop)
