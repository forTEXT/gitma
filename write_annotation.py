from catma_gitlab.catma_gitlab_classes import Tag
import uuid
import json
from datetime import datetime


def annotation_id(p_uuid, ac_uuid):
    return f'https://git.catma.de/{p_uuid}/collections/{ac_uuid}/C_{str(uuid.uuid1())}.json'


def write_annotation_json(
        project_uuid: str,
        annotation_collection_uuid: str,
        tagset_uuid: str,
        start_point: int,
        end_point: int,
        tag_direction: str,
        property_annotations: dict,
        author: str):

    annotation_file = annotation_id(project_uuid, annotation_collection_uuid)
    tag = Tag(tag_direction)
    tag_url = "https://git.catma.de/" + tag_direction

    context_dict = {}
    property_dict = {
        "system": {
            "CATMA_54A5F93F-5333-3F0D-92F7-7BD5930DB9E6": [str(datetime.today().strftime('%Y-%m-%dT%H:%M:%S'))],
            "CATMA_AB27F1D4-303A-3622-BB2C-72C310D0C1BF": [author]
        }
    }

    for prop in tag.properties_list:
        context_dict[prop.uuid] = f'https://git.catma.de/{tag.file_direction}/{prop.uuid}'
        if prop.name in property_annotations:
            property_dict[prop.name] = property_annotations[prop.name]
        else:
            property_dict[prop.name] = []


    context_dict["tag"] = "https://app.catma.de/catma//tag"
    context_dict["tagset"] = "https://app.catma.de/catma//tagset"

    json_dict = {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "body": {
            "@context": context_dict,
            "properties": property_dict,
            "tag": tag_url,
            "tagset": f"https://git.catma.de/{project_uuid}/tagsets/{tagset_uuid}",
            "type": "Dataset"
        },
        "id": annotation_file,
        "target": {
            "items": [{
                "selector": {
                    "end": end_point,
                    "start": start_point,
                    "type": "TextPositionSelector"
                },
                "source": f"D_{str(uuid.uuid1()).upper()}",
            }],
            "type": "List"
        },
        "type": "Annotation"
        }

    # write new annotation json file
    with open(annotation_file, 'w') as json_output:
        json_output.write(json.dumps(json_dict))
