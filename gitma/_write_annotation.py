import json
import os
import uuid

from datetime import datetime

from gitma.tag import Tag
from gitma.tagset import Tagset


def find_tagset_by_name(project, tagset_name: str):
    tagset = [tagset for tagset in project.tagsets if tagset.name == tagset_name][0]
    return tagset


def find_tag_by_name(tagset: Tagset, tag_name: str):
    tag = [tag for tag in tagset.tags if tag.name == tag_name][0]
    return tag


def get_new_annotation_uuid_and_path(annotation_collection_uuid: str):
    new_uuid = str(uuid.uuid1()).upper()
    new_path = f'collections/{annotation_collection_uuid}/annotations/CATMA_{new_uuid}'
    return new_uuid, new_path


def get_target_list(start_points: list, end_points: list, text_uuid: str) -> list:
    target_list = []

    for pair in zip(start_points, end_points):
        target_list.append({
            'source': text_uuid,
            'selector': {
                'start': pair[0],
                'end': pair[1],
                'type': 'TextPositionSelector'
            },
        })

    return target_list


def write_annotation_json(
        project,
        text_title: str,
        annotation_collection_name: str,
        tagset_name: str,
        tag_name: str,
        start_points: list,
        end_points: list,
        property_annotations: dict,
        author: str):
    """
    Function to write a new annotation into a given CatmaProject.
    Gets imported in the CatmaProject class and should only be used as a class method.

    Args:
        project (CatmaProject): A CatmaProject object.
        text_title (str): The text title.
        annotation_collection_name (str): The name of the target annotation collection.
        tagset_name (str): The tagset's name.
        tag_name (str): The tag's name.
        start_points (list): The start points of the annotation spans.
        end_points (list): The end points of the annotation spans.
        property_annotations (dict): A dictionary with property names mapped to value lists.
        author (str): The annotation's author.
    """

    cwd = os.getcwd()
    os.chdir(project.project_directory)

    text = project.text_dict[text_title]
    annotation_collection = project.ac_dict[annotation_collection_name]
    tagset = find_tagset_by_name(project, tagset_name)
    tag = find_tag_by_name(tagset, tag_name)

    new_annotation_uuid, new_annotation_relative_path = get_new_annotation_uuid_and_path(annotation_collection.uuid)

    tag_relative_path = tag.path[tag.path.index('/')+1:tag.path.rindex('/')]

    context_dict = {
        Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPTIMESTAMP: f'{tag_relative_path}/{Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPTIMESTAMP}',
        Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPAUTHOR: f'{tag_relative_path}/{Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPAUTHOR}'
    }

    property_dict = {
        'system': {
            # closest to what we're getting out of Java, except that a colon separator is added for the timezone offset
            # alternatively `.strftime('%Y-%m-%dT%H:%M:%S.%f%z')` omits the colon separator but has microsecond precision
            # TODO: check if this matters when parsed in Java (and how we're formatting there)
            Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPTIMESTAMP: [datetime.now().astimezone().isoformat(timespec='milliseconds')],
            Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPAUTHOR: [author]
        },
        'user': {}
    }

    for prop in tag.properties:
        context_dict[prop.uuid] = f'{tag_relative_path}/{prop.uuid}'

        if prop.name in property_annotations:
            property_dict['user'][prop.uuid] = property_annotations[prop.name] \
                if type(property_annotations[prop.name]) == list else [property_annotations[prop.name]]
        else:
            property_dict['user'][prop.uuid] = []

    context_dict['tag'] = 'https://www.catma.de/tag'
    context_dict['tagset'] = 'https://www.catma.de/tagset'

    json_dict = {
        '@context': 'http://www.w3.org/ns/anno.jsonld',
        'type': 'Annotation',
        'id': new_annotation_relative_path,
        'body': {
            '@context': context_dict,
            'tagset': f'tagsets/{tagset.uuid}',
            'tag': tag_relative_path,
            'properties': property_dict,
            'type': 'Dataset'
        },
        'target': {
            'items': get_target_list(start_points, end_points, text.uuid),
            'type': 'List'
        },
    }

    # TODO: determine appropriate page file and write annotation into it
    # write new annotation json file
    # with open(annotation_path, 'w', encoding='utf-8', newline='') as json_output:
    #     json_output.write(json.dumps(json_dict))

    os.chdir(cwd)
