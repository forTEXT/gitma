import json
from datetime import datetime
from catma_gitlab.tag_class import Tag


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


def get_annotated_text(json_data, plain_text):
    """
    Reads in annotation json as a dictionary and yield all text segments from plaintext within
    json_data['target'][items]
    """
    for item in json_data['target']['items']:
        yield plain_text[item['selector']['start']: item['selector']['end']]


class Annotation:
    def __init__(self, direction: str, plain_text: str, context=20):
        """
        Class which represents a CATMA annotation.
        :param direction: the annotations direction
        :param plain_text: annotated text as CATMA document
        """
        self.direction = direction
        with open(direction, 'r', encoding='utf-8') as ip:  # load annotation json file as dict
            self.data = json.load(ip)

        self.date = get_date(self.data)
        self.author = get_author(self.data)
        self.start_point = get_start_point(self.data)
        self.end_point = get_end_point(self.data)
        self.text = ' '.join(list(get_annotated_text(self.data, plain_text)))
        self.pretext = plain_text[self.start_point - context: self.start_point]
        self.posttext = plain_text[self.end_point: self.end_point + context]

        tag_direction = get_tag_direction(self.data)
        self.tag = Tag(tag_direction)

        user_properties = get_user_properties(self.data)
        self.properties = {
            self.tag.properties[prop]['name']: user_properties[prop] for prop in user_properties
        }

    def modify_property_value(self, tag: str, prop: str, old_value: str, new_value: str):
        """
        Modifies Property Values if the annotation is tagged by defined Tag and Property.
        """
        if self.tag.name == tag and prop in self.properties:
            # open annotation json file
            with open(self.direction) as json_input:
                json_dict = json.load(json_input)

            prop_uuid = self.tag.properties_dict[prop].uuid

            # set new property value
            values = json_dict["body"]['properties']['user'][prop_uuid]
            for index, value in enumerate(values):
                if value == old_value:
                    values[index] = new_value
            json_dict["body"]['properties']['user'][prop_uuid] = values

            # write new annotation json file
            with open(self.direction, 'w') as json_output:
                json_output.write(json.dumps(json_dict))

    def set_property_values(self, tag: str, prop: str, value: list):
        """
        Set Property Values if the annotation is tagged by defined Tag and Property.
        """
        if self.tag.name == tag:
            # open annotation json file
            with open(self.direction) as json_input:
                json_dict = json.load(json_input)

            prop_uuid = self.tag.properties_dict[prop].uuid

            # set new property value
            json_dict["body"]['properties']['user'][prop_uuid] = value

            # write new annotation json file
            with open(self.direction, 'w') as json_output:
                json_output.write(json.dumps(json_dict))

    def delete_property(self, tag: str, prop: str):
        """
        Delete Property Values if the annotation is tagged by defined Tag and Property.
        """
        if self.tag.name == tag and prop in self.properties:
            # open annotation json file
            with open(self.direction) as json_input:
                json_dict = json.load(json_input)

            prop_uuid = self.tag.properties_dict[prop].uuid

            # delete property
            json_dict["body"]['properties']['user'].pop(prop_uuid)

            # write new annotation json file
            with open(self.direction, 'w') as json_output:
                json_output.write(json.dumps(json_dict))