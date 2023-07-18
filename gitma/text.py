import json


class Text:
    """Class which represents a CATMA document.

    Args:
        project_root_directory (str): Name of a CATMA project root directory.
        document_uuid (str): Document UUID in the CATMA project.
    """

    def __init__(self, project_root_directory: str, document_uuid: str):
        #: The text's UUID.
        self.uuid: str = document_uuid
        with open(project_root_directory + '/documents/' + document_uuid +
                  '/header.json', 'r', encoding='utf-8', newline='') as text_header_input:
            text_header = json.load(text_header_input)

        #: The text's title.
        self.title: str = text_header['gitContentInfoSet']['title']

        #: The text's author.
        self.author: str = text_header['gitContentInfoSet']['author']

        with open(project_root_directory + '/documents/' + document_uuid +
                  '/' + document_uuid + '.txt', 'r', encoding='utf-8', newline='') as document:
            #: The text as a plain text. The offset annotation data refers to this plain text.
            self.plain_text: str = document.read()

    def __repr__(self):
        return f"Text(Name: {self.title}, Author: {self.author})"

    def __len__(self):
        return len(self.plain_text)
