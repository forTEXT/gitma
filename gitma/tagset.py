import json
import os
from typing import List, Dict
from gitma.tag import Tag


class Tagset:
    """Class which represents a CATMA tagset.

    Args:
        project_uuid (str): Name of a CATMA project directory.
        tagset_uuid (str): Tagset UUID. Corresponds to the directory name in the "tagsets" directory.
    Raises:
        FileNotFoundError: If the path of the tagset's header.json does not exist.
    """
    def __init__(self, project_uuid: str, tagset_uuid: str):
        #: The tagsets UUID.
        self.uuid: str = tagset_uuid

        #: The path of the tagsets within the project's folder structure.
        self.path: str = project_uuid + '/tagsets/' + tagset_uuid

        try:
            with open(self.path + '/header.json', 'r', encoding='utf-8', newline='') as header_input:
                header = json.load(header_input)
        except FileNotFoundError:
            raise FileNotFoundError(
                f'The tagset at this path could not be found: {self.path}\n\
                    --> Make sure the CATMA project clone worked properly.')

        #: The tagset's name
        self.name: str = header['name']

        #: List of tags as gitma.Tag objects.
        self.tags: List[Tag] = []

        #: Dictionary of tags with UUIDs as keys and gitma.Tag objects as values.
        self.tag_dict: Dict[str, Tag] = {}

        # walks through tagset directory
        for dirpath, _, filenames in os.walk(self.path):
            for file in filenames:
                if file == 'propertydefs.json':             # if a file is a tag JSON file
                    # create a Tag object
                    new_tag = Tag(dirpath + '/' + file)
                    # and store it in a list
                    self.tags.append(new_tag)
                    # and store it in a dict
                    self.tag_dict[new_tag.id] = new_tag

        for tag in self.tags:
            tag.get_parent_tag(self.tag_dict)
            tag.get_child_tags(self.tags)

        for tag in self.tags:
            tag.full_tag_path()

    def __repr__(self) -> str:
        return f'Tagset(Name: {self.name}, Tags: {self.tags})'

    def edit_property_names(self, tag_names: list, old_prop: str, new_prop: str) -> None:
        """Renames a property for all tags given as tag_names.

        Args:
            tag_names (list): List of names of the tags that hold the property to be renamed.
            old_prop (str): Property's name that will be changed.
            new_prop (str): The new property's name.
        """
        tags_to_edit = [tag for tag in self.tags if tag.name in tag_names]
        for tag in tags_to_edit:
            tag.rename_property(old_prop=old_prop, new_prop=new_prop)

    def edit_possible_property_values(self, tag_names: list, prop: str, old_value: str, new_value: str) -> None:
        """Replace an old property value with a new one. The possible property values will be listed in CATMA's
        property annotation window.

        Args:
            tag_names (list): The list of tags with the given property.
            prop (str): The property that holds the given old property value.
            old_value (str): The old property value.
            new_value (str): The new property value.
        """
        tags_to_edit = [tag for tag in self.tags if tag.name in tag_names]
        for tag in tags_to_edit:
            tag.rename_possible_property_value(
                prop=prop, old_value=old_value, new_value=new_value)
