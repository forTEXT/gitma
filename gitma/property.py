"""
Class ro represent a CATMA Property
"""


class Property:
    def __init__(self, uuid, name, possible_value):
        self.uuid = uuid
        self.name = name
        self.possible_value_list = possible_value

    def __repr__(self):
        return f'Property(Name: {self.name}), Default Values: {self.possible_value_list})'
