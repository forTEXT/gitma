import json
from datetime import datetime
# import catma_gitlab.catma_gitlabes as cgc import Tag, Tagset, Text, AnnotationCollection


def find_tag_by_name(tagset, tag_name: str):
    tag = [tag for tag in tagset.tag_list if tag.name == tag_name][0]
    return tag


def annotation_id(p_uuid, ac_uuid):
    import uuid
    uuid = str(uuid.uuid1()).upper()
    url = f'https://git.catma.de/{p_uuid}/collections/{ac_uuid}/annotations/CATMA_{uuid}.json'
    directory = f'{p_uuid}/collections/{ac_uuid}/annotations/CATMA_{uuid}.json'
    return url, directory


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
        project_uuid: str,
        annotation_collection,
        tagset,
        text,
        start_points: list,
        end_points: list,
        tag,
        property_annotations: dict,
        author: str):

    annotation_url, annotation_directory = annotation_id(
        project_uuid, annotation_collection.uuid)
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
            "tagset": f"https://git.catma.de/{project_uuid}/tagsets/{tagset.uuid}",
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
    with open(annotation_directory, 'w') as json_output:
        json_output.write(json.dumps(json_dict))
