"""
Some classes to represent a CATMA project cloned from gitlab including
    - Tag class
    - Tagset class
    - Annotation class
    - AnnotationCollection class
    - Text class
    - Project class

Each annotation is accessible from a project object.
Each annotation collection is also represented as pandas data frame: AnnotationCollection.table
"""

from catma_gitlab.catma_gitlab_functions import *
#from catma_gitlab_functions import *
import os
import json
import pandas as pd


class Property:
    def __init__(self, uuid, name, possible_value):
        self.uuid = uuid
        self.name = name
        self.possible_value_list = possible_value

    def __repr__(self):
        return self.name


class Tag:
    """
    Class which represents a CATMA Tag.
    :param: direction of a CATMA tag json file.
    """
    def __init__(self, json_file_direction: str):
        self.file_direction = json_file_direction

        with open(json_file_direction) as json_input:
            self.json = json.load(json_input)

        self.name = self.json['name']
        self.id = self.json['uuid']
        self.parent_id = self.json['parentUuid'] if 'parentUuid' in self.json else None
        self.properties = self.json['userDefinedPropertyDefinitions']
        self.properties_list = [
            Property(
                uuid=item,
                name=self.properties[item]['name'],
                possible_value=self.properties[item]["possibleValueList"]
                ) for item in self.properties
        ]
        self.properties_dict = {repr(item): item for item in self.properties_list}

        self.child_tags = []
        self.parent = None

    def get_parent_tag(self, tagset_dict: dict):
        self.parent = tagset_dict[self.parent_id] if self.parent_id in tagset_dict else None

    def get_child_tags(self, tag_list: list):
        for tag in tag_list:
            if tag.parent_id == self.id:
                self.child_tags.append(tag)


class Tagset:
    """
    Class which represents a CATMA Tagset.
    :param root_direction: direction of a CATMA gitlab root folder
    :param catma_id: UUID of the tagset which corresponds with the folder name in the "tagsets" direction.

    """
    def __init__(self, root_direction: str, catma_id: str):
        tagset_direction = root_direction + '/tagsets/' + catma_id
        with open(tagset_direction + '/header.json') as header_input:
            header = json.load(header_input)
        self.name = header['name']

        self.tag_list = []
        self.tag_dict = {}
        for dirpath, dirnames, filenames in os.walk(tagset_direction):  # walks through tagsets direction
            for file in filenames:
                if file == 'propertydefs.json':             # if a subdirection is a Tag json file
                    new_tag = Tag(dirpath + '/' + file)     # create a Tag Class object
                    self.tag_list.append(new_tag)           # and store it in a list
                    self.tag_dict[new_tag.id] = new_tag     # and store it in a dict

        for tag in self.tag_list:
            tag.get_parent_tag(self.tag_dict)
            tag.get_child_tags(self.tag_list)


class Text:
    """
    Class which represents a CATMA document.
    """
    def __init__(self, root_direction: str, catma_id: str):
        with open(root_direction + '/documents/' + catma_id + '/header.json') as text_header_input:
            text_header = json.load(text_header_input)

        self.title = text_header['gitContentInfoSet']['title']
        self.author = text_header['gitContentInfoSet']['author']

        with open(root_direction + '/documents/' + catma_id +
                  '/' + catma_id + '.txt', 'r', encoding='utf-8') as document:
            self.plain_text = document.read()


class Annotation:
    """
    Class which represents a CATMA annotation.
    :param direction: the annotations direction
    :param plain_text: annotated text as CATMA document
    """
    def __init__(self, direction: str, plain_text: str, context=10):
        self.direction = direction
        with open(direction, 'r', encoding='utf-8') as ip:
            self.data = json.load(ip)

        self.start_point, self.end_point = get_first_and_last_text_pointer(self.data)
        self.text = ' '.join(list(get_annotated_text(self.data, plain_text)))
        self.pretext = plain_text[self.start_point - context: self.start_point]
        self.posttext = plain_text[self.end_point: self.end_point + context]

        tag_direction = self.data['body']['tag'].replace('https://git.catma.de/', '') + '/propertydefs.json'
        self.tag = Tag(tag_direction)

        self.properties = {
            self.tag.properties[prop]['name']:
                self.data['body']['properties']['user'][prop] for prop in self.data['body']['properties']['user']
        }


    def modify_property_values(self, tag: str, prop:str, value:list):
        """
        Modifies Property Values if the annotation is tagged by defined Tag and Property.
        """
        if self.tag.name == tag and prop in self.properties:
            # open annotation json file
            with open(self.direction) as json_input:
                json_dict = json.load(json_input)

            prop_uuid = self.tag.properties_dict[prop].uuid

            # set new property value
            json_dict["body"]['properties']['user'][prop_uuid] = value

            # write new annotation json file
            with open(self.direction, 'w') as json_output:
                json_output.write(json.dumps(json_dict))

    def delete_property(self, tag: str, prop:str):
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


class AnnotationCollection:
    """
        Class which represents a CATMA annotation collection.
        :param root_direction:  direction of a CATMA gitlab root folder
        :param catma_id: uuid of the collection (folder)
        """
    def __init__(self, root_direction: str, catma_id: str):
        self.id = catma_id

        with open(root_direction + '/collections/' + self.id + '/header.json') as header_json:
            self.header = json.load(header_json)

        self.name = self.header['name']
        self.plain_text_id = self.header['sourceDocumentId']
        self.text = Text(root_direction=root_direction, catma_id=self.plain_text_id)

        self.annotations = [
            Annotation(
                direction=root_direction + '/collections/' + self.id + '/annotations/' + annotation,
                plain_text=self.text.plain_text
            ) for annotation in os.listdir(root_direction + '/collections/' + self.id + '/annotations/')
        ]
        self.annotations = sorted(self.annotations, key=lambda a: a.start_point)
        self.tags = [an.tag for an in self.annotations]

        # create pandas data frame for annotation collection
        self.df = pd.DataFrame(
            [
                (self.text.title, self.name, a.tag.name, a.properties, a.pretext, a.text, a.posttext, a.start_point, a.end_point)
                for a in self.annotations
            ], columns=['document', 'annotation collection', 'tag', 'properties', 'pretext',
                        'annotation', 'posttext', 'start_point', 'end_point']
        )
        self.df = split_property_dict_to_column((self.df))

    def __repr__(self):
        return self.name


    def get_annotation_by_tag(self, tag_name: str):
        return [
            annotation for annotation in self.annotations
            if annotation.tag.name == tag_name
            or annotation.tag.parent.name == tag_name
        ]

    def annotate_properties(self, tag: str, prop: str, value: list):
        for an in self.annotations:
            an.modify_property_values(tag=tag, prop=prop, value=value)

    def delete_properties(self, tag: str, prop: str, value: list):
        for an in self.annotations:
            an.delete_property(tag=tag, prop=prop, value=value)



class CatmaProject:
    """
    Class which represents a CATMA project including the texts, the annotation collections and the tagsets using
    the classes Text, AnnotationCollection and Tagset.
    :param root_direction:  direction of a CATMA gitlab root folder/project
    :param load_intrinsic: if false the project is loaded without intrinsic markup
    """
    def __init__(self, root_direction):
        tagsets_direction = root_direction + '/tagsets/'
        collections_direction = root_direction + '/collections/'

        self.tagsets = [
            Tagset(
                root_direction=root_direction,
                catma_id=direction
            ) for direction in os.listdir(tagsets_direction)
        ]

        self.annotation_collections = [
            AnnotationCollection(
                root_direction=root_direction,
                catma_id=direction
            ) for direction in os.listdir(collections_direction)
        ]

    def get_annotation_by_tag(self, tag_name):
        for ac in self.annotation_collections:
            return ac.get_annotation_by_tag(tag_name)


if __name__ == '__main__':
    project_direction = '../Test_Annotationen/'
    os.chdir(project_direction)
    project_uuid = os.listdir()[0]
    project = project_uuid

    corpus = CatmaProject(
        root_direction=project
    )
    # prop_to_annotate = 'mental'
    # for ac in corpus.annotation_collections:
    #     for an in ac.annotations[:5]:
    #         print(an.properties)
    #         an.modify_property_values(prop='mental', value=['ja', 'nein'])
    #         print(an.properties)
    #

    prop_to_delete = 'persistent'
    for an in corpus.annotation_collections[0].annotations[:5]:
        print(an.properties)
        an.delete_property(prop=prop_to_delete)



