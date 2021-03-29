import pandas as pd
import os
import json


def test_empty_ac(root_direction, ac_id):
    if os.path.isdir(
            f'{root_direction}/collections/{ac_id}/annotations'):
        return True


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


def get_tag_collocations(ac, collocation_span: int):
    tag_names = [t.name for t in ac.tags]
    collocation_dict = {tag: {t: 0 for t in tag_names if t != tag} for tag in tag_names}
    for index, row in ac.df.iterrows():
        max_sp = row['start_point'] + collocation_span
        min_sp = row['start_point'] - collocation_span
        col_df = ac.df[(min_sp < ac.df['start_point']) & (ac.df['start_point'] < max_sp)]
        for tag in col_df['tag']:
            if tag in collocation_dict[row['tag']]:
                collocation_dict[row['tag']][tag] += 1

    return pd.DataFrame(collocation_dict)


def get_collocation_network(collocation_df: pd.DataFrame, gexf_file: str):
    """
    Returns Gephi file for tag collocation data frame created by get_tag_collocation.
    """
    import networkx as nx

    nodes = [
        (c, {'size': collocation_df[c].sum()}) for c in collocation_df.index
    ]

    edges = []
    for index, row in collocation_df.iterrows():
        for col in list(collocation_df):
            if index != col:
                edges.append((index, col, row[col]))

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_weighted_edges_from(edges)
    nx.write_gexf(G, f'../{gexf_file}.gexf')


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
