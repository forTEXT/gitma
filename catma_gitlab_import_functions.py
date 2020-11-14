import os
import json
import uuid



def create_tag_dict(tag_name: str, tag_uuid, parent_tag_uuid: str, tagset_uuid, property_names: list):
    color_uuid = 'CATMA_' + str(uuid.uuid1()).upper()
    author_uuid = 'CATMA_' + str(uuid.uuid1()).upper()
    property_uuids = {prop: 'CATMA_' + str(uuid.uuid1()).upper() for prop in property_names}
    prop_dict = {
        property_uuids[prop]: {
            "name": prop,
            "possibleValueList": [],
            "uuid": property_uuids[prop]
        } for prop in property_names
    }
    return {
        "name": tag_name,
        "parentUuid": parent_tag_uuid,
        "systemPropertyDefinitions": {
            color_uuid: {
                "name": "catma_displaycolor",
                "possibleValueList": [
                    "25500"
                ],
                "uuid": color_uuid
            },
            author_uuid: {
                "name": "catma_markupauthor",
                "possibleValueList": [
                "pycatma"
                ],
                "uuid": author_uuid
            }
        },
        "tagsetDefinitionUuid": tagset_uuid,
        "userDefinedPropertyDefinitions": prop_dict,
        "uuid": tag_uuid
    }


def create_tagset(root_project: str, tagset_name: str, tagset: list):

    tagset_uuid = 'CATMA_' + str(uuid.uuid1()).upper()

    # create tagset folder
    tagset_direction = root_project + '/tagsets/' + tagset_uuid
    os.mkdir(tagset_direction)

    # create tagset header json file
    tagset_header_dict = {
        "deletedDefinitions": [],
        "description": "",
        "name": tagset_name
    }
    with open(f'{tagset_direction}/header.json', 'w') as outfile:
        json.dump(tagset_header_dict, outfile)

    # create tags
    tagpaths = []
    tagset_dict = {}
    for tag_list in tagset:
        print(tag_list)
        tag_direction = tagset_direction
        tag_path = ''
        print(tag_direction)
        parent_uuid = ''
        for tag in tag_list:

            print(tag)
            if tag_path not in tagpaths:
                tag_path += f'/{tag}'

                # create tag uuid
                tag_uuid = 'CATMA_' + str(uuid.uuid1())
                tagset_dict[tag] = tag_uuid

                # create tag folder
                tag_direction = f'{tag_direction}/{tag_uuid}'
                os.mkdir(tag_direction)

                # create tag dict
                tag_dict = create_tag_dict(
                    tag_name=tag,
                    tag_uuid=tag_uuid,
                    parent_tag_uuid=parent_uuid,
                    property_names=[],
                    tagset_uuid=tagset_uuid
                )

                # create tag json file
                with open(f'{tag_direction}/propertydefs.json', 'w', encoding='utf-8') as outfile:
                    json.dump(tag_dict, outfile)

                parent_uuid = tag_uuid

            else:
                tag_direction += f'/{tagset_dict[tag]}'
                parent_uuid = tagset_dict[tag]


if __name__ == '__main__':
    os.chdir('..')
    tagset = [
        ['hauptfigur', 'männlich', 'blond'],
        ['hauptfigur', 'weibliche', 'schwarzhaarig'],
        ['nebenfigur', 'männlich'],
        ['nebenfigur', 'weibliche']
    ]
    create_tagset(
        'create_test', 'test_tagset', tagset
        )
