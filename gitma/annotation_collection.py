import json
import os
from collections import Counter
import string
import pandas as pd
from gitma.text import Text
from gitma.annotation import Annotation


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


def duplicate_rows(ac_df: pd.DataFrame, property_col: str) -> pd.DataFrame:
    """
    Duplicates rows in AnnotationCollection DataFrame if multiple property values exist in defined porperty column.
    """
    if 'prop:' not in property_col:
        property_col = f'prop:{property_col}'

    if property_col not in ac_df.columns:
        raise ValueError(
            f'{property_col} is not a valid value in the given annotation collections. Choose any of these: {list(ac_df.columns)}')

    def duplicate_generator(df):
        for _, row in df.iterrows():
            if isinstance(row[property_col], list) and len(row[property_col]) > 0:
                for item in row[property_col]:
                    row_dict = dict(row)
                    row_dict[property_col] = item
                    yield row_dict
            elif isinstance(row[property_col], str) and len(row[property_col]) > 0:
                yield dict(row)
            elif isinstance(row[property_col], int) or isinstance(row[property_col], float):
                yield dict(row)
            else:
                row_dict = dict(row)
                row_dict[property_col] = 'NOT ANNOTATED'
                yield dict(row_dict)

    df_new = pd.DataFrame(list(duplicate_generator(ac_df)))
    return df_new


def most_common_token(
        annotation_col: pd.Series,
        stopwords: list = None,
        ranking: int = 10) -> dict:
    """Counts Token for list of strings.

    Args:
        annotation_col (pd.Series): The columns name to be analyzed.
        stopwords (list, optional): List of stopwords. Defaults to None.
        ranking (int, optional): Number of most common token to include. Defaults to 10.

    Returns:
        dict: Dictionary storing the token freqeuncies.
    """
    token_list = []
    for str_item in annotation_col:
        removed_punctation = str_item.translate(
            str.maketrans('', '', string.punctuation))
        token_list.extend(removed_punctation.split(' '))

    while '' in token_list:
        token_list.remove('')

    # remove stopwords
    if stopwords:
        token_list = [
            token for token in token_list if token not in stopwords]

    return dict(Counter(token_list).most_common(ranking))


def get_text_span_per_tag(ac_df: pd.DataFrame) -> int:
    return sum(ac_df['end_point'] - ac_df['start_point'])


def get_text_span_mean_per_tag(ac_df: pd.DataFrame) -> int:
    return sum(ac_df['end_point'] - ac_df['start_point']) / len(ac_df)


class AnnotationCollection:
    def __init__(self, ac_uuid: str, catma_project, context: int = 50):
        """Class which represents a CATMA annotation collection.

        Args:
            ac_uuid (str): The annotation collection's UUID
            catma_project (CatmaProject): The parent Catma Project
            context (int, optional): The text span to be considered for the annotation context. Defaults to 50.

        Raises:
            FileNotFoundError: If the directory of the Annotation Collection header.json does not exists.
        """
        self.uuid = ac_uuid

        try:
            with open(catma_project.uuid + '/collections/' + self.uuid + '/header.json') as header_json:
                self.header = json.load(header_json)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The Annotation Collection in this directory could not be found:\n{self.directory}\n\
                    --> Make sure the CATMA Project clone did work properly.")

        self.name = self.header['name']

        self.plain_text_id = self.header['sourceDocumentId']
        self.text = Text(project_uuid=catma_project.uuid,
                         catma_id=self.plain_text_id)
        self.text_version = self.header['sourceDocumentVersion']

        print(
            f"\t Loading Annotation Collection '{self.name}' for {self.text.title}")

        df_columns = [
            'document', 'annotation collection', 'annotator',
            'tag', 'properties', 'left_context', 'annotation',
            'right_context', 'start_point', 'end_point', 'date'
        ]

        if os.path.isdir(catma_project.uuid + '/collections/' + self.uuid + '/annotations/'):
            self.annotations = sorted([
                Annotation(
                    directory=f'{catma_project.uuid}/collections/{self.uuid}/annotations/{annotation_dir}',
                    plain_text=self.text.plain_text,
                    catma_project=catma_project,
                    context=context
                ) for annotation_dir in os.listdir(catma_project.uuid + '/collections/' + self.uuid + '/annotations/')
                if annotation_dir.startswith('CATMA_')
            ])

            self.tags = [an.tag for an in self.annotations]

            # create pandas data frame for annotation collection
            self.df = pd.DataFrame(
                [
                    (self.text.title, self.name, a.author, a.tag.name, a.properties, a.pretext,
                     a.text, a.posttext, a.start_point, a.end_point, a.date)
                    for a in self.annotations
                ], columns=df_columns
            )
            self.df = split_property_dict_to_column(self.df)
        else:
            self.annotations = []
            self.df = pd.DataFrame(columns=df_columns)

        print(f"\t-> with {len(self.annotations)} Annotations.")

    def __repr__(self):
        return f"AnnotationCollection(Name: {self.name}, Document: {self.text.title}, Length: {len(self)})"

    def __len__(self):
        return len(self.annotations)

    def __iter__(self):
        for an in self.annotations:
            yield an

    def duplicate_by_prop(self, prop: str):
        try:
            return duplicate_rows(ac_df=self.df, property_col=prop)
        except KeyError:
            prop_cols = [item.replace('prop:', '')
                         for item in self.df.columns if 'prop:' in item]
            raise ValueError(
                f"Given Property doesn't exist. Choose one of these: {prop_cols}")

    from gitma._vizualize import plot_annotations

    from gitma._vizualize import plot_scaled_annotations

    from gitma._export_annotations import to_stanford_tsv

    def cooccurrence_network(
            self, character_distance: int = 100,
            start_point: float = 0, end_point: float = 1.0,
            included_tags: list = None, excluded_tags: list = None,
            plot_stats: bool = True):
        """Draws cooccurrence network graph.

        Args:
            character_distance (int, optional): In which distance annotations are considered coocurrent. Defaults to 100.
            start_point (float, optional): Which texparts to consider. Defaults to 0.
            end_point (float, optional): Which texparts to consider. Defaults to 1.0.
            included_tags (list, optional): List of included tags. Defaults to None.
            excluded_tags (list, optional): List of excluded tags. Defaults to None.
            plot_stats (bool, optional): Whether to return network stats. Defaults to True.
        """
        from gitma.network import Network

        nw = Network(
            annotation_collection=self,
            character_distance=character_distance,
            start_point=start_point,
            end_point=end_point,
            included_tags=included_tags,
            excluded_tags=excluded_tags
        )
        nw.plot(plot_stats=plot_stats)

    def to_pygamma_table(self):
        return self.df[['annotator', 'tag', 'start_point', 'end_point']]

    def tag_stats(
            self,
            tag_col: str = 'tag',
            stopwords: list = None,
            ranking: int = 10) -> pd.DataFrame:
        """Get data for Tags.

        Args:
            tag_col (str, optional): Whether the data for the tag a property or annotators gets computed. Defaults to 'tag'.
            stopwords (list, optional): A list with stopword tokens. Defaults to None.
            ranking (int, optional): The number of most frequent token to be included. Defaults to 10.

        Returns:
            pd.DataFrame: The data as pandas DataFrame.
        """

        if 'prop:' in tag_col:
            analyze_df = duplicate_rows(self.df, property_col=tag_col)
        else:
            analyze_df = self.df

        tag_data = {}
        for tag in analyze_df[tag_col].unique():
            filtered_df = analyze_df[analyze_df[tag_col] == tag]
            tag_data[tag] = {
                'annotations': len(filtered_df),
                'text_span': get_text_span_per_tag(ac_df=filtered_df),
                'text_span_mean': get_text_span_mean_per_tag(ac_df=filtered_df),
            }
            mct = most_common_token(
                annotation_col=filtered_df['annotation'],
                stopwords=stopwords,
                ranking=ranking
            )
            for token_index, token in enumerate(mct):
                tag_data[tag][f'token{token_index + 1}'] = f'{token}: {mct[token]}'

        return pd.DataFrame(tag_data).T

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
