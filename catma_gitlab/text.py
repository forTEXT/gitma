import json


class Text:
    def __init__(self, project_uuid: str, catma_id: str):
        """
        Class which represents a CATMA document.
        :param project_uuid: CATMA Project directory
        :param catma_id: document uuid in the CATMA Project
        """
        self.uuid = catma_id
        with open(project_uuid + '/documents/' + catma_id + '/header.json') as text_header_input:
            text_header = json.load(text_header_input)
        self.title = text_header['gitContentInfoSet']['title']
        self.author = text_header['gitContentInfoSet']['author']

        with open(project_uuid + '/documents/' + catma_id +
                  '/' + catma_id + '.txt', 'r', encoding='utf-8') as document:
            self.plain_text = document.read()
