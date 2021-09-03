import json
from catma_gitlab.property import Property


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
    def __init__(self, json_file_directory: str):
        """
        Class which represents a CATMA Tag.
        :param: directory of a CATMA tag json file.
        """
        self.file_directory = json_file_directory.replace('\\', '/')
        with open(json_file_directory) as json_input:
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
        self.properties_dict = {
            repr(item): item for item in self.properties_list}

        self.child_tags = []
        self.parent = None

        self.time_property = get_time_uuid(self.json)
        self.user_property = get_user_properties(self.json)

    def get_parent_tag(self, tagset_dict: dict):
        self.parent = tagset_dict[self.parent_id] if self.parent_id in tagset_dict else None

    def get_child_tags(self, tag_list: list):
        for tag in tag_list:
            if tag.parent_id == self.id:
                self.child_tags.append(tag)

    def rename_property(self, old_prop: str, new_prop: str):
        for item in self.properties_list:
            if item.name == old_prop:
                self.json['userDefinedPropertyDefinitions'][item.uuid]['name'] = new_prop
        # write new tag json file
        with open(self.file_directory, 'w') as json_output:
            json_output.write(json.dumps(self.json))

    def rename_possible_property_value(self, prop: str, old_value: str, new_value: str):
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
