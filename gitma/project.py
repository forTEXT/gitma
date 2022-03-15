import subprocess
import os
import json
import gitlab
import pygit2
import pandas as pd
from typing import Dict, List, Tuple, Union, Generator
from gitma.text import Text
from gitma.tagset import Tagset
from gitma.annotation_collection import AnnotationCollection
from gitma.annotation import Annotation


def load_gitlab_project(
        gitlab_access_token: str,
        project_name: str,
        backup_directory: str = './') -> str:
    """Downloads a CATMA Project using git.

    Args:
        gitlab_access_token (str): GitLab Access Token.
        project_name (str): The CATMA Project name.
        project_dir (str): Where to locate the CATMA Project.

    Raises:
        Exception: If no CATMA Project with the given name could be found.

    Returns:
        str: The CATMA Project UUID.
    """
    # cwd = os.getcwd()
    # os.chdir(backup_directory)
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
    creds = pygit2.UserPass('none', gitlab_access_token)
    callbacks = pygit2.RemoteCallbacks(credentials=creds)
    repo = pygit2.clone_repository(
        url=project_url,
        path=backup_directory + project_uuid,
        bare=False,
        callbacks=callbacks
    )
    submodules = repo.listall_submodules()
    repo.init_submodules(submodules=submodules)
    repo.update_submodules(submodules=submodules, callbacks=callbacks)

    return project_uuid


def get_local_project_uuid(
        project_directory: str,
        project_name: str) -> str:
    """Returns project uuid identified by name.

    Args:
        project_directory (str): The directory where the project clone is located.
        project_name (str): The project's name.

    Raises:
        FileNotFoundError: If none of the projects in the project_directory is named as the given project name.
        ValueError: If more then one project with the given project name exist.

    Returns:
        str: Project UUID.
    """
    project_uuids = [
        item for item in os.listdir(project_directory)
        if project_name in item
    ]
    if len(project_uuids) < 1:
        raise FileNotFoundError(
            f'The project "{project_name}" name does not exist in directory "{project_directory}".\
                Select one of these: {[item[43:-5] for item in os.listdir(project_directory)]}!'
        )
    elif len(project_uuids) > 1:
        raise ValueError(
            f'In "{project_directory}" exist multiple projects named "{project_name}".\
            Specifiy which project to load by one of the full UUIDs as project name: {project_uuids}'
        )
    else:
        return project_uuids[0]


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
        excluded_acs (list): All listed Annotations Collections don't get loaded.\
            If neither icluded nor excluded Annotation Collections are defined, all Annotation Collections get loaded.

    Returns:
        Tuple[List[AnnotationCollection], Dict[str, AnnotationCollection]]: List and Dict of Annotation Collections
    """
    collections_directory = catma_project.uuid + '/collections/'

    if included_acs:        # selects annotation collections listed in included_acs
        annotation_collections = [
            AnnotationCollection(
                catma_project=catma_project,
                ac_uuid=directory
            ) for directory in os.listdir(collections_directory)
            if get_ac_name(catma_project.uuid, directory) in included_acs
        ]
    elif excluded_acs:      # selects all annotation collections except for the excluded_acs
        annotation_collections = [
            AnnotationCollection(
                catma_project=catma_project,
                ac_uuid=directory
            ) for directory in os.listdir(collections_directory)
            if get_ac_name(catma_project.uuid, directory) not in excluded_acs
        ]
    elif ac_filter_keyword:  # selects annotation collections with the given ac_filter_keyword
        annotation_collections = [
            AnnotationCollection(
                catma_project=catma_project,
                ac_uuid=directory
            ) for directory in os.listdir(collections_directory)
            if ac_filter_keyword in get_ac_name(catma_project.uuid, directory)
        ]
    else:                   # selects all annotation collections
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
        tagset_uuid: str) -> bool:
    """Tests if Tagset has header.json to filter empty Tagsets from loading process.

    Args:
        project_uuid (str): UUID.
        tagset_uuid (str): UUID.

    Returns:
        boolean: True if header.json exists.
    """
    tageset_dir = f'{project_uuid}/tagsets/{tagset_uuid}/header.json'
    if os.path.isfile(tageset_dir):
        return True


def load_tagsets(project_uuid: str) -> Tuple[List[Tagset], Dict[str, Tagset]]:
    """Generates List and Dict of Tagsets.

    Args:
        project_uuid (str): CATMA Project UUID.

    Returns:
        Tuple[List[Tagset], Dict[str, Tagset]]: Tagsets as list and dictionary with UUIDs as keys.
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
        Tuple[List[Text], Dict[Text]]: List and dictionary of documents.
    """
    texts_directory = project_uuid + '/documents/'
    texts = [
        Text(
            project_uuid=project_uuid,
            catma_id=directory
        ) for directory in os.listdir(texts_directory)
        if directory.startswith('D_')
    ]

    texts_dict = {text.title: text for text in texts}
    return texts, texts_dict


class CatmaProject:
    """Class that represents a CATMA Project including all Documents, Tagsets and Annotation Collections.
    
    You can eather load the Project from a local git clone or you load it directly
    from GitLab after generating a gitlab_access_token in the CATMA GUI.
    See the [examples in the docs](https://gitma.readthedocs.io/en/latest/class_project.html#examples) for details.

    Args:

        project_name (str): The CATMA Project name. Defaults to None.
        project_directory (str, optional): The directory where your CATMA Project(s) are located. Defaults to './'
        included_acs (list, optional): All Annotation Collections that should get loaded. If neither any annotation collections are included nor excluded \
            all Annotation Collections get loaded. Default to None.
        excluded_acs (list, optional): All Annotation Collections that should not get loaded. Default to None.
        ac_filter_keyword (str, bool): Only Annotation Collections with the given keyword get loaded.
        load_from_gitlab (bool, optional): Whether the CATMA Project shall be loaded dircetly from the CATMA GitLab. Defaults to False.
        gitlab_access_token (str, optional): The private CATMA GitLab Token. Defaults to None.
        backup_directory (str, optional): The your Project clone should be located. Default to './'.

    Raises:
        FileNotFoundError: If the CATMA Project was not found in the CATMA GitLab.
        FileNotFoundError: If the local or remote CATMA Project were not found.
    """

    def __init__(
            self,
            project_name: str,
            project_directory: str = './',
            included_acs: list = None,
            excluded_acs: list = None,
            ac_filter_keyword: str = None,
            load_from_gitlab: bool = False,
            gitlab_access_token: str = None,
            backup_directory: str = './'):
        # get the current directory to return after loaded the project
        cwd = os.getcwd()

        # Clone CATMA Project
        if load_from_gitlab:
            #: The project's UUID.
            self.uuid: str = load_gitlab_project(
                gitlab_access_token=gitlab_access_token,
                project_name=project_name,
                backup_directory=backup_directory
            )
            project_directory = backup_directory
        else:
            self.uuid: str = get_local_project_uuid(
                project_directory=project_directory,
                project_name=project_name
            )

        #: The project's directory.
        self.project_directory: str = project_directory

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
                tagsets = load_tagsets(
                    project_uuid=self.uuid)

                #: List of gitma.Tagset objects.
                self.tagsets: List[Tagset] = tagsets[0]

                #: Dictionary of the project's tagsets with the UUIDs as keys and gitma.Tagset objects as values.
                self.tagset_dict: Dict[str, Tagset] = tagsets[1]
                print(f'\t Found {len(self.tagsets)} Tagset(s).')
            else:
                self.tagsets, self.tagset_dict = None, None
                print(f'\t Did not found any Tagsets.')

            # Load Texts
            print('Loading Documents ...')
            texts = load_texts(project_uuid=self.uuid)

            #: List of the gitma.Text objects.
            self.texts: List[Text] = texts[0]

            #: Dictionary of the project's texts with titles as keys and gitma.Text objects as values
            self.text_dict: Dict[str, Text] = texts[1]
            print(f'\t Found {len(self.texts)} Document(s).')

            # Load Annotation Collections
            print('Loading Annotation Collections ...')
            annotation_collections = load_annotation_collections(
                catma_project=self,
                included_acs=included_acs,
                excluded_acs=excluded_acs,
                ac_filter_keyword=ac_filter_keyword,
            )
            #: List of gitma.AnnotationCollection objects.
            self.annotation_collections: List[AnnotationCollection] = annotation_collections[0]

            #: Dictionary of the project's annotation collections with their name as keys and gitma.AnnotationCollection objects as values
            self.ac_dict: Dict[str,
                               AnnotationCollection] = annotation_collections[1]

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
    
    from gitma._vizualize import compare_annotation_collections

    from gitma._metrics import get_iaa

    from gitma._gamma import gamma_agreement

    def all_annotations(self) -> Generator[Annotation, None, None]:
        """Generator that yields all annotations as gitma annotation objects.

        Yields:
            Annotation: gitma Annotation object.
        """
        for ac in self.annotation_collections:
            for an in ac.annotations:
                yield an

    def pygamma_table(self, annotation_collections: Union[str, list] = 'all') -> pd.DataFrame:
        """Concatenates annotation collections to pygamma table.

        Args:
            annotation_collections (Union[str, list], optional): List of annotation collections. Defaults to 'all'.

        Returns:
            pd.DataFrame: Concatenated annotation collections as pd.DataFrame in pygamma format.
        """
        if annotation_collections == 'all':
            return pd.concat(
                [ac.to_pygamma_table() for ac in self.annotation_collections]
            )
        else:
            return pd.concat(
                [
                    ac.to_pygamma_table() for ac in self.annotation_collections
                    if ac.name in annotation_collections
                ]
            )

    def merge_annotations(self) -> pd.DataFrame:
        """Concatenes all annotation collections to one pandas data frame and resets index.

        Returns:
            pd.DataFrame: Data frame including all annotation in the CATMA project.
        """
        return pd.concat(
            [ac.df for ac in self.annotation_collections]
        ).reset_index(drop=True)

    def merge_annotations_per_document(self) -> Dict[str, pd.DataFrame]:
        """Merges all annotations per document to one annotation collection.

        Returns:
            Dict[str, pd.DataFrame]: Dictionary with document titles as keys and annotations per\
                document as pandas data frame.
        """
        project_df = self.merge_annotations
        document_acs = {
            document: project_df[project_df['document']
                                 == document].reset_index(drop=True)
            for document in project_df['document'].unique()
        }

        return document_acs

    def stats(self) -> pd.DataFrame:
        """Shows some CATMA Project stats.

        Returns:
            pd.DataFrame: DataFrame with projects stats sorted by the Annotation Collection names.
        """
        ac_stats = [
            {
                'annotation collection': ac.name,
                'document': ac.text.title,
                'annotations': len(ac.annotations),
                'annotator': set([an.author for an in ac.annotations]),
                'tag': set([an.tag.name for an in ac.annotations]),
                'first_annotation': min([an.date for an in ac.annotations]),
                'last_annotation': max([an.date for an in ac.annotations]),
                'uuid': ac.uuid,
            } for ac in self.annotation_collections
            if len(ac.annotations) > 0
        ]

        df = pd.DataFrame(ac_stats).sort_values(
            by=['annotation collection']).reset_index(drop=True)
        return df

    def cooccurrence_network(
        self,
        annotation_collections: Union[str, List[str]] = 'all',
        character_distance: int = 100,
        included_tags: list = None,
        excluded_tags: list = None,
        level: str = 'tag',
        plot_stats: bool = True,
        save_as_gexf: Union[bool, str] = False):
        """Draws cooccurrence network graph for annotations.
         
        Every tag is represented by a node and every edge represents two cooccurent tags.
        You can by the `character_distance` parameter when two annotations are considered cooccurent.
        If you set `character_distance=0` only the tags of overlapping annotations will be represented
        as connected nodes.

        See the [examples in the docs](https://gitma.readthedocs.io/en/latest/class_project.html#plot-a-cooccurrence-network-for-the-annotations-in-your-project) for details about the usage.

        Args:
            annotation_collections (Union[str, List[str]]): List with the names of the included annotation collections.\
                If set to 'all' all annotation collections are included. Defaults to 'all'.
            character_distance (int, optional): In which distance annotations are considered coocurrent. Defaults to 100.
            included_tags (list, optional): List of included tags. Defaults to None.
            excluded_tags (list, optional): List of excluded tags. Defaults to None.
            plot_stats (bool, optional): Whether to return network stats. Defaults to True.
            save_as_gexf (bool, optional): If given any string the network gets saved as Gephi file with the string as filename.
        """
        if isinstance(annotation_collections, list):
            plot_acs = [
                ac for ac in self.annotation_collections
                if ac.name in annotation_collections
            ]
        else:
            plot_acs = self.annotation_collections

        from gitma._network import Network
        nw = Network(
            annotation_collections=plot_acs,
            character_distance=character_distance,
            included_tags=included_tags,
            excluded_tags=excluded_tags,
            level=level
        )
        nw.plot(plot_stats=plot_stats)
        if save_as_gexf:
            nw.to_gexf(filename=f'{save_as_gexf}.gexf')


    def update(self) -> None:
        """Updates local git folder and reloads CatmaProject.

        Warning: This method can only be used if you have [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed.
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
            catma_project=self,
            included_acs=list(self.ac_dict)
        )

        print('Updated the CATMA Project')

        os.chdir(cwd)


if __name__ == '__main__':

    project = CatmaProject(
        project_directory='gitma/test/demo_project/',
        project_uuid='test_corpus_root'
    )
    print(project.stats())
