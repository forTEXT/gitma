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
    time_prop = [item for item in system_properties if system_properties[item]['name'] == "catma_markuptimestamp"]
    if len(time_prop) > 0:
        return time_prop[0]
    else:
        return None


def get_user_uuid(tag_dict):
    system_properties = tag_dict['systemPropertyDefinitions']
    time_prop = [item for item in system_properties if system_properties[item]['name'] == "catma_markupauthor"]
    if len(time_prop) > 0:
        return time_prop[0]
    else:
        return None
