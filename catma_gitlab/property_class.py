"""
Class ro represent a CATMA Property
"""


class Property:
    def __init__(self, uuid, name, possible_value):
        self.uuid = uuid
        self.name = name
        self.possible_value_list = possible_value

    def __repr__(self):
        return self.name
