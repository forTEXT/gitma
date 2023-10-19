import os
import unittest

from gitma import CatmaProject
from gitma._write_annotation import write_annotation_json
from gitma.annotation import get_tagset_uuid, get_tag_uuid


class TestWriteAnnotation(unittest.TestCase):
    def test_write_annotation_json(self):
        # test writing an annotation by opening the demo project and copying an existing one
        project = CatmaProject(
            projects_directory='../demo/projects/',
            project_name='CATMA_9385E190-13CD-44BE-8A06-32FA95B7EEFA_GitMA_Demo_Project'
        )

        text = project.texts[0]

        annotation_collection = project.annotation_collections[0]
        annotation = annotation_collection.annotations[0]

        tagset_uuid = get_tagset_uuid(annotation.data)
        tagset = project.tagset_dict[tagset_uuid]

        tag_uuid = get_tag_uuid(annotation.data)
        tag = tagset.tag_dict[tag_uuid]

        project_relative_page_file_path = write_annotation_json(
            project,
            text.title,
            annotation_collection.name,
            tagset.name,
            tag.name,
            [annotation.start_point],
            [annotation.end_point],
            annotation.properties,
            annotation.author,
            uuid_override='CATMA_823C1D3A-684C-11EE-8D15-9CB6D09600FA',
            timestamp_override='2023-10-11T17:40:30.684+02:00'
        )

        relative_page_file_path = f'../demo/projects/{project.uuid}/{project_relative_page_file_path}'

        with (open('test__write_annotation_expected_output_1.json', 'r') as expected, open(relative_page_file_path, 'r') as actual):
            self.assertListEqual(list(expected), list(actual))  # could do this instead: https://stackoverflow.com/a/76842754/207981

        # write the same annotation again and assert that it is properly appended to the page file
        write_annotation_json(
            project,
            text.title,
            annotation_collection.name,
            tagset.name,
            tag.name,
            [annotation.start_point],
            [annotation.end_point],
            annotation.properties,
            annotation.author,
            uuid_override='CATMA_823C1D3A-684C-11EE-8D15-9CB6D09600FA',
            timestamp_override='2023-10-11T17:40:30.684+02:00'
        )

        with (open('test__write_annotation_expected_output_2.json', 'r') as expected, open(relative_page_file_path, 'r') as actual):
            self.assertListEqual(list(expected), list(actual))

        # write only '[]' into the page file, then write the same annotation again and assert that the page file is overwritten
        with open(relative_page_file_path, 'w') as page_file:
            page_file.write('[]')

        write_annotation_json(
            project,
            text.title,
            annotation_collection.name,
            tagset.name,
            tag.name,
            [annotation.start_point],
            [annotation.end_point],
            annotation.properties,
            annotation.author,
            uuid_override='CATMA_823C1D3A-684C-11EE-8D15-9CB6D09600FA',
            timestamp_override='2023-10-11T17:40:30.684+02:00'
        )

        with (open('test__write_annotation_expected_output_1.json', 'r') as expected, open(relative_page_file_path, 'r') as actual):
            self.assertListEqual(list(expected), list(actual))

        # delete output page file
        os.remove(relative_page_file_path)


if __name__ == '__main__':
    unittest.main()
