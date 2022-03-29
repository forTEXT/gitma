import json
from typing import List, Dict
from gitma.property import Property


def rgbint_to_hex(rgb: int) -> str:
    red = (rgb >> 16) & 0xFF
    green = (rgb >> 8) & 0xFF
    blue = (rgb >> 0) & 0xFF
    return '0x'+'{:02x}'.format(red)+'{:02x}'.format(green)+'{:02x}'.format(blue)


def get_tag_color(tag_dict: dict) -> str:
    system_properties = tag_dict['systemPropertyDefinitions']
    color_prop = [
        system_properties[item] for item in system_properties
        if system_properties[item]['name'] == "catma_displaycolor"
    ][0]
    color_rgbstr = color_prop["possibleValueList"][0]
    return rgbint_to_hex(int(color_rgbstr))


def get_tag_name(tag_dict):
    return tag_dict['name']


def get_tag_uuid(tag_dict):
    return tag_dict['uuid']


def get_parent_uuid(tag_dict):
    return tag_dict['parentUuid'] if 'parentUuid' in tag_dict else None


def get_user_properties(tag_dict):
    return tag_dict['userDefinedPropertyDefinitions']


def get_time_uuid(tag_dict):
    system_properties = tag_dict['systemPropertyDefinitions']
    time_prop = [item for item in system_properties if system_properties[item]
                 ['name'] == "catma_markuptimestamp"]
    if len(time_prop) > 0:
        return time_prop[0]
    else:
        return None


def get_user_uuid(tag_dict):
    system_properties = tag_dict['systemPropertyDefinitions']
    time_prop = [item for item in system_properties if system_properties[item]
                 ['name'] == "catma_markupauthor"]
    if len(time_prop) > 0:
        return time_prop[0]
    else:
        return None


class Tag:
    """Class which represents a CATMA Tag.

    Args:
        json_file_directory (str): The directory ot the tag within the project's folder structure.

    Raises:
        FileNotFoundError: If the json_file_directory could not be found.
    """

    def __init__(self, json_file_directory: str):
        #: The tag's directory.
        self.directory: str = json_file_directory.replace('\\', '/')
        try:
            with open(json_file_directory) as json_input:
                self.json = json.load(json_input)
        except FileNotFoundError:
            raise FileNotFoundError(
                f'The Tag file in this directory could not be found:\n{self.directory}\n\
                    --> Make sure the CATMA Project clone did work properly.')

        #: The tag's name.
        self.name: str = self.json['name']

        #: The tag's UUID.
        self.id: str = self.json['uuid']

        #: The parent tag's UUID.
        self.parent_id: str = self.json['parentUuid'] if 'parentUuid' in self.json else None

        #: The tag's properties as a list of dictionaries.
        self.properties: dict = self.json['userDefinedPropertyDefinitions']

        #: The tag's properties as list of gitma.Property objects.
        self.properties_list: List[Property] = [
            Property(
                uuid=item,
                name=self.properties[item]['name'],
                possible_values=self.properties[item]["possibleValueList"]
            ) for item in self.properties
        ]

        #: Dictionary with the names of properties as keys and gitma.Propety objects as values.
        self.properties_dict: Dict[str, Property] = {
            prop.name: prop for prop in self.properties_list
        }

        #: The color defined for the tag in the CATMA UI
        self.color = get_tag_color(self.json)

        #: List of child tags as gitma.Tag objects.
        #: Is an empy list until gitma.Tag.get_child_tags will be used.
        self.child_tags: List[Tag] = []

        #: Parent tag as gitma.Tag objects.
        #: Is None until gitma.Tag.get_child_tags will be used.
        self.parent: Tag = None

        #: The full tag path within the tagset.
        self.full_path: str = None

        #: The tag's time UUID.
        self.time_property: str = get_time_uuid(self.json)

        #: The tag's user property.
        self.user_property: str = get_user_properties(self.json)

    def __repr__(self):
        return f'Tag(Name: {self.name}, Properties: {self.properties_list})'

    def get_parent_tag(self, tagset_dict: dict) -> None:
        """Adds the the parent tag to self.parent.

        Args:
            tagset_dict (dict): The tagset as a gitma.Tagse.tag_dict.
        """
        self.parent = tagset_dict[self.parent_id] if self.parent_id in tagset_dict else None

    def get_child_tags(self, tags: list) -> None:
        """Adds all child tags to the tag's tags

        Args:
            tags (list): A list of gitma.Tag objects.
        """
        for tag in tags:
            if tag.parent_id == self.id:
                self.child_tags.append(tag)

    def full_tag_path(self) -> None:
        tag_path = f'/{self.name}'
        new_tag = self

        while new_tag.parent:
            new_tag = new_tag.parent
            tag_path = f'/{new_tag.name}{tag_path}'

        self.full_path = tag_path

    def rename_property(self, old_prop: str, new_prop: str) -> None:
        """Renames a property of the tag by overwriting it's json.

        Args:
            old_prop (str): The old property's name.
            new_prop (str): The new proeprty's name.
        """
        for item in self.properties_list:
            if item.name == old_prop:
                self.json['userDefinedPropertyDefinitions'][item.uuid]['name'] = new_prop
        # write new tag json file
        with open(self.file_directory, 'w') as json_output:
            json_output.write(json.dumps(self.json))

    def rename_possible_property_value(self, prop: str, old_value: str, new_value: str) -> None:
        """Renames as specified property value in the list of possible property values.

        Args:
            prop (str): The property's name.
            old_value (str): The property value to be replaced.
            new_value (str): The new property value.
        """
        for item in self.properties_list:
            if item.name == prop:
                pv = self.json['userDefinedPropertyDefinitions'][item.uuid]["possibleValueList"]
                for index, v in enumerate(pv):
                    if v == old_value:
                        pv[index] = new_value
                self.json['userDefinedPropertyDefinitions'][item.uuid]["possibleValueList"] = pv
        # write new tag json file
        with open(self.file_directory, 'w') as json_output:
            json_output.write(json.dumps(self.json))
