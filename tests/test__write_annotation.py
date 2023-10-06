import unittest

from gitma import CatmaProject
from gitma._write_annotation import write_annotation_json
from gitma.annotation import get_tagset_uuid, get_tag_uuid


class TestWriteAnnotation(unittest.TestCase):
    def test_write_annotation_json(self):
        # test writing an annotation by opening the demo project and copying an existing one
        project = CatmaProject(
            project_directory='../demo/projects/',
            project_name='CATMA_9385E190-13CD-44BE-8A06-32FA95B7EEFA_GitMA_Demo_Project'
        )

        text = project.texts[0]

        annotation_collection = project.annotation_collections[0]
        annotation = annotation_collection.annotations[0]

        tagset_uuid = get_tagset_uuid(annotation.data)
        tagset = project.tagset_dict[tagset_uuid]

        tag_uuid = get_tag_uuid(annotation.data)
        tag = tagset.tag_dict[tag_uuid]

        write_annotation_json(
            project,
            text.title,
            annotation_collection.name,
            tagset.name,
            tag.name,
            [annotation.start_point],
            [annotation.end_point],
            annotation.properties,
            annotation.author
        )

        # TODO: assert things
        assert False


if __name__ == '__main__':
    unittest.main()
