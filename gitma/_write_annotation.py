import json
import os
from datetime import datetime
from gitma.tagset import Tagset


def find_tag_by_name(tagset: Tagset, tag_name: str):
    tag = [tag for tag in tagset.tags if tag.name == tag_name][0]
    return tag


def annotation_id(p_uuid, ac_uuid):
    import uuid
    uuid = str(uuid.uuid1()).upper()
    url = f'https://git.catma.de/{p_uuid}/collections/{ac_uuid}/annotations/CATMA_{uuid}.json'
    path = f'{p_uuid}/collections/{ac_uuid}/annotations/CATMA_{uuid}.json'
    return url, path


def get_target_list(start_points: list, end_points: list, text_uuid) -> list:
    target_list = []
    for pair in zip(start_points, end_points):
        target_list.append({
            "selector": {
                "end": pair[1],
                "start": pair[0],
                "type": "TextPositionSelector"
            },
            "source": text_uuid,
        })

    return target_list


def write_annotation_json(
        project,
        annotation_collection_name: str,
        tagset_name: str,
        text_title: str,
        tag_name: str,
        start_points: list,
        end_points: list,
        property_annotations: dict,
        author: str):
    """Function to write a new annotation into a given CatmaProject.
    Gets imported in the CatmaProject class and should only be used as a class method.

    Args:
        project (CatmaProject): A CatmaProject object.
        annotation_collection_name (str): The annotation collection's name
        tagset_name (str): The tagset's name
        text_title (str): The text title
        tag_name (str): The tag's name
        start_points (list): The annotation span start point
        end_points (list): The annotation span end point
        property_annotations (dict): dictionary with property annotations
        author (str): the annotation's author
    """

    cwd = os.getcwd()
    os.chdir(project.project_directory)

    ac = project.ac_dict[annotation_collection_name]
    tagset = project.tagset_dict[tagset_name]
    text = project.text_dict[text_title]
    tag = find_tag_by_name(
        tagset=tagset,
        tag_name=tag_name
    )

    annotation_url, annotation_path = annotation_id(
        project.uuid, ac.uuid)
    tag_directory = tag.file_directory
    tag_url = "https://git.catma.de/" + tag_directory

    context_dict = {
        tag.time_property: f'{tag_url}/{tag.time_property}',
        tag.user_property: f'{tag_url}/{tag.user_property}'
    }
    property_dict = {
        "system": {
            tag.time_property: [str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S'))],
            tag.user_property: [author]
        },
        "user": {}
    }

    for prop in tag.properties_list:
        context_dict[prop.uuid] = f'{tag_url}/{prop.uuid}'
        if prop.name in property_annotations:
            property_dict['user'][prop.uuid] = [
                property_annotations[prop.name]]
        else:
            property_dict['user'][prop.uuid] = []

    context_dict["tag"] = "https://app.catma.de/catma//tag"
    context_dict["tagset"] = "https://app.catma.de/catma//tagset"

    json_dict = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "body": {
            "@context": context_dict,
            "properties": property_dict,
            "tag": tag_url.replace('/propertydefs.json', ''),
            "tagset": f"https://git.catma.de/{project.uuid}/tagsets/{tagset.uuid}",
            "type": "Dataset"
        },
        "id": annotation_url,
        "target": {
            "items": get_target_list(start_points, end_points, text.uuid),
            "type": "List"
        },
        "type": "Annotation"
    }

    # write new annotation json file
    with open(annotation_path, 'w', encoding='utf-8', newline='') as json_output:
        json_output.write(json.dumps(json_dict))

    os.chdir(cwd)
