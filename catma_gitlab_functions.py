from catma_gitlab.catma_gitlab_classes import *


def get_first_and_last_text_pointer(annotation_json_dict):
    """
    A function that takes a CATMA annotation dict and returns the first and last text pointer
    to get the annotated string.
    """
    return [
        annotation_json_dict['target']['items'][0]['selector']['start'],
        annotation_json_dict['target']['items'][-1]['selector']['end']
    ]


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


def duplicate_rows(df, property_row):
    def duplicate_generator(df):
        for index, row in df.iterrows():
            if len(row[property_row]) > 1:
                for item in row[property_row]:
                    row_dict = dict(row)
                    row_dict[property_row] = item
                    yield row_dict
            else:
                row_dict = dict(row)
                if len(row[property_row]) > 0:
                    row_dict[property_row] = row[property_row][0]
                    yield dict(row_dict)
                else:
                    row_dict[property_row] = 'nan'
                    yield dict(row_dict)

    df_new = pd.DataFrame(list(duplicate_generator(df)))
    return df_new

