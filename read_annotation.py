from datetime import datetime


def get_start_point(annotation_dict):
    return annotation_dict['target']['items'][0]['selector']['start']


def get_end_point(annotation_dict):
    return annotation_dict['target']['items'][-1]['selector']['end']


def get_tag_direction(annotation_dict):
    tag_url = annotation_dict['body']['tag']
    tag_direction = tag_url.replace('https://git.catma.de/', '') + '/propertydefs.json'
    return tag_direction


def get_system_properties(annotation_dict):
    return annotation_dict['body']['properties']['system']


def get_date(annotation_dict):
    annotation_time = list(get_system_properties(annotation_dict).values())[0]
    annotation_date = annotation_time[0][:19]
    return datetime.strptime(annotation_date, '%Y-%m-%dT%H:%M:%S')


def get_author(annotation_dict):
    return list(get_system_properties(annotation_dict).values())[1][0]


def get_user_properties(annotation_dict):
    return annotation_dict['body']['properties']['user']