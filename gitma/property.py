class Property:
    """Class to represent a CATMA Property

    Args:
        uuid (str): The property's UUID.
        name (str): The property's name.
        possible_values (list): The property's possible value.
    """

    def __init__(self, uuid: str, name: str, possible_values: list):
        #: The property's UUID.
        self.uuid: str = uuid

        #: The property's name.
        self.name: str = name

        #: The list of possible property values that gets displayed in CATMA's property window.
        self.possible_value_list: list = possible_values

    def __repr__(self):
        return f'Property(Name: {self.name}), Default Values: {self.possible_value_list})'
