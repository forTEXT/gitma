import json


class Text:
    def __init__(self, root_direction: str, catma_id: str):
        """
        Class which represents a CATMA document.
        :param root_direction: CATMA Project direction
        :param catma_id: document uuid in the CATMA Project
        """
        self.uuid = catma_id
        with open(root_direction + '/documents/' + catma_id + '/header.json') as text_header_input:
            text_header = json.load(text_header_input)
        self.title = text_header['gitContentInfoSet']['title']
        self.author = text_header['gitContentInfoSet']['author']

        with open(root_direction + '/documents/' + catma_id +
                  '/' + catma_id + '.txt', 'r', encoding='utf-8') as document:
            self.plain_text = document.read()
