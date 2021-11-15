import json
import os
from catma_gitlab.tag import Tag


class Tagset:
    def __init__(self, project_uuid: str, catma_id: str):
        """
        Class which represents a CATMA Tagset.
        :param project_uuid: directory of a CATMA gitlab root folder
        :param catma_id: UUID of the tagset which corresponds with the folder name in the "tagsets" directory.

        """
        self.uuid = catma_id

        self.directory = project_uuid + '/tagsets/' + catma_id

        try:
            with open(self.directory + '/header.json') as header_input:
                header = json.load(header_input)
        except FileNotFoundError:
            raise FileNotFoundError(
                f'The Tagset in this directory could not be found:\n{self.directory}\n\
                    --> Make sure the CATMA Project clone did work properly.')

        self.name = header['name']
        self.tag_list = []
        self.tag_dict = {}

        # walks through tagsets directory
        for dirpath, dirnames, filenames in os.walk(self.directory):
            for file in filenames:
                if file == 'propertydefs.json':             # if a subdirectory is a Tag json file
                    # create a Tag Class object
                    new_tag = Tag(dirpath + '/' + file)
                    # and store it in a list
                    self.tag_list.append(new_tag)
                    # and store it in a dict
                    self.tag_dict[new_tag.id] = new_tag

        for tag in self.tag_list:
            tag.get_parent_tag(self.tag_dict)
            tag.get_child_tags(self.tag_list)

    def edit_property_names(self, tag_names: list, old_prop: str, new_prop: str):
        """
        Renames Property for all Tags given as tag_names.
        """
        tags_to_edit = [tag for tag in self.tag_list if tag.name in tag_names]
        print(tags_to_edit)
        for tag in tags_to_edit:
            tag.rename_property(old_prop=old_prop, new_prop=new_prop)

    def edit_possible_property_values(self, tag_names: list, prop: str, old_value: str, new_value: str):
        """
        Renames Property for all Tags given as tag_names.
        """
        tags_to_edit = [tag for tag in self.tag_list if tag.name in tag_names]
        print(tags_to_edit)
        for tag in tags_to_edit:
            tag.rename_possible_property_value(
                prop=prop, old_value=old_value, new_value=new_value)
