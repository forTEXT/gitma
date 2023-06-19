import json


class Text:
    """Class which represents a CATMA document.

    Args:
        project_uuid (str): CATMA Project UUID.
        catma_id (str): Document UUID in the CATMA Project.
    """

    def __init__(self, project_uuid: str, catma_id: str):
        #: The text's UUID.
        self.uuid: str = catma_id
        with open(project_uuid + '/documents/' + catma_id + '/header.json') as text_header_input:
            text_header = json.load(text_header_input)

        #: The text's title.
        self.title: str = text_header['gitContentInfoSet']['title']

        #: The text's author.
        self.author: str = text_header['gitContentInfoSet']['author']

        text_file_dir = f"{project_uuid}/documents/{catma_id}/{catma_id}.txt"
        with open(text_file_dir, 'r', encoding='utf-8', newline="") as document:
            #: The text as a plain text. The offset annotation data refers to this plain text.
            self.plain_text: str = document.read()

    def __repr__(self):
        return f"Text(Name: {self.title}, Author: {self.author})"

    def __len__(self):
        return len(self.plain_text)
