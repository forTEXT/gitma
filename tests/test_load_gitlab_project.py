## Load Gitlab project tests
# load_gitlab_project function is responsible for getting a project from CATMA gitlab endpoint.
# 1- It should pull a project if project does not exist.
# 2- It should update a project if project already exists and if `--update` flag is set.
# a- check if there is a .git folder.
# b- check if there is a folder with full uuid and project name.
# 3- If flag is not set and project already exists, it should skip pulling, print a notice and return the project name.
#
# The GitLab API is mocked, but cloning and pulling are performed for real against a
# local git repository that stands in for the CATMA GitLab remote. This keeps the tests
# offline and independent of a valid access token.

import contextlib
import io
import json
import os
import shutil
import stat
import unittest
import uuid
from unittest.mock import MagicMock, patch

import pygit2

from gitma import CatmaProject
from gitma.project import load_gitlab_project
from gitma.tag import Tag

API_KEY = 'fake_gitlab_access_token'
TEST_PROJECT_NAME = 'test_project'
TEST_PROJECTS_DIRECTORY = '.test_projects'

MARKUPTIMESTAMP_UUID = Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPTIMESTAMP
MARKUPAUTHOR_UUID = Tag.SYSTEM_PROPERTY_UUID_CATMA_MARKUPAUTHOR
SYSTEM_PROPERTY_DEFINITIONS = {
    MARKUPTIMESTAMP_UUID: {
        'name': 'catma_markuptimestamp',
        'possibleValueList': [],
        'uuid': MARKUPTIMESTAMP_UUID,
    },
    'CATMA_A309D8FB-C5B8-33C9-A1B1-8CF7A5548C6A': {
        'name': 'catma_displaycolor',
        'possibleValueList': ['-15179441'],
        'uuid': 'CATMA_A309D8FB-C5B8-33C9-A1B1-8CF7A5548C6A',
    },
    MARKUPAUTHOR_UUID: {
        'name': 'catma_markupauthor',
        'possibleValueList': ['GitMA_TestUser'],
        'uuid': MARKUPAUTHOR_UUID,
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


class TestLoadGitlabProject(unittest.TestCase):
    """Tests the clone and update behavior of `load_gitlab_project`.

    A local git repository is used as the remote: the mocked GitLab project points
    `http_url_to_repo` at it, so pygit2 clones and pulls from it exactly as it would
    from CATMA's GitLab backend.
    """

    def setUp(self):
        # keep the directory names short: libgit2 rejects paths longer than 260 characters
        self.project_uuid = f'CATMA_{str(uuid.uuid4()).upper()}_Test_Project'
        self.work_dir = os.path.join(
            os.getcwd(),
            TEST_PROJECTS_DIRECTORY,
            uuid.uuid4().hex[:8],
        )
        self.backup_dir = os.path.join(self.work_dir, 'backup')
        self.remote_dir = os.path.join(self.work_dir, 'remote')
        os.makedirs(self.backup_dir)
        os.makedirs(self.remote_dir)
        self._create_remote_project()

    def tearDown(self):
        _delete_path(self.work_dir)

    def _log(self, action, message):
        '''Prints a labeled test action with a leading newline so it does not stick to the unittest output.'''
        print(f'\n[TEST:{action}] {message}', flush=True)

    def _create_remote_project(self):
        '''Creates a minimal but valid CATMA project in a local git repo.'''
        self.document_uuid = f'D_{uuid.uuid4().hex[:8].upper()}'
        self.tagset_uuid = f'T_{uuid.uuid4().hex[:8].upper()}'
        self.tag_uuid = f'CATMA_{uuid.uuid4().hex[:8].upper()}'
        self.ac_uuid = f'C_{uuid.uuid4().hex[:8].upper()}'

        self._write_json(
            os.path.join('documents', self.document_uuid, 'header.json'),
            {
                'gitContentInfoSet': {
                    'author': 'GitMA_TestUser',
                    'description': 'test document',
                    'publisher': 'gitma',
                    'title': 'Test Document',
                },
            },
        )
        with open(
            os.path.join(self.remote_dir, 'documents', self.document_uuid, f'{self.document_uuid}.txt'),
            'w',
            encoding='utf-8',
            newline='',
        ) as output:
            output.write('This is a test document for the load_gitlab_project tests.')

        self._write_json(
            os.path.join('tagsets', self.tagset_uuid, 'header.json'),
            {
                'name': 'test_tagset',
                'description': None,
                'responsibleUser': 'GitMA_TestUser',
            },
        )
        self._write_json(
            os.path.join('tagsets', self.tagset_uuid, self.tag_uuid, 'propertydefs.json'),
            {
                'name': 'test_tag',
                'parentUuid': '',
                'systemPropertyDefinitions': SYSTEM_PROPERTY_DEFINITIONS,
                'tagsetDefinitionUuid': self.tagset_uuid,
                'userDefinedPropertyDefinitions': {},
                'uuid': self.tag_uuid,
            },
        )

        self._write_json(
            os.path.join('collections', self.ac_uuid, 'header.json'),
            {
                'name': 'test_annotation_collection',
                'sourceDocumentId': self.document_uuid,
                'responsibleUser': 'GitMA_TestUser',
            },
        )
        self._write_json(
            os.path.join('collections', self.ac_uuid, 'annotations', 'annotations.json'),
            [],
        )

        repo = pygit2.init_repository(self.remote_dir, initial_head='master')
        repo.config['user.name'] = 'GitMA Test'
        repo.config['user.email'] = 'test@gitma.local'
        self._commit_all(repo, 'initialize test project')

    def _write_json(self, relative_path, data):
        path = os.path.join(self.remote_dir, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='') as output:
            json.dump(data, output, indent=2)

    def _commit_all(self, repo, message):
        repo.index.add_all()
        repo.index.write()
        tree = repo.index.write_tree()
        parents = [] if repo.head_is_unborn else [repo.head.target]
        signature = repo.default_signature
        return repo.create_commit('refs/heads/master', signature, signature, message, tree, parents)

    def _commit_remote_file(self, relative_path, content, message):
        '''Writes a file to the remote's working tree and commits it.'''
        path = os.path.join(self.remote_dir, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8', newline='') as output:
            output.write(content)
        repo = pygit2.Repository(self.remote_dir)
        return self._commit_all(repo, message)

    @property
    def project_path(self):
        return os.path.join(self.backup_dir, self.project_uuid)

    def _new_annotation(self, annotation_uuid):
        '''Builds a fully populated CATMA annotation for the fixture project.'''
        return {
            '@context': 'http://www.w3.org/ns/anno.jsonld',
            'type': 'Annotation',
            'id': f'collections/{self.ac_uuid}/annotations/{annotation_uuid}',
            'body': {
                '@context': {
                    MARKUPTIMESTAMP_UUID: f'tagsets/{self.tagset_uuid}/{self.tag_uuid}/{MARKUPTIMESTAMP_UUID}',
                    MARKUPAUTHOR_UUID: f'tagsets/{self.tagset_uuid}/{self.tag_uuid}/{MARKUPAUTHOR_UUID}',
                    'tag': 'https://www.catma.de/tag',
                    'tagset': 'https://www.catma.de/tagset',
                },
                'tagset': f'tagsets/{self.tagset_uuid}',
                'tag': f'tagsets/{self.tagset_uuid}/{self.tag_uuid}',
                'properties': {
                    'system': {
                        MARKUPTIMESTAMP_UUID: ['2026-11-05T12:00:00.000+00:00'],
                        MARKUPAUTHOR_UUID: ['GitMA_TestUser'],
                    },
                    'user': {},
                },
                'type': 'Dataset',
            },
            'target': {
                'items': [{
                    'source': self.document_uuid,
                    'selector': {
                        'start': 0,
                        'end': 4,
                        'type': 'TextPositionSelector',
                    },
                }],
                'type': 'List',
            },
        }

    def _load(self, update=False):
        '''Calls `load_gitlab_project` with a mocked GitLab API.'''
        gitlab_project = MagicMock()
        gitlab_project.id = 42
        gitlab_project.name = self.project_uuid
        gitlab_project.http_url_to_repo = self.remote_dir

        gitlab_client = MagicMock()
        gitlab_client.projects.list.return_value = [gitlab_project]
        gitlab_client.projects.get.return_value = gitlab_project

        with patch('gitma.project.gitlab.Gitlab', return_value=gitlab_client) as gitlab_class:
            result = load_gitlab_project(
                gitlab_access_token=API_KEY,
                project_name=TEST_PROJECT_NAME,
                backup_directory=self.backup_dir,
                update=update,
            )
        # unittest.mock assertions do not accept a msg argument; mock reports the mismatch itself.
        gitlab_class.assert_called_once_with(
            url='https://git.catma.de/',
            private_token=API_KEY,
        )
        gitlab_client.projects.list.assert_called_once_with(search=TEST_PROJECT_NAME)
        gitlab_client.projects.get.assert_called_once_with(id=gitlab_project.id)
        return result

    def test_on_empty_projects_directory(self):
        '''[TEST] Clones the project into an empty backup directory.'''
        self._log('CLONE', f'Cloning "{self.project_uuid}" into "{self.backup_dir}"')
        project_name = self._load()

        self.assertEqual(
            project_name,
            self.project_uuid,
            f"Expected load_gitlab_project to return the GitLab project name '{self.project_uuid}', but got '{project_name}'.",
        )
        self.assertTrue(
            os.path.isdir(self.project_path),
            f"Expected the project to be cloned to '{self.project_path}', but the directory does not exist.",
        )
        self.assertTrue(
            os.path.isdir(os.path.join(self.project_path, '.git')),
            f"Expected a '.git' directory inside the cloned project at '{self.project_path}'.",
        )
        document_path = os.path.join(
            self.project_path, 'documents', self.document_uuid, f'{self.document_uuid}.txt'
        )
        self.assertTrue(
            os.path.isfile(document_path),
            f"Expected the cloned project to contain the document file '{document_path}', but it does not exist.",
        )

        local_repo = pygit2.Repository(self.project_path)
        remote_repo = pygit2.Repository(self.remote_dir)
        self.assertEqual(
            local_repo.head.target,
            remote_repo.head.target,
            f"Expected the local clone to be at the remote HEAD {remote_repo.head.target}, but it is at {local_repo.head.target}.",
        )

    def test_on_existing_project_with_update_flag(self):
        '''[TEST] Pulls new remote commits into an existing local clone when update is set.'''
        self._log('CLONE', f'Cloning "{self.project_uuid}" into "{self.backup_dir}"')
        self._load()
        head_before = pygit2.Repository(self.project_path).head.target

        self._commit_remote_file('update_marker.txt', 'created on the remote\n', 'add update marker')
        self._log('UPDATE', 'Pulling latest changes from the remote')
        project_name = self._load(update=True)

        self.assertEqual(
            project_name,
            self.project_uuid,
            f"Expected load_gitlab_project to return the GitLab project name '{self.project_uuid}', but got '{project_name}'.",
        )
        update_marker_path = os.path.join(self.project_path, 'update_marker.txt')
        self.assertTrue(
            os.path.isfile(update_marker_path),
            f"Expected the new remote file '{update_marker_path}' to be pulled into the existing clone, but it does not exist.",
        )

        local_repo = pygit2.Repository(self.project_path)
        remote_repo = pygit2.Repository(self.remote_dir)
        self.assertEqual(
            local_repo.head.target,
            remote_repo.head.target,
            f"Expected the local clone to be updated to the remote HEAD {remote_repo.head.target}, but it is at {local_repo.head.target}.",
        )
        self.assertNotEqual(
            local_repo.head.target,
            head_before,
            f"Expected the update to advance the local HEAD beyond {head_before}, but it did not change.",
        )

    def test_on_existing_project_without_update_flag(self):
        '''[TEST] Skips the pull, prints a notice and returns the project name when update is not set.'''
        self._log('CLONE', f'Cloning "{self.project_uuid}" into "{self.backup_dir}"')
        self._load()
        head_before = pygit2.Repository(self.project_path).head.target

        # this file must not reach the local clone because no pull should happen
        self._commit_remote_file(
            'skipped_update_marker.txt', 'must not be pulled\n', 'add marker that should be skipped'
        )

        self._log('SKIP_UPDATE', 'Project exists and update=False, expecting no pull')
        with contextlib.redirect_stdout(io.StringIO()) as buffer:
            project_name = self._load(update=False)
        printed = buffer.getvalue()

        self.assertEqual(
            project_name,
            self.project_uuid,
            f"Expected load_gitlab_project to return the GitLab project name '{self.project_uuid}', but got '{project_name}'.",
        )
        self.assertIn(
            'already exists',
            printed,
            f"Expected the output to explain that the project already exists, but got: '{printed}'.",
        )
        self.assertIn(
            'No pulling operation has been performed',
            printed,
            f"Expected the output to state that no pull was performed, but got: '{printed}'.",
        )
        self.assertIn(
            'update',
            printed,
            f"Expected the output to mention the 'update' parameter, but got: '{printed}'.",
        )
        skipped_marker_path = os.path.join(self.project_path, 'skipped_update_marker.txt')
        self.assertFalse(
            os.path.exists(skipped_marker_path),
            f"Expected no pull to happen when update=False, but the new remote file '{skipped_marker_path}' exists locally.",
        )
        head_after = pygit2.Repository(self.project_path).head.target
        self.assertEqual(
            head_after,
            head_before,
            f"Expected the local HEAD to remain at {head_before} when update=False, but it changed to {head_after}.",
        )

    def test_after_new_annotations_added_on_remote(self):
        '''[TEST] Pulls a detailed newly added annotation page file from the remote.'''
        self._log('CLONE', f'Cloning "{self.project_uuid}" into "{self.backup_dir}"')
        self._load()

        annotation_uuid = f'CATMA_{str(uuid.uuid4()).upper()}'
        annotation = self._new_annotation(annotation_uuid)
        annotation_page_path = os.path.join(
            'collections', self.ac_uuid, 'annotations', 'new_annotations_0.json'
        )
        self._log('ADD_REMOTE_ANNOTATION', f'Committing new annotation "{annotation_uuid}"')
        self._commit_remote_file(
            annotation_page_path, json.dumps([annotation], indent=2), 'add new annotations'
        )

        self._log('UPDATE', 'Pulling the new annotation from the remote')
        self._load(update=True)

        local_annotation_page = os.path.join(self.project_path, *annotation_page_path.split(os.sep))
        self.assertTrue(
            os.path.isfile(local_annotation_page),
            f"Expected the new annotation page '{local_annotation_page}' to be pulled into the local clone, but it does not exist.",
        )
        with open(local_annotation_page, 'r', encoding='utf-8', newline='') as annotation_page_file:
            local_annotations = json.load(annotation_page_file)

        self.assertEqual(
            len(local_annotations),
            1,
            f"Expected the pulled annotation page to contain exactly 1 annotation, but got {len(local_annotations)}.",
        )
        pulled_annotation = local_annotations[0]
        self.assertEqual(
            pulled_annotation['id'],
            f'collections/{self.ac_uuid}/annotations/{annotation_uuid}',
            f"Expected the pulled annotation id to point at '{annotation_uuid}', but got '{pulled_annotation['id']}'.",
        )
        self.assertEqual(
            pulled_annotation['body']['tagset'],
            f'tagsets/{self.tagset_uuid}',
            f"Expected the annotation to reference tagset '{self.tagset_uuid}', but got '{pulled_annotation['body']['tagset']}'.",
        )
        self.assertEqual(
            pulled_annotation['body']['tag'],
            f'tagsets/{self.tagset_uuid}/{self.tag_uuid}',
            f"Expected the annotation to reference tag '{self.tag_uuid}', but got '{pulled_annotation['body']['tag']}'.",
        )
        selector = pulled_annotation['target']['items'][0]['selector']
        self.assertEqual(
            (selector['start'], selector['end']),
            (0, 4),
            f"Expected the annotation to cover text offsets 0 to 4, but got {selector['start']} to {selector['end']}.",
        )
        self.assertEqual(
            pulled_annotation['body']['properties']['system'][MARKUPAUTHOR_UUID],
            ['GitMA_TestUser'],
            f"Expected the annotation author to be 'GitMA_TestUser', but got "
            f"{pulled_annotation['body']['properties']['system'][MARKUPAUTHOR_UUID]}.",
        )

        # the update must also be able to parse the annotation into a CatmaProject
        self._log('RELOAD', 'Reloading the project and checking the parsed annotation')
        reloaded_project = CatmaProject(
            project_name=self.project_uuid,
            projects_directory=self.backup_dir,
            gitlab_access_token=API_KEY,
        )
        reloaded_ac = reloaded_project.ac_dict['test_annotation_collection']
        self.assertEqual(
            len(reloaded_ac.annotations),
            1,
            f"Expected the reloaded project to contain 1 parsed annotation, but got {len(reloaded_ac.annotations)}.",
        )
        reloaded_annotation = reloaded_ac.annotations[0]
        self.assertEqual(
            reloaded_annotation.tag.name,
            'test_tag',
            f"Expected the parsed annotation to use tag 'test_tag', but got '{reloaded_annotation.tag.name}'.",
        )
        self.assertEqual(
            reloaded_annotation.text,
            'This',
            f"Expected the parsed annotation to cover the text 'This', but got '{reloaded_annotation.text}'.",
        )
        self.assertEqual(
            reloaded_annotation.author,
            'GitMA_TestUser',
            f"Expected the parsed annotation author to be 'GitMA_TestUser', but got '{reloaded_annotation.author}'.",
        )

        local_repo = pygit2.Repository(self.project_path)
        remote_repo = pygit2.Repository(self.remote_dir)
        self.assertEqual(
            local_repo.head.target,
            remote_repo.head.target,
            f"Expected the local clone to be updated to the remote HEAD {remote_repo.head.target}, but it is at {local_repo.head.target}.",
        )


if __name__ == '__main__':
    unittest.main()
