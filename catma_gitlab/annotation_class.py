import json
import uuid
from typing import List
from datetime import datetime
from catma_gitlab.tag_class import Tag
from catma_gitlab.selector_class import Selector


def get_start_point(annotation_dict):
    return annotation_dict['target']['items'][0]['selector']['start']


def get_end_point(annotation_dict):
    return annotation_dict['target']['items'][-1]['selector']['end']


def get_tag_direction(annotation_dict):
    tag_url = annotation_dict['body']['tag']
    tag_direction = tag_url.replace(
        'https://git.catma.de/', '') + '/propertydefs.json'
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
    return (selector.covered_text for selector in build_selectors(json_data, plain_text))


def get_project_uuid(annotation_dict):
    return annotation_dict['id'][21:-111]


def build_selectors(json_data, plain_text):
    """
    Yields `Segment`s covered by the annotation described in in `json_data`.

    :param json_data: Raw json data describing the `Annotation`
    :param plain_text: Plain text of the document targeted by the `Annotation` in `json_data`.
    """
    for item in json_data['target']['items']:
        yield Selector(item['selector']['start'], item['selector']['end'], plain_text)


def get_annotation_segments(json_data: dict) -> bool:
    start_points = [
        int(item['selector']['start']) for item in json_data['target']['items']
    ]
    end_points = [
        int(item['selector']['end']) for item in json_data['target']['items']
    ]

    filtered_start_points = [
        start_point for start_point in start_points if start_point not in end_points
    ]

    return len(filtered_start_points)


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

        self.date: str = get_date(self.data)
        self.author: str = get_author(self.data)
        self.start_point: int = get_start_point(self.data)
        self.end_point: int = get_end_point(self.data)
        self.text: str = ' '.join(
            list(get_annotated_text(self.data, plain_text)))
        self.pretext: str = plain_text[self.start_point -
                                       context: self.start_point]
        self.posttext: str = plain_text[self.end_point: self.end_point + context]
        self.selectors: List[Selector] = list(
            build_selectors(self.data, plain_text))

        tag_direction = get_tag_direction(self.data)
        self.tag = Tag(tag_direction)

        user_properties = get_user_properties(self.data)
        self.properties = {
            self.tag.properties[prop]['name']: user_properties[prop] for prop in user_properties
        }

    def __len__(self) -> int:
        return self.end_point - self.start_point

    def __bool__(self) -> True:
        return True

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

    def copy(
            self,
            annotation_collection: str,
            compare_annotation=None) -> None:
        """Copies the Annotation into another Annotation Collection by creating a new Annotation UUID.

        Args:
            annotation_collection (str): The annotation collection UUID to get the direction the annotation should be copied to.
            include_property_value (bool, optional): Whether the Property Values should be copied too. Defaults to True.
            compare_annotation (Annotation, optional): An Annotation to compare Property Values. (For Gold Annotations). Defaults to True.
        """

        new_uuid = "CATMA_" + str(uuid.uuid1()).upper()

        id_prefix = self.data['id'][:-98]
        new_id = f"{id_prefix}{annotation_collection}/annotations/{new_uuid}"

        new_annotation_data = self.data
        new_annotation_data['id'] = new_id

        sys_props = list(self.data['body']['properties']['system'])
        # new annotation time property value
        new_annotation_data['body']['properties']['system'][sys_props[0]] = [
            str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S'))
        ]
        # new annotation author name
        new_annotation_data['body']['properties']['system'][sys_props[1]] = [
            'auto_gold'
        ]

        # copy all property values which are matching the compare annotation
        if compare_annotation:
            for prop in self.data['body']['properties']['user']:
                # test for each user Property if the Property Values are matching
                if self.data['body']['properties']['user'][prop] == compare_annotation.data['body']['properties']['user'][prop]:
                    new_annotation_data['body']['properties']['user'][prop] = self.data['body']['properties']['user'][prop]
                else:
                    new_annotation_data['body']['properties']['user'][prop] = [
                    ]
        else:
            for prop in self.data['body']['properties']['user']:
                # remove all Property Values
                new_annotation_data['body']['properties']['user'][prop] = []

        new_direction = f'collections/{annotation_collection}/annotations/{new_uuid}.json'
        with open(new_direction, 'w') as json_output:
            json_output.write(json.dumps(new_annotation_data))
