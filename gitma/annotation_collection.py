import json
import os
from typing import List, Union
from collections import Counter
import string
import pandas as pd
from gitma.text import Text
from gitma.annotation import Annotation
from gitma.tag import Tag


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


def clean_text_in_ac_df(annotation: str) -> str:
    annotation = annotation.replace('\n', ' ')
    while '  ' in annotation:
        annotation = annotation.replace('  ', ' ')
    return annotation


df_columns = [
    'document', 'annotation collection', 'annotator',
    'tag', 'properties', 'left_context', 'annotation',
    'right_context', 'start_point', 'end_point', 'date'
]


def ac_to_df(annotations: List[Annotation], text_title, ac_name) -> pd.DataFrame:
    # create df
    df = pd.DataFrame(
        [
            (text_title, ac_name, a.author, a.tag.name, a.properties, a.pretext,
                a.text, a.posttext, a.start_point, a.end_point, a.date)
            for a in annotations
        ], columns=df_columns
    )

    # create property columns
    df = split_property_dict_to_column(df)

    # clean annotations
    df['left_context'] = df['left_context'].apply(clean_text_in_ac_df)
    df['annotation'] = df['annotation'].apply(clean_text_in_ac_df)
    df['right_context'] = df['right_context'].apply(clean_text_in_ac_df)

    return df


class AnnotationCollection:
    """Class which represents a CATMA annotation collection.

    Args:
        ac_uuid (str): The annotation collection's UUID
        catma_project (CatmaProject): The parent Catma Project
        context (int, optional): The text span to be considered for the annotation context. Defaults to 50.

    Raises:
        FileNotFoundError: If the directory of the Annotation Collection header.json does not exists.
    """

    def __init__(self, ac_uuid: str, catma_project, context: int = 50):
        #: The annotation collection's UUID.
        self.uuid: str = ac_uuid

        try:
            with open(catma_project.uuid + '/collections/' + self.uuid + '/header.json') as header_json:
                self.header = json.load(header_json)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The Annotation Collection in this directory could not be found:\n{self.directory}\n\
                    --> Make sure the CATMA Project clone did work properly.")

        #: The annotation collection's name.
        self.name: str = self.header['name']

        #: The UUID of the annotation collection's document.
        self.plain_text_id: str = self.header['sourceDocumentId']

        #: The document of the annotation collection as a gitma.Text object.
        self.text: Text = Text(project_uuid=catma_project.uuid,
                               catma_id=self.plain_text_id)

        #: The document's version.
        self.text_version: str = self.header['sourceDocumentVersion']

        print(
            f"\t Loading Annotation Collection '{self.name}' for {self.text.title}")

        if os.path.isdir(catma_project.uuid + '/collections/' + self.uuid + '/annotations/'):
            #: List of annotations in annotation collection as gitma.Annotation objects.
            self.annotations: List[Annotation] = sorted([
                Annotation(
                    directory=f'{catma_project.uuid}/collections/{self.uuid}/annotations/{annotation_dir}',
                    plain_text=self.text.plain_text,
                    catma_project=catma_project,
                    context=context
                ) for annotation_dir in os.listdir(catma_project.uuid + '/collections/' + self.uuid + '/annotations/')
                if annotation_dir.startswith('CATMA_')
            ])

            #: List of tags found in the annotation collection as a list of gitma.Tag objects.
            self.tags: List[Tag] = [an.tag for an in self.annotations]

            #:  Annotations as a pandas.DataFrame.
            self.df: pd.DataFrame = ac_to_df(
                annotations=self.annotations,
                text_title=self.text.title,
                ac_name=self.name
            )
        else:
            self.annotations: list = []
            self.df: pd.DataFrame = pd.DataFrame(columns=df_columns)

        print(f"\t-> with {len(self.annotations)} Annotations.")

    def __repr__(self):
        return f"AnnotationCollection(Name: {self.name}, Document: {self.text.title}, Length: {len(self)})"

    def __len__(self):
        return len(self.annotations)

    def __iter__(self):
        for an in self.annotations:
            yield an

    def duplicate_by_prop(self, prop: str) -> pd.DataFrame:
        """Duplicates the rows in the annotation collection's DataFrame if the given Property has multiple Property Values
        the annotations represented by a DataFrame row.

        Args:
            prop (str): A property used in the annotation collection.

        Raises:
            ValueError: If the property has not been used in the annotation collection.

        Returns:
            pd.DataFrame: A duplicate of the annotation collection's DataFrame.
        """
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
            self,
            character_distance: int = 100,
            included_tags: list = None, excluded_tags: list = None,
            level: str = 'tag',
            plot_stats: bool = True,
            save_as_gexf: Union[bool, str]= False):
        """Draws cooccurrence network graph where every tag is a node and every edge represents two cooccurent tags.
        You can by the `character_distance` parameter when two annotations are considered cooccurent.
        If you set `character_distance=0` only the tags of overlapping annotations will be represented
        as connected nodes.

        Args:
            character_distance (int, optional): In which distance annotations are considered coocurrent. Defaults to 100.
            included_tags (list, optional): List of included tags. Defaults to None.
            level (str, optional): Select 'tag' or any property in your annotation collections with the prefix 'prop'.
            excluded_tags (list, optional): List of excluded tags. Defaults to None.
            plot_stats (bool, optional): Whether to return network stats. Defaults to True.
            save_as_gexf (bool, optional): If given any string as filename the network gets saved as Gephi file.
        """
        from gitma._network import Network

        nw = Network(
            annotation_collections=[self],
            character_distance=character_distance,
            included_tags=included_tags,
            excluded_tags=excluded_tags,
            level=level
        )
        nw.plot(plot_stats=plot_stats)
        if save_as_gexf:
            nw.to_gexf(filename=save_as_gexf)

    def to_pygamma_table(self) -> pd.DataFrame:
        """Returns the annotation collection's DataFrame in the format pygamma takes as input.

        Returns:
            pd.DataFrame: DataFrame with four columns: 'annotator', 'tag', 'start_point' and 'end_point'.
        """
        return self.df[['annotator', 'tag', 'start_point', 'end_point']]

    def tag_stats(
            self,
            tag_col: str = 'tag',
            stopwords: list = None,
            ranking: int = 10) -> pd.DataFrame:
        """Computes the following data for each tag in the annotation collection:
        - the count of annotations with a tag
        - the complete text span annotated with a tag
        - the average text span annotated with a tag
        - the n-most frequent token in the text span annotated with a tag

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

    def property_stats(self) -> pd.DataFrame:
        """Counts for each property the property values.

        Returns:
            pd.DataFrame: DataFrame with properties as index and property values as header.
        """
        return pd.DataFrame(
            {col: duplicate_rows(self.df, col)[col].value_counts(
            ) for col in self.df.columns if 'prop:' in col}
        ).T

    def get_annotation_by_tag(self, tag_name: str) -> List[Annotation]:
        """Creates list of all annotations with a given name.

        Args:
            tag_name (str): The searched tag's name.

        Args:
            tag_name (str): _description_

        Returns:
            List[Annotation]: List of annotations as gitma.Annotation objects.
        """
        return [
            annotation for annotation in self.annotations
            if annotation.tag.name == tag_name
            or annotation.tag.parent.name == tag_name
        ]

    def annotate_properties(self, tag: str, prop: str, value: list):
        """Set value for given property. This function uses the `gitma.Annotation.set_property_values()` method.

        Args:
            tag (str): The parent tag of the property.
            prop (str): The property to be annotated.
            value (list): The new property value.
        """
        for an in self.annotations:
            an.set_property_values(tag=tag, prop=prop, value=value)

    def rename_property_value(self, tag: str, prop: str, old_value: str, new_value: str):
        """Renames Property of all annotations with the given tag name.
        Replaces only the property value defined by the parameter `old_value`.

        Args:
            tag (str): The tag's name-
            prop (str): The property's name-
            old_value (str): The old property value that will be replaced.
            new_value (str): The new property value that will replace the old property value.
        """
        for an in self.annotations:
            an.modify_property_value(
                tag=tag, prop=prop, old_value=old_value, new_value=new_value)

    def delete_properties(self, tag: str, prop: str):
        """Deletes a property from all annotations with a given tag name.

        Args:
            tag (str): The annotations tag name.
            prop (str): The name of the property that will be removed.
        """
        for an in self.annotations:
            an.delete_property(tag=tag, prop=prop)
