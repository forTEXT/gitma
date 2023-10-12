import json
import os
import uuid

from datetime import datetime

from gitma.tag import Tag
from gitma.tagset import Tagset


# the value of this constant should match the value in the relevant CATMA instance's settings
MAX_ANNOTATION_PAGE_FILE_SIZE_BYTES = 200000


def find_tagset_by_name(project, tagset_name: str):
    tagset = [tagset for tagset in project.tagsets if tagset.name == tagset_name][0]
    return tagset


def find_tag_by_name(tagset: Tagset, tag_name: str):
    tag = [tag for tag in tagset.tags if tag.name == tag_name][0]
    return tag


def get_new_annotation_uuid_and_path(annotation_collection_uuid: str):
    new_uuid = f'CATMA_{str(uuid.uuid1()).upper()}'
    new_path = f'collections/{annotation_collection_uuid}/annotations/{new_uuid}'
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


def _get_current_page_file_path(annotations_base_path: str, username: str = 'GitMA_DummyUser', force_new: bool = False) -> str:
    pages = []
    for file in os.listdir(annotations_base_path):
        if file.lower().endswith('.json') and file[0:file.rindex('_')] == username:
            pages.append(file)

    page_no = 0

    if len(pages) > 0:
        pages.sort(key=lambda page: page[page.rindex('_')+1:])
        page_no = len(pages)-1
        last_page = pages[-1]

        if os.path.getsize(f'{annotations_base_path}{last_page}') >= MAX_ANNOTATION_PAGE_FILE_SIZE_BYTES or force_new:
            page_no += 1

    return f'{annotations_base_path}{username}_{page_no}.json'


def write_annotation_json(
        project,
        text_title: str,
        annotation_collection_name: str,
        tagset_name: str,
        tag_name: str,
        start_points: list,
        end_points: list,
        property_annotations: dict,
        author: str,
        uuid_override: str = None,
        timestamp_override: str = None) -> str:
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
        uuid_override (str): If supplied, overrides the internally generated annotation UUID for testing purposes.
        timestamp_override (str): If supplied, overrides the internally generated annotation timestamp for testing purposes.

    Returns:
        str: The project-relative path of the page file that the annotation was written to.
    """

    cwd = os.getcwd()
    os.chdir(project.project_directory + project.uuid)

    text = project.text_dict[text_title]
    annotation_collection = project.ac_dict[annotation_collection_name]
    tagset = find_tagset_by_name(project, tagset_name)
    tag = find_tag_by_name(tagset, tag_name)

    # NB: new_annotation_relative_path is NOT a file path and is only used in the JSON-LD representation of the annotation
    new_annotation_uuid, new_annotation_relative_path = get_new_annotation_uuid_and_path(annotation_collection.uuid)
    if uuid_override is not None:
        new_annotation_relative_path = new_annotation_relative_path.replace(new_annotation_uuid, uuid_override)
        new_annotation_uuid = uuid_override

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
    if timestamp_override is not None:
        property_dict['system'][Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPTIMESTAMP] = [timestamp_override]

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

    # the below should be roughly equivalent to what GitAnnotationCollectionHandler.createTagInstances does in CATMA
    annotation_json = json.dumps([json_dict], indent=2)
    annotation_byte_size = len(annotation_json.encode('utf-8'))

    annotations_base_path = f'collections/{annotation_collection.uuid}/annotations/'
    current_page_file_path = _get_current_page_file_path(annotations_base_path)  # <annotations_base_path><username>_<pagenumber>.json

    if os.path.isfile(current_page_file_path) and os.path.getsize(current_page_file_path) + annotation_byte_size > MAX_ANNOTATION_PAGE_FILE_SIZE_BYTES:
        # the current page file doesn't have enough space to write the new annotation, we need to create a new one
        current_page_file_path = _get_current_page_file_path(annotations_base_path, force_new=True)

    with open(current_page_file_path, 'r+b' if os.path.isfile(current_page_file_path) else 'xb') as current_page_file:
        file_size = current_page_file.seek(0, os.SEEK_END)
        current_page_file.seek(0, os.SEEK_SET)

        # condition is '> 2' because a page file can contain only "[]" (if all the annotations that the page contains are deleted)
        if file_size > 2:
            # replace the opening list bracket of the serialized annotation to be written with a comma
            # in preparation for appending the annotation to the list of existing annotations in the page file
            annotation_json = ',' + annotation_json[1:]

            # seek so that the closing list bracket and the preceding newline in the page file will be overwritten
            # with the new annotation + a new closing bracket
            current_page_file.seek(-2, os.SEEK_END)

        current_page_file.write(annotation_json.encode('utf-8'))

    os.chdir(cwd)

    return current_page_file_path
