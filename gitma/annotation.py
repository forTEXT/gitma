import json
import os
import uuid
from typing import List
from datetime import datetime
from gitma.selector import Selector


def get_uuid(annotation_dict: dict) -> str:
    full_id = annotation_dict['id']
    filename = full_id.split('/')[-1]
    uuid = filename.replace('.json', '')
    return uuid


def get_start_point(annotation_dict: dict) -> int:
    return annotation_dict['target']['items'][0]['selector']['start']


def get_end_point(annotation_dict: dict) -> int:
    return annotation_dict['target']['items'][-1]['selector']['end']


def get_tagset_uuid(annotation_dict: dict) -> str:
    return annotation_dict['body']['tagset'].split('/')[-1]


def get_tag_uuid(annotation_dict: dict) -> str:
    return annotation_dict['body']['tag'].split('/')[-1]


def get_tag_directory(annotation_dict: dict) -> str:
    tag_url = annotation_dict['body']['tag']
    tag_directory = tag_url.replace(
        'https://git.catma.de/', '') + '/propertydefs.json'
    return tag_directory


def get_system_properties(annotation_dict: dict) -> str:
    return annotation_dict['body']['properties']['system']


def get_date(annotation_dict: dict) -> str:
    annotation_time = list(get_system_properties(annotation_dict).values())[0]
    annotation_date = annotation_time[0][:19]
    return datetime.strptime(annotation_date, '%Y-%m-%dT%H:%M:%S')


def get_author(annotation_dict: dict):
    return list(get_system_properties(annotation_dict).values())[1][0]


def get_user_properties(annotation_dict: dict) -> str:
    return annotation_dict['body']['properties']['user']


def get_annotated_text(json_data: str, plain_text: str) -> tuple:
    """
    Reads in annotation json as a dictionary and yield all text segments from plaintext within
    json_data['target'][items]
    """
    return (selector.covered_text for selector in build_selectors(json_data, plain_text))


def get_project_uuid(annotation_dict: dict) -> str:
    return annotation_dict['id'][21:-111]


def build_selectors(json_data: dict, plain_text: str):
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


def get_selector_items(start_points: list, end_points: list, source_document_uuid: str) -> list:
    """Creates list of selectors for annotation JSON file.
    Gets used when generating gold annotations.

    Args:
        start_points (list): Annotation Start Points
        end_points (list): Annotation End Points
        source_document_uuid (str): Document UUID in CATMA Project.
    Returns:
        list: List of selectors.
    """
    return [
        {
            "selector": {
                "end": end_points[index],
                "start": start_point,
                "type": "TextPositionSelector"
            },
            "source": source_document_uuid
        } for start_point, index in enumerate(start_points)
    ]


def search_for_startpoints(selector_list: List[Selector]) -> list:
    """Searches annotation selector item for start and end points-

    Args:
        selector_list (List[Selector]): _description_

    Returns:
        list: _description_
    """
    start_points = [selector.start for selector in selector_list]
    end_points = [selector.end for selector in selector_list]

    # filter redundant start points
    start_points = [
        start_point for start_point in start_points if start_point not in end_points]
    end_points = [
        end_point for end_point in end_points if end_point not in start_points]

    return list(zip(start_points, end_points))


def numeric_property_values_to_int(prop_dict: dict) -> dict:
    """Transforms numeric property values to integers.

    Args:
        prop_dict (dict): Dictionary with Property names as keys and values as list.

    Returns:
        dict: Dictionary with Property names as keys and values as list.
    """
    output_dict = {}
    for prop in prop_dict:
        values = []
        for value in prop_dict[prop]:
            if value.isnumeric():
                values.append(int(value))
            else:
                values.append(value)
        output_dict[prop] = values
    return output_dict


class Annotation:
    """Class which represents a CATMA annotation.

    Args:
        directory (str): The annotations directory within the project clone.
        plain_text (str): The plain text annotated by the annotation.
        catma_project (_type_): The parent CatmaProject .
        context (int, optional): Size of the context that gets included in the\
            data frame representation of annotation collections. Defaults to 50.

    Raises:
        FileNotFoundError: If the directory of the annotation's JSON file does not exists.
    """

    def __init__(self, directory: str, plain_text: str, catma_project, context: int = 50):
        self.project_direcory = catma_project.project_directory
        
        #: The annotation's directory.
        self.directory = directory
        try:
            with open(directory, 'r', encoding='utf-8') as ip:  # load annotation json file as dict
                #: The annotation's data as dictionary.
                self.data: dict = json.load(ip)
        except FileNotFoundError:
            raise FileNotFoundError(
                f'The Annotation in this directory could not be found:\n{self.directory}\n\
                    --> Make sure the CATMA Project clone did work properly.')

        #: The annotation's uuid.
        self.uuid: str = get_uuid(self.data)
        
        #: The date the annotation has been created.
        self.date: str = get_date(self.data)

        #: The annotation's author.
        self.author: str = get_author(self.data)

        #: The annotation's start point (character index) in the plain text.
        self.start_point: int = get_start_point(self.data)

        #: The annotation's end point (character index) in the plain text.
        self.end_point: int = get_end_point(self.data)

        #: The annotated text span.
        self.text: str = ' '.join(
            list(get_annotated_text(self.data, plain_text))
        )

        #: The annotation's left context.
        self.pretext: str = plain_text[
            self.start_point - context: self.start_point
        ]

        #: The annotation's right context.
        self.posttext: str = plain_text[self.end_point: self.end_point + context]

        #: The annotation's selectors as a list of gitma.Selector
        self.selectors: List[Selector] = list(
            build_selectors(self.data, plain_text))

        tagset_uuid = get_tagset_uuid(self.data)
        tag_uuid = get_tag_uuid(self.data)

        #: The annotation's tag as a gitma.Tag object.
        self.tag = catma_project.tagset_dict[tagset_uuid].tag_dict[tag_uuid]

        user_properties = get_user_properties(self.data)

        #: The annotation's properties as a dictionary with property names as keys
        #: and the property values as list.
        self.properties = {
            self.tag.properties_data[prop]['name']: user_properties[prop] for prop in user_properties
        }

    def __len__(self) -> int:
        return self.end_point - self.start_point

    def __lt__(self, other):
        return self.start_point < other.start_point

    def __bool__(self) -> bool:
        return True

    def __repr__(self):
        return f"Annotation(Author: {self.author}, Tag: {self.tag}, Properties: {self.properties}, Start Point: {self.start_point}, )"

    def to_dict(self) -> dict:
        """Returns annotation core elements as keys

        Returns:
            dict: Annotation text, the tag, the properties as dictionary, start point and end point.
        """
        return {
            'annotation': self.text,
            'tag': self.tag.name,
            'properties': numeric_property_values_to_int(self.properties),
            'spans': search_for_startpoints(self.selectors)
        }

    def modify_start_point(self, new_start_point: int, relative: bool = False) -> None:
        """Rewrites annotation json file with new start point.

        Args:
            new_start_point (int): New end point.
            relative (bool, optional): If true the `new_start_point` parameter is interpreted as relative to the old end point.\
                Defaults to False.
        """
        if relative:
            new_start_point = self.start_point + new_start_point
        self.data['target']['items'][0]['selector']['start'] = new_start_point
        with open(self.project_direcory + self.directory, 'w', encoding='utf-8') as json_output:
            json_output.write(json.dumps(self.data))

    def modify_end_point(self, new_end_point: int, relative: bool = False) -> None:
        """Rewrites annotation json file with new end point.

        Args:
            new_end_point (int): New end point.
            relative (bool, optional): If true the `new_end_point` parameter is interpreted as relative to the old end point.\
                Defaults to False.
        """
        if relative:
            new_end_point = self.end_point + new_end_point
        self.data['target']['items'][-1]['selector']['end'] = new_end_point
        with open(self.project_direcory + self.directory, 'w', encoding='utf-8') as json_output:
            json_output.write(json.dumps(self.data))
    
    def modify_property_value(self, tag: str, prop: str, old_value: str, new_value: str) -> None:
        """Modifies property values if the annotation is tagged by defined tag and property
        by rewriting the annotation's JSON file.

        Args:
            tag (str): The annotations tag.
            prop (str): The tag property to be modified.
            old_value (str): The old property value.
            new_value (str): The new property value.
        """
        if self.tag.name == tag and prop in self.properties:
            # open annotation json file
            with open(self.directory) as json_input:
                json_dict = json.load(json_input)

            prop_uuid = self.tag.properties_dict[prop].uuid

            # set new property value
            values = json_dict["body"]['properties']['user'][prop_uuid]
            for index, value in enumerate(values):
                if value == old_value:
                    values[index] = new_value
            json_dict["body"]['properties']['user'][prop_uuid] = values

            # write new annotation json file
            with open(self.directory, 'w') as json_output:
                json_output.write(json.dumps(json_dict))

    def set_property_values(self, tag: str, prop: str, value: list) -> None:
        """Set property value of the given tag.

        Args:
            tag (str): The tag's name.
            prop (str): The property's name.
            value (list): The list of new property values.
        """
        if self.tag.name == tag and prop in self.properties:
            # open annotation json file
            with open(self.directory) as json_input:
                json_dict = json.load(json_input)

            prop_uuid = self.tag.properties_dict[prop].uuid

            # set new property value
            json_dict["body"]['properties']['user'][prop_uuid] = value

            # write new annotation json file
            with open(self.directory, 'w') as json_output:
                json_output.write(json.dumps(json_dict))

    def delete_property(self, tag: str, prop: str) -> None:
        """Deletes property if the annotation is tagged by defined tag and property.

        Args:
            tag (str): The tag with the property to be deleted.
            prop (str): The property to be deleted.
        """
        if self.tag.name == tag and prop in self.properties:
            # open annotation json file
            with open(self.directory) as json_input:
                json_dict = json.load(json_input)

            prop_uuid = self.tag.properties_dict[prop].uuid

            # delete property
            json_dict["body"]['properties']['user'].pop(prop_uuid)

            # write new annotation json file
            with open(self.directory, 'w') as json_output:
                json_output.write(json.dumps(json_dict))

    def copy(
            self,
            annotation_collection: str,
            compare_annotation=None,
            new_start_points: list = None,
            new_end_points: list = None) -> None:
        """Copies the Annotation into another Annotation Collection by creating a new Annotation UUID.

        Args:
            annotation_collection (str): The annotation collection UUID to get the directory the annotation should be copied to.
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

        new_directory = f'collections/{annotation_collection}/annotations/{new_uuid}.json'
        with open(new_directory, 'w') as json_output:
            json_output.write(json.dumps(new_annotation_data))

    def remove(self) -> None:
        """Removes the annotation from the annotation collection.
        """
        os.remove(self.directory)
