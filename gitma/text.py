import json


class Text:
    """Class which represents a CATMA document.

    Args:
        project_uuid (str): Name of a CATMA project directory.
        document_uuid (str): Document UUID. Corresponds to the directory name in the "documents" directory.
    """
    def __init__(self, project_uuid: str, document_uuid: str):
        #: The text's UUID.
        self.uuid: str = document_uuid
        with open(project_uuid + '/documents/' + document_uuid +
                  '/header.json', 'r', encoding='utf-8', newline='') as text_header_input:
            text_header = json.load(text_header_input)

        #: The text's title.
        self.title: str = text_header['gitContentInfoSet']['title']

        #: The text's author.
        self.author: str = text_header['gitContentInfoSet']['author']

        text_file_path = f"{project_uuid}/documents/{document_uuid}/{document_uuid}.txt"
        with open(text_file_path, 'r', encoding='utf-8', newline='') as document:
            #: The text as a plain text. The offset annotation data refers to this plain text.
            self.plain_text: str = document.read()

    def __repr__(self):
        return f"Text(Name: {self.title}, Author: {self.author})"

    def __len__(self):
        return len(self.plain_text)
