import json
from copy import deepcopy
from datetime import datetime
from typing import List

from gitma import Tag
from gitma._write_annotation import write_annotation_json
from gitma.selector import Selector


def get_uuid(annotation_dict: dict) -> str:
    return annotation_dict['id'].split('/')[-1]


def get_start_point(annotation_dict: dict) -> int:
    return annotation_dict['target']['items'][0]['selector']['start']


def get_end_point(annotation_dict: dict) -> int:
    return annotation_dict['target']['items'][-1]['selector']['end']


def get_tagset_uuid(annotation_dict: dict) -> str:
    return annotation_dict['body']['tagset'].split('/')[-1]


def get_tag_uuid(annotation_dict: dict) -> str:
    return annotation_dict['body']['tag'].split('/')[-1]


def get_system_properties(annotation_dict: dict) -> str:
    return annotation_dict['body']['properties']['system']


def get_date(annotation_dict: dict) -> datetime:
    annotation_iso_datetime = get_system_properties(annotation_dict)[Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPTIMESTAMP][0]
    # not using datetime.fromisoformat here because it doesn't handle a timezone component without a colon separator
    try:
        timestamp = datetime.strptime(annotation_iso_datetime, '%Y-%m-%dT%H:%M:%S.%f%z')
    except ValueError:
        # older GitMA versions wrote the timestamp without a timezone component, which will cause the above to fail
        # as a limited amount of annotation were created using these versions we assume CEST and append its offset to allow parsing to succeed
        # if you used older GitMA versions to create annotation and an accurate timestamp is important to you, consider correcting the source data
        # or modify the offset below
        timestamp = datetime.strptime(annotation_iso_datetime + '+02:00', '%Y-%m-%dT%H:%M:%S%z')
    return timestamp


def get_author(annotation_dict: dict):
    return get_system_properties(annotation_dict)[Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPAUTHOR][0]


def get_user_properties(annotation_dict: dict) -> str:
    return annotation_dict['body']['properties']['user']


def get_annotated_text(json_data: str, plain_text: str) -> tuple:
    """
    Reads in annotation json as a dictionary and yield all text segments from plaintext within
    json_data['target'][items]
    """
    return (selector.covered_text for selector in build_selectors(json_data, plain_text))


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
    Gets used when generating gold annotation.

    Args:
        start_points (list): annotation start points
        end_points (list): annotation end points
        source_document_uuid (str): document UUID in CATMA project.
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


def merge_adjacent_spans_forming_continuous_logical_span(selector_list: List[Selector]) -> list:
    """Merges separate spans that cover a continuous logical span of text, e.g.: [(0, 17), (17, 35)] -> [(0, 35)]

    Args:
        selector_list (List[Selector]): _description_

    Returns:
        list: _description_
    """
    start_points = [selector.start for selector in selector_list]
    end_points = [selector.end for selector in selector_list]

    start_points_filtered = [
        start_point for start_point in start_points if start_point not in end_points]
    end_points_filtered = [
        end_point for end_point in end_points if end_point not in start_points]

    return list(zip(start_points_filtered, end_points_filtered))


def numeric_property_values_to_int(prop_dict: dict) -> dict:
    """Transforms numeric property value to integers.

    Args:
        prop_dict (dict): Dictionary with Property names as keys and value as list.

    Returns:
        dict: Dictionary with Property names as keys and value as list.
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
        annotation_data (dict): The annotation data as a dict.
        page_file_path (str): The path of the JSON annotation page file from which annotation_data was loaded.
        plain_text (str): The plain text annotated by the annotation.
        project (CatmaProject): The parent CatmaProject.
        context (int, optional): Size of the context that gets included in the\
            data frame representation of annotation collection. Defaults to 50.
    """
    def __init__(self, annotation_data: dict, page_file_path: str, plain_text: str, project, context: int = 50):
        #: The parent CatmaProject
        self.project = project
        
        #: The annotation in its json representation as a dict
        self.data: dict = annotation_data

        #: The path of the annotation page file that this annotation was loaded from
        self.page_file_path: str = page_file_path

        #: The annotation's uuid.
        self.uuid: str = get_uuid(self.data)
        
        #: The date & time the annotation was created.
        self.date: datetime = get_date(self.data)

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
        self.tag = project.tagset_dict[tagset_uuid].tag_dict[tag_uuid]

        user_properties = get_user_properties(self.data)

        #: The annotation's properties as a dictionary with property names as keys
        #: and the property value as list.
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
        return f"Annotation(Author: {self.author}, Tag: {self.tag}, Properties: {self.properties}, Start Point: {self.start_point}, End Point: {self.end_point}, Text: {self.text}, )"

    def to_dict(self) -> dict:
        """Returns annotation core elements as keys

        Returns:
            dict: Annotation text, the tag, the properties as dictionary, start point and end point.
        """
        return {
            'annotation': self.text,
            'tag': self.tag.name,
            'properties': numeric_property_values_to_int(self.properties),
            'spans': merge_adjacent_spans_forming_continuous_logical_span(self.selectors)
        }
    
    
    def remove(self) -> None:
        """Removes the annotation from the annotation collection's json file.
        """
        with open(self.page_file_path, 'r', encoding='utf-8', newline='') as ac_input:
            ac_data = json.load(ac_input)

        for item in ac_data:
            if get_uuid(item) == self.uuid:
                ac_data.remove(self.data)

        with open(self.page_file_path, 'w', encoding='utf-8', newline='') as ac_output:
            ac_output.write(json.dumps(ac_data))
    
    def modify_annotation(self) -> None:
        """Overwrite annotation collection's json file with the updated
        annotation data: `self.data`.
        """
        with open(self.page_file_path, 'r', encoding='utf-8', newline='') as ac_input:
            ac_data = json.load(ac_input)

        for index, item in enumerate(ac_data):
            if get_uuid(item) == self.uuid:
                ac_data[index] = self.data

        with open(self.page_file_path, 'w', encoding='utf-8', newline='') as ac_output:
            ac_output.write(json.dumps(ac_data))

    def modify_start_point(self, new_start_point: int, relative: bool = False) -> None:
        """Rewrites annotation json file with new start point.

        Args:
            new_start_point (int): New start point.
            relative (bool, optional): If true the `new_start_point` parameter is interpreted as relative to the old start point.\
                Defaults to False.
        """
        if relative:
            new_start_point = self.start_point + new_start_point
        self.data['target']['items'][0]['selector']['start'] = new_start_point
        self.modify_annotation()

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
        self.modify_annotation()
    
    def modify_property_value(self, tag: str, prop: str, old_value: str, new_value: str) -> None:
        """Modifies property value if the annotation is tagged by defined tag and property
        by rewriting the annotation's JSON file.

        Args:
            tag (str): The annotation's tag.
            prop (str): The tag property to be modified.
            old_value (str): The old property value.
            new_value (str): The new property value.
        """
        if self.tag.name == tag and prop in self.properties:
            prop_uuid = self.tag.properties_dict[prop].uuid

            # set new property value
            values = self.data["body"]['properties']['user'][prop_uuid]
            for index, value in enumerate(values):
                if value == old_value:
                    values[index] = new_value
            self.data["body"]['properties']['user'][prop_uuid] = values

            self.modify_annotation()

    def set_property_values(self, tag: str, prop: str, value: list) -> None:
        """Set property value of the given tag.

        Args:
            tag (str): The tag's name.
            prop (str): The property's name.
            value (list): The list of new property value.
        """
        if self.tag.name == tag and prop in self.properties:

            prop_uuid = self.tag.properties_dict[prop].uuid

            # set new property value
            self.data["body"]['properties']['user'][prop_uuid] = value

            self.modify_annotation()

    def delete_property(self, tag: str, prop: str) -> None:
        """Deletes property if the annotation is tagged by defined tag and property.

        Args:
            tag (str): The tag with the property to be deleted.
            prop (str): The property to be deleted.
        """
        if self.tag.name == tag and prop in self.properties:
            prop_uuid = self.tag.properties_dict[prop].uuid

            # delete property
            self.data["body"]['properties']['user'].pop(prop_uuid)

            self.modify_annotation()

    def _copy(
            self,
            annotation_collection_name: str,
            compare_annotation: 'Annotation' = None,
            uuid_override: str = None,
            timestamp_override: str = None
    ) -> str:
        new_properties = deepcopy(self.properties)

        # remove property value from new_properties unless we have a compare_annotation whose corresponding property value match
        for property_name in new_properties.keys():
            if compare_annotation is None or new_properties.get(property_name) != compare_annotation.properties.get(property_name, []):
                new_properties[property_name] = []

        document_uuid = self.data['target']['items'][0]['source']
        document_title = [text for text in self.project.texts if text.uuid == document_uuid][0].title

        start_points = [item['selector']['start'] for item in self.data['target']['items']]
        end_points = [item['selector']['end'] for item in self.data['target']['items']]

        return write_annotation_json(
            self.project,
            document_title,
            annotation_collection_name,
            self.project.tagset_dict[get_tagset_uuid(self.data)].name,
            self.tag.name,
            start_points,
            end_points,
            new_properties,
            'auto_gold',
            uuid_override=uuid_override,
            timestamp_override=timestamp_override
        )

    def copy(
            self,
            annotation_collection_name: str,
            compare_annotation: 'Annotation' = None
    ) -> None:
        """Copies this annotation into another annotation collection, giving it a new UUID.

        Args:
            annotation_collection_name (str): The name of the annotation collection that the annotation should be copied to.
            compare_annotation (Annotation, optional): An annotation to compare property value (for gold annotation). Defaults to None.
        """
        self._copy(annotation_collection_name, compare_annotation)
