import pandas as pd
import os
import json


def test_empty_ac(root_direction, ac_id):
    if os.path.isdir(
            f'{root_direction}/collections/{ac_id}/annotations'):
        return True


def get_annotated_text(json_data, plain_text):
    """
    Reads in annotation json as a dictionary and yield all text segments from plaintext within
    json_data['target'][items]
    """
    for item in json_data['target']['items']:
        yield plain_text[item['selector']['start']: item['selector']['end']]


def split_property_dict_to_column(ac_df):
    """
    Creates pandas DataFrame columns for each property in annotation collection.
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


def duplicate_rows(df, property_col):
    """
    Duplicates rows in AnnotationCollection dataframe if multiple property values exist in defined porperty column.
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

    df_new = pd.DataFrame(list(duplicate_generator(df)))
    return df_new


def test_intrinsic(project_uuid: str, direction: str, test_positive=True):
    """
    This Function tests if a Catma Annotation Collection is intrinsic markup.
    Returns True if so.
    :param project_uuid: CATMA gitlab root project uuids
    :param direction: annotation collection direction
    :param test_positive: what should be returned if it is intrinsic markup
    """
    with open(f'{project_uuid}/collections/{direction}/header.json', 'r') as header_input:
        header_dict = json.load(header_input)

    if header_dict['name'] == 'Intrinsic Markup':
        return test_positive
