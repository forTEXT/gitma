import argparse
import contextlib
import io
import json
import os
import random
import shutil
import stat
import sys
import unittest
import uuid

import pygit2

from gitma import CatmaProject

KEEP_TEST_DATA = os.environ.get('GITMA_KEEP_TEST_DATA', '') == '1'

PROJECT_NAME = 'Scratch_Test_Project'
TEXT_TITLE = 'Test Document'
TEXT_LENGTH = 1000
TAGSETS = {
    'test_tagset_1': ['test_tag_1', 'test_tag_2'],
    'test_tagset_2': ['test_tag_3', 'test_tag_4'],
}
AC_NAMES = ['test_ac_1', 'test_ac_2', 'test_ac_3']
GOLD_AC_NAME = 'gold_ac'
ANNOTATIONS_PER_AC = 10
TEST_PROJECTS_DIRECTORY = ".test_projects"
SYSTEM_PROPERTY_DEFINITIONS = {
    'CATMA_54A5F93F-5333-3F0D-92F7-7BD5930DB9E6': {
        'name': 'catma_markuptimestamp',
        'possibleValueList': [],
        'uuid': 'CATMA_54A5F93F-5333-3F0D-92F7-7BD5930DB9E6',
    },
    'CATMA_A309D8FB-C5B8-33C9-A1B1-8CF7A5548C6A': {
        'name': 'catma_displaycolor',
        'possibleValueList': ['-15179441'],
        'uuid': 'CATMA_A309D8FB-C5B8-33C9-A1B1-8CF7A5548C6A',
    },
    'CATMA_AB27F1D4-303A-3622-BB2C-72C310D0C1BF': {
        'name': 'catma_markupauthor',
        'possibleValueList': ['GitMA_TestUser'],
        'uuid': 'CATMA_AB27F1D4-303A-3622-BB2C-72C310D0C1BF',
    },
}


def _delete_path(path):
    '''Recursively deletes a path, clearing the read-only attribute first (pygit2 writes git loose objects as read-only on Windows).'''
    for root, _dirs, files in os.walk(path):
        for name in files:
            try:
                os.chmod(os.path.join(root, name), stat.S_IWRITE)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)


def _tree_paths(repo, tree, path=''):
    '''Returns the paths of all blobs in a pygit2 tree.'''
    paths = []
    for entry in tree:
        entry_path = f'{path}/{entry.name}' if path else entry.name
        if entry.type == pygit2.GIT_OBJECT_TREE:
            paths.extend(_tree_paths(repo, repo[entry.id], entry_path))
        else:
            paths.append(entry_path)
    return paths


class TestScratchProject(unittest.TestCase):
    """
    Test case for creating a CATMA project programmatically from scratch, adding document, tagsets, annotation collections and annotations.

    Call with "--keep-test-data" to keep the generated test data under .test_projects/ and skip teardown. Can also be set via the GITMA_KEEP_TEST_DATA=1 environment variable.
    """
    @classmethod
    def setUpClass(cls):
        cls.projects_directory = os.path.join(os.getcwd(), TEST_PROJECTS_DIRECTORY)
        _delete_path(cls.projects_directory)
        os.makedirs(cls.projects_directory, exist_ok=True)
        if not KEEP_TEST_DATA:
            cls.addClassCleanup(lambda: _delete_path(cls.projects_directory))

        # build project directory name
        cls.project_uuid = f'CATMA_{uuid.uuid4().hex.upper()}_{PROJECT_NAME}'
        cls.project_dir = os.path.join(cls.projects_directory, cls.project_uuid)

        # create the project directory structure
        os.makedirs(os.path.join(cls.project_dir, 'documents'))
        os.makedirs(os.path.join(cls.project_dir, 'tagsets'))
        os.makedirs(os.path.join(cls.project_dir, 'collections'))

        cls.text_uuid = cls._create_text()
        for tagset_name, tag_names in TAGSETS.items():
            cls._create_tagset(tagset_name, tag_names)
        cls.ac_names = list(AC_NAMES)
        for ac_name in cls.ac_names:
            cls._create_annotation_collection(ac_name)
        print(f'[SETUP] Created a barebone CATMA project. project_uuid: {cls.project_uuid}, project_dir: {cls.project_dir}')
        cls._create_annotation_collection(GOLD_AC_NAME)
        cls._setup_git_repo()
        project = cls._load_project()
        cls._add_annotations(project)
        cls.project = cls._load_project()

    @classmethod
    def tearDownClass(cls):
        '''Cleans up the temporary project directory. Skipped when KEEP_TEST_DATA is set.'''
        if not KEEP_TEST_DATA:
            _delete_path(cls.projects_directory)

    @classmethod
    def _load_project(cls) -> CatmaProject:
        '''Loads a CATMA project from the test directory.'''
        return CatmaProject(
            project_name=PROJECT_NAME,
            projects_directory=cls.projects_directory,
            gitlab_access_token='faketoken',
        )

    @classmethod
    def _setup_git_repo(cls):
        '''Initializes a git repo with an initial commit and a local bare remote.'''
        repo = pygit2.init_repository(cls.project_dir, initial_head='master')
        repo.config['user.name'] = 'GitMA Test'
        repo.config['user.email'] = 'test@gitma.local'

        index = repo.index
        index.add_all()
        index.write()
        tree = index.write_tree()
        signature = repo.default_signature
        repo.create_commit(
            'refs/heads/master',
            signature,
            signature,
            'initialize test project',
            tree,
            [],
        )

        cls.remote_dir = os.path.join(cls.projects_directory, 'origin.git')
        pygit2.init_repository(cls.remote_dir, bare=True, initial_head='master')
        repo.remotes.create('origin', 'file:///' + cls.remote_dir.replace(os.sep, '/'))
        print(f'[SETUP] Initialized git repo in {cls.project_dir} and a bare remote in {cls.remote_dir}.')

    @classmethod
    def _create_text(cls) -> str:
        '''Creates a document in the project directory.'''
        text_uuid = f'D_{uuid.uuid4().hex.upper()}'
        text_dir = os.path.join(cls.project_dir, 'documents', text_uuid)
        os.makedirs(text_dir)

        with open(os.path.join(text_dir, 'header.json'), 'w', encoding='utf-8', newline='') as output:
            json.dump(
                {
                    'gitContentInfoSet': {
                        'author': 'Test Author',
                        'description': 'dummy text created by gitma tests',
                        'publisher': 'gitma',
                        'title': TEXT_TITLE,
                    },
                    'gitIndexInfoSet': {
                        'locale': 'en',
                        'unseparableCharacterSequences': [],
                        'userDefinedSeparatingCharacters': [],
                    },
                    'gitTechInfoSet': {
                        'charset': 'UTF-8',
                        'checksum': 0,
                        'fileName': 'dummy_text.txt',
                        'fileOSType': 'UNIX',
                        'fileType': 'TEXT',
                        'mimeType': 'text/plain',
                        'responsibleUser': 'GitMA_TestUser',
                    },
                },
                output,
                indent=2,
            )

        paragraph = 'The quick brown fox jumps over the lazy dog. ' * 10 + '\n\n' # a paragraph of 10 sentences
        plain_text = (paragraph * (TEXT_LENGTH // len(paragraph) + 1))[:TEXT_LENGTH] # continue adding paragraphs until TEXT_LENGTH is reached, then cut off the rest
        with open(os.path.join(text_dir, f'{text_uuid}.txt'), 'w', encoding='utf-8', newline='') as output:
            output.write(plain_text)
        print(f'[PREP:CREATE_TEXT] Created document with title: {TEXT_TITLE}, text_uuid: {text_uuid}')
        return text_uuid

    @classmethod
    def _create_tagset(cls, tagset_name: str, tag_names: list) -> str:
        '''Creates a tagset and as many tags as specified in the tag_names list.'''
        tagset_uuid = f'T_{uuid.uuid4().hex.upper()}'
        tagset_dir = os.path.join(cls.project_dir, 'tagsets', tagset_uuid)
        os.makedirs(tagset_dir)

        with open(os.path.join(tagset_dir, 'header.json'), 'w', encoding='utf-8', newline='') as output:
            json.dump(
                {
                    'deletedDefinitions': [],
                    'description': None,
                    'forkedFromCommitURL': None,
                    'name': tagset_name,
                    'responsibleUser': 'GitMA_TestUser',
                },
                output,
                indent=2,
            )

        for tag_name in tag_names:
            tag_uuid = f'CATMA_{uuid.uuid4().hex.upper()}'
            tag_dir = os.path.join(tagset_dir, tag_uuid)
            os.makedirs(tag_dir)
            with open(os.path.join(tag_dir, 'propertydefs.json'), 'w', encoding='utf-8', newline='') as output:
                json.dump(
                    {
                        'name': tag_name,
                        'parentUuid': '',
                        'systemPropertyDefinitions': SYSTEM_PROPERTY_DEFINITIONS,
                        'tagsetDefinitionUuid': tagset_uuid,
                        'userDefinedPropertyDefinitions': {},
                        'uuid': tag_uuid,
                    },
                    output,
                    indent=2,
                )
        print(f'[PREP:CREATE_TAGSET] Passed with tagset_name: {tagset_name}, tagset_uuid: {tagset_uuid}')
        return tagset_uuid

    @classmethod
    def _create_annotation_collection(cls, ac_name: str) -> str:
        '''Creates an annotation collection in the project directory.'''
        ac_uuid = f'C_{uuid.uuid4().hex.upper()}'
        ac_dir = os.path.join(cls.project_dir, 'collections', ac_uuid)
        os.makedirs(os.path.join(ac_dir, 'annotations'))

        with open(os.path.join(ac_dir, 'header.json'), 'w', encoding='utf-8', newline='') as output:
            json.dump(
                {
                    'author': None,
                    'description': 'annotation collection created by gitma tests',
                    'forkedFromCommitURL': None,
                    'name': ac_name,
                    'publisher': None,
                    'responsibleUser': 'GitMA_TestUser',
                    'sourceDocumentId': cls.text_uuid,
                },
                output,
                indent=2,
            )
        print(f'[PREP:CREATE_ANNOTATION_COLLECTION] Passed with ac_name: {ac_name}, ac_uuid: {ac_uuid}')
        return ac_uuid

    def test_project_loads_from_scratch(self):
        '''Tests loading the auto generated project.
        This test checks the following conditions:
        - Project has one document with the expected title and UUID.
        - Project has two tagsets with the expected tag names.
        - Project has the same tags as specified in the TAGSETS dictionary.
        - Project has three annotation collections with the expected names and associated with the correct document.
        '''
        project = self.project

        self.assertEqual(len(project.texts), 1, f"Expected 1 document in the project, but found {len(project.texts)}.")
        text = project.text_dict[TEXT_TITLE]
        self.assertEqual(text.uuid, self.text_uuid)
        self.assertNotEqual(len(text.plain_text), 0)

        self.assertEqual(len(project.tagsets), 2)
        tag_names_per_tagset = {
            tagset.name: sorted([tag.name for tag in tagset.tags])
            for tagset in project.tagsets
        }
        self.assertEqual(tag_names_per_tagset, TAGSETS)

        self.assertEqual(len(project.annotation_collections), len(AC_NAMES) + 1)  # +1 for the gold annotation collection
        for ac_name in self.ac_names:
            ac = project.ac_dict[ac_name]
            self.assertEqual(ac.plain_text_id, self.text_uuid)
            self.assertEqual(ac.text.title, TEXT_TITLE)
        print(f'[TEST:LOAD_PROJECT] Loaded dummy project created by this test.')


    @classmethod
    def _add_annotations(cls, project: CatmaProject):
        '''Adds annotations with random start and end points to the annotation collections.'''
        random.seed(42)

        tagset_tag_pairs = [
            (tagset_name, tag_name)
            for tagset_name, tag_names in TAGSETS.items()
            for tag_name in tag_names
        ]

        text_length = len(project.text_dict[TEXT_TITLE].plain_text)

        for ac_name in cls.ac_names:
            ac_annotations = []
            for _ in range(ANNOTATIONS_PER_AC):
                start = random.randint(0, text_length - 2)
                end = random.randint(start + 1, text_length - 1)
                tagset_name, tag_name = random.choice(tagset_tag_pairs)
                ac_annotations.append((tagset_name, tag_name, start, end))
                project.write_annotation_json(
                    text_title=TEXT_TITLE,
                    annotation_collection_name=ac_name,
                    tagset_name=tagset_name,
                    tag_name=tag_name,
                    start_points=[start],
                    end_points=[end],
                    property_annotations={},
                    author='GitMA_TestUser',
                )
            print(f"[PREP:ADD_ANNOTATIONS] Added {len(ac_annotations)} annotations to annotation collection: {ac_name}.")

    def test_a_add_annotations(self):
        '''Adds annotations with random start and end points to the annotation collections.
        This test checks the following conditions:
        - Checks the number of annotations in each annotation collection against ANNOTATIONS_PER_AC.
        - Checks that the tag names of the annotations are in the allowed_tags set.
        - Checks that the start and end points of the annotations are within the bounds of the text length.
        '''
        allowed_tags = {tag_name for tag_names in TAGSETS.values() for tag_name in tag_names}

        project = self.project
        text = project.text_dict[TEXT_TITLE]

        annotation_count = 0
        for ac_name in self.ac_names:
            ac = project.ac_dict[ac_name]
            self.assertEqual(len(ac.annotations), ANNOTATIONS_PER_AC, f"Expected {ANNOTATIONS_PER_AC} annotations in collection {ac_name}, but found {len(ac.annotations)}.")

            for an in ac.annotations:
                self.assertIn(an.tag.name, allowed_tags, f"Annotation tag name '{an.tag.name}' is not in the allowed tags: {allowed_tags}")
                self.assertGreaterEqual(an.start_point, 0, f"Annotation start point {an.start_point} is less than 0.")
                self.assertLess(an.start_point, an.end_point, f"Annotation start point {an.start_point} is not less than end point {an.end_point}.")
                self.assertLessEqual(an.end_point, len(text), f"Annotation end point {an.end_point} is not less than or equal to text length {len(text)}.")
            annotation_count += len(ac.annotations)
        print(f"[TEST:ADD_ANNOTATIONS] Verified {annotation_count} annotations in the project.")

    def test_b_push_annotations(self):
        '''Tests `AnnotationCollection.push_annotations` by pushing to a local bare remote.
        This test checks the following conditions:
        - Pushing creates a local commit with the given message and a clean working tree.
        - The commit's tree contains the annotation page file.
        - The local commit is pushed to the bare remote.
        - A second push with nothing to commit prints "No changes to push" without creating a local
          commit or interacting with the remote.
        '''
        commit_message = 'add annotations via pygit2'
        ac = self.project.ac_dict[self.ac_names[0]]

        ac.push_annotations(commit_message=commit_message)

        repo = pygit2.Repository(self.project_dir)
        master = repo.lookup_reference('refs/heads/master')
        pushed_commit = repo[master.target]
        self.assertEqual(pushed_commit.message.strip(), commit_message)
        self.assertEqual(repo.status(), {})

        page_file_path = f'collections/{ac.uuid}/annotations/GitMA_DummyUser_0.json'
        self.assertIn(page_file_path, _tree_paths(repo, pushed_commit.tree))

        remote_repo = pygit2.Repository(self.remote_dir)
        remote_target = remote_repo.lookup_reference('refs/heads/master').target
        self.assertEqual(remote_target, master.target)

        # No changes validation
        with contextlib.redirect_stdout(io.StringIO()) as buf: # capture the output of the second push
            ac.push_annotations()
        self.assertIn('No changes to push', buf.getvalue(), "Expected 'No changes to push' in the output of the second push.")
        self.assertEqual(repo.lookup_reference('refs/heads/master').target, master.target, "second push does not create a new commit")
        self.assertEqual(repo.status(), {}, "second push does not change the working tree")
        self.assertEqual(remote_repo.lookup_reference('refs/heads/master').target, remote_target, "second push does not change the remote")
        print(f"[TEST:PUSH_ANNOTATIONS] Pushed annotations from collection {ac.name} to the local bare remote in {self.remote_dir}.")

    def test_c_create_gold_annotations(self):
        '''
        Tests the gold annotation functionality by copying annotations from one collection to another.
        `create_gold_annotations` is called with the same annotation collection for both `ac_1_name` and `ac_2_name`, and with `push_to_gitlab=True`. This triggers new annotations being added 
        '''
        project = self.project
        ac_1_name = self.ac_names[0]
        ac_2_name = self.ac_names[0]

        project.create_gold_annotations(
            ac_1_name=ac_1_name,
            ac_2_name=ac_2_name,
            gold_ac_name=GOLD_AC_NAME,
            min_overlap=0.5,
            same_tag=True,
            copy_property_values_if_equal=True,
            push_to_gitlab=True,
        )
        project = self._load_project()  # reload the project to get the latest state after gold annotations creation

        self.assertEqual(len(project.ac_dict[GOLD_AC_NAME].annotations),
                         len(project.ac_dict[ac_1_name].annotations),
                         "Expected the same number of annotations in the gold collection as in the source collection.")
        print(f"[TEST:GOLD_ANNOTATIONS_FULL_MATCH] Created gold annotations in collection: {GOLD_AC_NAME} in {project.name} from the same {ac_1_name} annotation collection. All annotations should match and be copied and a git commit should be created.")


    def test_e_pull_annotations(self):
        self.project.pull()
        print(f"[TEST:PULL_ANNOTATIONS] Pulled annotations from the local bare remote in {self.remote_dir}.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the scratch CATMA project tests.',
    )
    parser.add_argument(
        '--keep-test-data',
        action='store_true',
        help='Keep the generated test data under .test_projects/ and skip teardown. '
             'Can also be set via the GITMA_KEEP_TEST_DATA=1 environment variable.',
    )
    args, remaining = parser.parse_known_args()
    KEEP_TEST_DATA = args.keep_test_data or os.environ.get('GITMA_KEEP_TEST_DATA', '') == '1'
    unittest.main(argv=[sys.argv[0]] + remaining)