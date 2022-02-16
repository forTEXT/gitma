import subprocess
import os
import json
import gitlab
import pandas as pd
from typing import Dict, List, Tuple
from gitma.text import Text
from gitma.tagset import Tagset
from gitma.annotation_collection import AnnotationCollection


def load_gitlab_project(gitlab_access_token: str, project_name: str, backup_directory: str = './') -> str:
    """Downloads a CATMA Project using git.

    Args:
        gitlab_access_token (str): GitLab Access Token.
        project_name (str): The CATMA Project name.
        project_dir (str): Where to locate the CATMA Project.

    Raises:
        Exception: If no CATMA Project with the given name could be found.

    Returns:
        str: The CATMA Project UUID
    """

    gl = gitlab.Gitlab(
        url='https://git.catma.de/',
        private_token=gitlab_access_token
    )

    try:
        project_gitlab_id = gl.projects.list(search=project_name)[0].id
    except IndexError:
        raise Exception("Couldn't find the given CATMA Project!")

    project_uuid = gl.projects.get(id=project_gitlab_id).name
    project_url = f"https://git.catma.de/{project_uuid[:-5]}/{project_uuid}.git"

    # clone the project in the defined directory
    cwd = os.getcwd()
    os.chdir(backup_directory)
    subprocess.run(['git', 'clone', '--recurse-submodules', project_url])
    os.chdir(cwd)
    return project_uuid


def get_ac_name(project_uuid: str, directory: str) -> str:
    """Gives Annotation Collection name.

    Args:
        project_uuid (str): CATMA gitlab root project uuids
        directory (str): annotation collection directory
        test_positive (bool, optional): what should be returned if it is intrinsic markup. Defaults to True.

    Returns:
        str: CATMA Annotation Collection
    """
    with open(f'{project_uuid}/collections/{directory}/header.json', 'r') as header_input:
        header_dict = json.load(header_input)

    return header_dict['name']


def load_annotation_collections(
        catma_project,
        included_acs: list = None,
        excluded_acs: list = None,
        ac_filter_keyword: str = None) -> Tuple[List[AnnotationCollection], Dict[str, AnnotationCollection]]:
    """Generates List and Dict of CATMA Annotation Collections.

    Args:
        project_uuid (str): CATMA Project UUID
        included_acs (list): All listed Annotation Collections get loaded.
        excluded_acs (list): All listed Annotations Collections don't get loaded.
            If neither icluded nor excluded Annotation Collections are defined, all Annotation Collections get loaded.

    Returns:
        Tuple[List[AnnotationCollection], Dict[str, AnnotationCollection]]: List and Dict of Annotation Collections
    """
    collections_directory = catma_project.uuid + '/collections/'

    if included_acs:
        annotation_collections = [
            AnnotationCollection(
                catma_project=catma_project,
                ac_uuid=directory
            ) for directory in os.listdir(collections_directory)
            if get_ac_name(catma_project.uuid, directory) in included_acs
        ]
    elif excluded_acs:
        annotation_collections = [
            AnnotationCollection(
                catma_project=catma_project,
                ac_uuid=directory
            ) for directory in os.listdir(collections_directory)
            if get_ac_name(catma_project.uuid, directory) not in excluded_acs
        ]
    elif ac_filter_keyword:
        annotation_collections = [
            AnnotationCollection(
                catma_project=catma_project,
                ac_uuid=directory
            ) for directory in os.listdir(collections_directory)
            if ac_filter_keyword in get_ac_name(catma_project.uuid, directory)
        ]
    else:
        annotation_collections = [
            AnnotationCollection(
                catma_project=catma_project,
                ac_uuid=directory
            ) for directory in os.listdir(collections_directory)
            if directory.startswith('C_') or directory.startswith('CATMA_')
        ]

    ac_dict = {
        ac.name: ac for ac in annotation_collections}

    return annotation_collections, ac_dict


def test_tageset_directory(
        project_uuid: str,
        tagset_uuid: str):
    tageset_dir = f'{project_uuid}/tagsets/{tagset_uuid}/header.json'
    if os.path.isfile(tageset_dir):
        return True


def load_tagsets(project_uuid: str) -> Tuple[List[Tagset], Dict[str, Tagset]]:
    """Generates List and Dict of Tagsets.

    Args:
        project_uuid (str): CATMA Project UUID

    Returns:
        List[Tagset]: List and Dict of Tagsets
    """
    tagsets_directory = project_uuid + '/tagsets/'
    tagsets = [
        Tagset(
            project_uuid=project_uuid,
            catma_id=directory
        ) for directory in os.listdir(tagsets_directory)
        # ignore empty tagsets
        if test_tageset_directory(project_uuid, directory)
    ]
    tagset_dict = {tagset.uuid: tagset for tagset in tagsets}

    return tagsets, tagset_dict


def load_texts(project_uuid: str) -> Tuple[List[Text], Dict[str, Text]]:
    """Generates List and Dict of CATMA Texts.

    Args:
        project_uuid (str): CATMA Project UUID

    Returns:
        Tuple[List[Text], Dict[Text]]: List and Dict of CATMA Texts
    """
    texts_directory = project_uuid + '/documents/'
    texts = [
        Text(
            project_uuid=project_uuid,
            catma_id=directory
        ) for directory in os.listdir(texts_directory)
    ]

    texts_dict = {text.title: text for text in texts}
    return texts, texts_dict


class CatmaProject:
    def __init__(
            self,
            project_uuid: str = None,
            project_directory: str = './',
            included_acs: list = None,
            excluded_acs: list = None,
            ac_filter_keyword: str = None,
            load_from_gitlab: bool = False,
            gitlab_access_token: str = None,
            project_name: str = None,
            backup_directory: str = './'):
        """This Project represents a CATMA Project including all Documents, Tagsets
        and Annotation Collections.
        You can eather load the Project from a local git clone or you load it directly
        from GitLab after generating a gitlab_access_token in the CATMA GUI.

        Args:
            project_directory (str, optional): The directory where your CATMA Project(s) are located. Defaults to '.'.
            project_uuid (str, optional): The Project UUID. Defaults to None.
            included_acs (list, optional): All Annotation Collections that should get loaded. If neither included nor excluded
                Annotation Collections are defined, all Annotation Collections get loaded. Default to None.
            excluded_acs (list, optional): All Annotation Collections that should not get loaded. Default to None.
            load_from_gitlab (bool, optional): Whether the CATMA Project shall be loaded dircetly from the CATMA GitLab. Defaults to False.
            gitlab_access_token (str, optional): The private CATMA GitLab Token. Defaults to None.
            project_name (str, optional): The CATMA Project name. Defaults to None.
            backup_directory (str, optional): The your Project clone should be located. Default to './'.
        Raises:
            Exception: If the CATMA Project were not found in the CATMA GitLab.
            FileNotFoundError: If the local or remote CATMA Project were not found.
        """
        # get the current directory to return after loaded the project
        cwd = os.getcwd()

        # Clone CATMA Project
        if load_from_gitlab:
            self.uuid = load_gitlab_project(
                gitlab_access_token=gitlab_access_token,
                project_name=project_name,
                backup_directory=backup_directory
            )
            project_directory = backup_directory
        else:
            self.uuid = project_uuid

        self.project_directory = project_directory

        try:
            os.chdir(self.project_directory)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The CATMA Project in this directory could not been found: \n{self.project_directory}\n\
                    -> Make sure the CATMA Project clone did work properly and that the project directory is correct")

        try:
            # Load Tagsets
            print('Loading Tagsets ...')
            if os.path.isdir(self.uuid + '/tagsets/'):
                self.tagsets, self.tagset_dict = load_tagsets(
                    project_uuid=self.uuid)
                print(f'\t Found {len(self.tagsets)} Tagset(s).')
            else:
                self.tagsets, self.tagset_dict = None, None
                print(f'\t Did not found any Tagsets.')

            # Load Texts
            print('Loading Documents ...')
            self.texts, self.text_dict = load_texts(project_uuid=self.uuid)
            print(f'\t Found {len(self.texts)} Document(s).')

            # Load Annotation Collections
            print('Loading Annotation Collections ...')
            self.annotation_collections, self.ac_dict = load_annotation_collections(
                catma_project=self,
                included_acs=included_acs,
                excluded_acs=excluded_acs,
                ac_filter_keyword=ac_filter_keyword,
            )
            os.chdir(cwd)
        except FileNotFoundError:
            os.chdir(cwd)
            raise FileNotFoundError(
                f"Some components of your CATMA project could not be loaded."
            )

    def __repr__(self):
        documents = [text.title for text in self.texts]
        tagsets = [tagset.name for tagset in self.tagsets]
        acs = [ac.name for ac in self.annotation_collections]
        return f"CatmaProject(\n\tName: {self.uuid[43:-5]},\n\tDocuments: {documents},\n\tTagsets: {tagsets},\n\tAnnotationCollections: {acs})"

    from gitma._gold_annotation import create_gold_annotations

    from gitma._write_annotation import write_annotation_json

    from gitma._vizualize import plot_annotation_progression

    from gitma._vizualize import plot_interactive

    from gitma._metrics import get_iaa

    from gitma._gamma import gamma_agreement

    def all_annotations(self):
        for ac in self.annotation_collections:
            for an in ac.annotations:
                yield an

    def merge_annotations_per_document(self):
        """Merges all Annotation Collections DataFrames belonging to the same document and extends the `self.ac_dict`.
        """
        for document in self.texts:
            ac_name = f'{document.title}-all_annotations'
            self.ac_dict[ac_name] = pd.DataFrame()
            for ac in self.annotation_collections:
                if ac.text.title == document.title:
                    self.ac_dict[ac_name] = self.ac_dict[ac_name].append(
                        ac.df, ignore_index=True)
                    self.ac_dict[ac_name].sort_values(
                        by=['start_point'], inplace=True)

    def stats(self) -> pd.DataFrame:
        """Shows some CATMA Project stats.

        Returns:
            pd.DataFrame: DataFrame with projects stats sorted by the Annotation Collection names.
        """
        stats_dict = {
            ac.name: {
                'annotations': len(ac.annotations),
                'authors': set([an.author for an in ac.annotations]),
                'tags': set([an.tag.name for an in ac.annotations]),
                'first_annotation': min([an.date for an in ac.annotations]),
                'last_annotation': max([an.date for an in ac.annotations]),
                'uuid': ac.uuid,
            } for ac in self.annotation_collections
            if len(ac.annotations) > 0
        }

        return pd.DataFrame(stats_dict).T.sort_index()

    def update(self) -> None:
        """Updates local git folder and reloads CatmaProject
        """
        cwd = os.getcwd()
        os.chdir(f'{self.project_directory}{self.uuid}/')

        subprocess.run(['git', 'pull'])
        subprocess.run(['git', 'submodule', 'update',
                       '--recursive', '--remote'])

        os.chdir('../')
        # Load Tagsets
        self.tagsets, self.tagset_dict = load_tagsets(project_uuid=self.uuid)

        # Load Texts
        self.texts, self.text_dict = load_texts(project_uuid=self.uuid)

        # Load Annotation Collections
        self.annotation_collections, self.ac_dict = load_annotation_collections(
            project_uuid=self.uuid)

        print('Updated the CATMA Project')

        os.chdir(cwd)


if __name__ == '__main__':

    project = CatmaProject(
        project_directory='gitma/test/demo_project/',
        project_uuid='test_corpus_root'
    )
    print(project.stats())
