import os
import unittest

from gitma import CatmaProject


class TestAnnotation(unittest.TestCase):
    def test__copy_without_compare_annotation(self):
        # test copying an annotation by opening the demo project and copying an existing one
        project = CatmaProject(
            project_directory='../demo/projects/',
            project_name='CATMA_9385E190-13CD-44BE-8A06-32FA95B7EEFA_GitMA_Demo_Project'
        )

        annotation_collection_1 = project.annotation_collections[0]
        annotation_collection_2 = project.annotation_collections[1]

        annotation = annotation_collection_1.annotations[0]

        project_relative_page_file_path = annotation._copy(
            annotation_collection_2.name,
            uuid_override='CATMA_6150CE31-69AC-11EE-B1FA-9CB6D09600FA',
            timestamp_override='2023-10-13T11:39:18.305+02:00'
        )

        relative_page_file_path = f'../demo/projects/{project.uuid}/{project_relative_page_file_path}'

        with (open('test_annotation_expected_output_1.json', 'r') as expected, open(relative_page_file_path, 'r') as actual):
            self.assertListEqual(list(expected), list(actual))  # could do this instead: https://stackoverflow.com/a/76842754/207981

        # delete output page file
        os.remove(relative_page_file_path)

    def test__copy_with_compare_annotation(self):
        # test copying an annotation by opening the demo project and copying an existing one, also supplying compare_annotation
        project = CatmaProject(
            project_directory='../demo/projects/',
            project_name='CATMA_9385E190-13CD-44BE-8A06-32FA95B7EEFA_GitMA_Demo_Project'
        )

        annotation_collection_1 = project.annotation_collections[0]
        annotation_collection_2 = project.annotation_collections[1]

        annotation = annotation_collection_1.annotations[0]

        project_relative_page_file_path = annotation._copy(
            annotation_collection_2.name,
            annotation,  # supply the same annotation as compare_annotation to check that property values are copied
            uuid_override='CATMA_6150CE31-69AC-11EE-B1FA-9CB6D09600FA',
            timestamp_override='2023-10-13T11:39:18.305+02:00'
        )

        relative_page_file_path = f'../demo/projects/{project.uuid}/{project_relative_page_file_path}'

        with (open('test_annotation_expected_output_2.json', 'r') as expected, open(relative_page_file_path, 'r') as actual):
            self.assertListEqual(list(expected), list(actual))  # could do this instead: https://stackoverflow.com/a/76842754/207981

        # delete output page file
        os.remove(relative_page_file_path)


if __name__ == '__main__':
    unittest.main()
