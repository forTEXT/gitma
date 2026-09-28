import os
import unittest
from pathlib import Path

from gitma import CatmaProject

TESTS_DIR = Path(__file__).resolve().parent
# Anchored on __file__ rather than the working directory so that the suite runs both
# from the repository root (as `testpaths` in pyproject.toml implies) and from inside
# tests/. The trailing separator is required: CatmaProject and write_annotation_json
# build paths by string concatenation.
DEMO_PROJECTS_DIR = f'{TESTS_DIR.parent / "demo" / "projects"}{os.sep}'
DEMO_PROJECT_NAME = 'CATMA_9385E190-13CD-44BE-8A06-32FA95B7EEFA_GitMA_Demo_Project'


def _remove_if_exists(path: str) -> None:
    """Cleanup helper, registered via addCleanup so that it also runs when a test fails.

    The page file these tests write lands inside demo/projects/. If it survived a
    failing test, the next run would append to it instead of creating it, so that
    run would fail too - the suite would stay red until the file was deleted by
    hand.
    """
    if os.path.exists(path):
        os.remove(path)


class TestAnnotation(unittest.TestCase):
    def test__copy_without_compare_annotation(self):
        # test copying an annotation by opening the demo project and copying an existing one
        project = CatmaProject(
            projects_directory=DEMO_PROJECTS_DIR,
            project_name=DEMO_PROJECT_NAME
        )

        # Selected by name, not by index: annotation_collections follows os.listdir
        # order, which varies by filesystem, whereas the expected output below pins
        # the target collection's UUID.
        annotation_collection_1 = project.ac_dict['ac_2']
        annotation_collection_2 = project.ac_dict['ac_1']

        annotation = annotation_collection_1.annotations[0]

        project_relative_page_file_path = annotation._copy(
            annotation_collection_2.name,
            uuid_override='CATMA_6150CE31-69AC-11EE-B1FA-9CB6D09600FA',
            timestamp_override='2023-10-13T11:39:18.305+02:00'
        )

        relative_page_file_path = f'{DEMO_PROJECTS_DIR}{project.uuid}/{project_relative_page_file_path}'
        self.addCleanup(_remove_if_exists, relative_page_file_path)

        with (open(TESTS_DIR / 'test_annotation_expected_output_1.json', 'r') as expected, open(relative_page_file_path, 'r') as actual):
            self.assertListEqual(list(expected), list(actual))  # could do this instead: https://stackoverflow.com/a/76842754/207981


    def test__copy_with_compare_annotation(self):
        # test copying an annotation by opening the demo project and copying an existing one, also supplying compare_annotation
        project = CatmaProject(
            projects_directory=DEMO_PROJECTS_DIR,
            project_name=DEMO_PROJECT_NAME
        )

        # Selected by name, not by index - see the note in the test above.
        annotation_collection_1 = project.ac_dict['ac_2']
        annotation_collection_2 = project.ac_dict['ac_1']

        annotation = annotation_collection_1.annotations[0]

        project_relative_page_file_path = annotation._copy(
            annotation_collection_2.name,
            annotation,  # supply the same annotation as compare_annotation to check that property values are copied
            uuid_override='CATMA_6150CE31-69AC-11EE-B1FA-9CB6D09600FA',
            timestamp_override='2023-10-13T11:39:18.305+02:00'
        )

        relative_page_file_path = f'{DEMO_PROJECTS_DIR}{project.uuid}/{project_relative_page_file_path}'
        self.addCleanup(_remove_if_exists, relative_page_file_path)

        with (open(TESTS_DIR / 'test_annotation_expected_output_2.json', 'r') as expected, open(relative_page_file_path, 'r') as actual):
            self.assertListEqual(list(expected), list(actual))  # could do this instead: https://stackoverflow.com/a/76842754/207981


if __name__ == '__main__':
    unittest.main()
