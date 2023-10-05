import subprocess
import os
import json
import textwrap
import gitlab
import pygit2
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Union, Generator
from gitma.text import Text
from gitma.tagset import Tagset
from gitma.annotation_collection import AnnotationCollection
from gitma.annotation import Annotation
from gitma.tag import Tag
from gitma._write_annotation import write_annotation_json
from gitma._gold_annotation import create_gold_annotations
from gitma._vizualize import plot_interactive, plot_annotation_progression
from gitma._metrics import get_annotation_pairs, get_iaa_data, get_confusion_matrix, gamma_agreement


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
    pygit2.clone_repository(
        url=project_url,
        path=backup_directory + project_uuid,
        bare=False,
        callbacks=callbacks
    )

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
    """Gets an annotation collection's name.

    Args:
        project_uuid (str): CATMA GitLab root project UUID
        directory (str): annotation collection directory
        test_positive (bool, optional): what should be returned if it is intrinsic markup. Defaults to True.

    Returns:
        str: annotation collection name
    """
    with open(f'{project_uuid}/collections/{directory}/header.json', 'r', encoding='utf-8', newline='') as header_input:
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
            If neither included nor excluded Annotation Collections are defined, all Annotation Collections get loaded.

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
            project_root_directory=project_uuid,
            tagset_uuid=directory
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
            project_root_directory=project_uuid,
            document_uuid=directory
        ) for directory in os.listdir(texts_directory)
        if directory.startswith('D_')
    ]

    texts_dict = {text.title: text for text in texts}
    return texts, texts_dict


class CatmaProject:
    """Class that represents a CATMA project including all documents, tagsets and annotation collections.
    
    You can either load the project from a local Git clone or you can load it directly
    from GitLab after generating an access token in the CATMA GUI.
    See the [examples in the docs](https://gitma.readthedocs.io/en/latest/class_project.html#examples) for details.

    Args:

        project_name (str): The CATMA project name. Defaults to None.
        project_directory (str, optional): The directory where your CATMA projects are located. Defaults to './'
        included_acs (list, optional): All annotation collections that should get loaded. If annotation collections are neither included nor excluded \
            all annotation collections get loaded. Defaults to None.
        excluded_acs (list, optional): Annotation collections that should not get loaded. Defaults to None.
        ac_filter_keyword (str, bool): Only annotation collections with the given keyword get loaded.
        load_from_gitlab (bool, optional): Whether the CATMA project should be loaded directly from CATMA's GitLab backend. Defaults to False.
        gitlab_access_token (str, optional): The private CATMA GitLab access token. Defaults to None.
        backup_directory (str, optional): The directory where your project clone should be located. Defaults to './'.

    Raises:
        FileNotFoundError: If the local or remote CATMA project was not found.
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
        # get the current directory, to return to after loading the project
        cwd = os.getcwd()

        # Clone the CATMA project
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

        #: The project's name.
        self.name: str = self.uuid[43:-5]

        try:
            os.chdir(self.project_directory)
        except FileNotFoundError:
            raise FileNotFoundError(
                f"The CATMA project \"{self.name}\" could not been found in this directory: {self.project_directory}\n\
                    -> Make sure the project clone worked properly and that the project directory is correct")

        try:
            # Load tagsets
            print('Loading tagsets ...')
            if os.path.isdir(self.uuid + '/tagsets/'):
                tagsets = load_tagsets(
                    project_uuid=self.uuid)

                #: List of gitma.Tagset objects.
                self.tagsets: List[Tagset] = tagsets[0]

                #: Dictionary of the project's tagsets with the UUIDs as keys and gitma.Tagset objects as values.
                self.tagset_dict: Dict[str, Tagset] = tagsets[1]
                print(f'\t Found {len(self.tagsets)} tagset(s).')
            else:
                self.tagsets, self.tagset_dict = None, None
                print(f'\t Did not find any tagsets.')

            # Load texts
            print('Loading documents ...')
            texts = load_texts(project_uuid=self.uuid)

            #: List of the gitma.Text objects.
            self.texts: List[Text] = texts[0]

            #: Dictionary of the project's texts with titles as keys and gitma.Text objects as values
            self.text_dict: Dict[str, Text] = texts[1]
            print(f'\t Found {len(self.texts)} document(s).')

            # Load annotation collections
            print('Loading annotation collections ...')
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

        except FileNotFoundError:
            raise FileNotFoundError(
                f"Some components of your CATMA project could not be loaded."
            )
        os.chdir(cwd)

    def __repr__(self):
        documents = [text.title for text in self.texts]
        tagsets = [tagset.name for tagset in self.tagsets]
        acs = [ac.name for ac in self.annotation_collections]
        return f"CatmaProject(\n\tName: {self.name},\n\tDocuments: {documents},\n\tTagsets: {tagsets},\n\tAnnotationCollections: {acs})"

    def to_json(self,
        annotation_collections: Union[List[str], str] = 'all',
        rename_dict: Union[Dict[str, str], None] = None,
        included_tags: Union[list, None] = None,
        directory: str = './') -> None:
        """Saves all annotations as a single JSON file.

        Args:
            annotation_collections (Union[List[str], str], optional): Parameter to define the exported annotation collections. Defaults to 'all'.
            rename_dict (Union[Dict[str, str], None], optional): Dictionary to rename annotation collections. Defaults to None.
            included_tags (Union[list, None]): Tags included in the annotations list. If `None` all tags are included. Defaults to None.
            directory (str): Backup directory. Defaults to './'
        """
        
        if annotation_collections == 'all':
            annotation_collections = self.annotation_collections
        else:
            annotation_collections = [ac for ac in self.annotation_collections if ac.name in annotation_collections]

        if not rename_dict:
            rename_dict = {ac.name: ac.name for ac in annotation_collections}

        output_dict = {}
        for ac in annotation_collections:
            if ac.text.title not in output_dict:
                output_dict[ac.text.title] = {rename_dict[ac.name]: ac.to_list(tags=included_tags)}
            else:
                output_dict[ac.text.title][rename_dict[ac.name]] = ac.to_list(tags=included_tags)

        with open(f'{directory}{self.name}.json', 'w', encoding='utf-8', newline='') as json_output:
            json_output.write(json.dumps(output_dict))

    def update(self) -> None:
        """Updates local git folder and reloads CatmaProject.

        Warning: This method can only be used if you have [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) installed.
        """
        cwd = os.getcwd()
        os.chdir(f'{self.project_directory}{self.uuid}/')

        subprocess.run(['git', 'pull'])

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

    def annotations(self) -> Generator[Annotation, None, None]:
        """Generator that yields all annotations as gitma.annotation.Annotation objects.

        Yields:
            Annotation: gitma.annotation.Annotation
        """
        for ac in self.annotation_collections:
            for an in ac.annotations:
                yield an

    def all_tags(self) -> Generator[Tag, None, None]:
        """Generator that yields all tags as gitma.tag.Tag objects.

        Yields:
            Tag: gitma.tag.Tag
        """
        for tagset in self.tagsets:
            for tag in tagset.tags:
                yield tag

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

    def write_annotation_json(
        self,
        annotation_collection_name: str,
        tagset_name: str,
        text_title: str,
        tag_name: str,
        start_points: list,
        end_points: list,
        property_annotations: dict,
        author: str):
        """Function to write a new annotation into a given CatmaProject.

        Args:
            project (CatmaProject): A CatmaProject object.
            annotation_collection_name (str): The annotation collections name
            tagset_name (str): The tagsets name
            text_title (str): The text title
            tag_name (str): The tags name
            start_points (list): The annotation span start point
            end_points (list): The annotation span end point
            property_annotations (dict): dictionary with property annotations
            author (str): the annotations author
        """
        write_annotation_json(
            project=self,
            annotation_collection_name=annotation_collection_name,
            tagset_name=tagset_name,
            text_title=text_title,
            tag_name=tag_name,
            start_points=start_points,
            end_points=end_points,
            property_annotations=property_annotations,
            author=author
        )

    def create_gold_annotations(
            self,
            ac_1_name: str,
            ac_2_name: str,
            gold_ac_name: str,
            excluded_tags: list = None,
            min_overlap: float = 1.0,
            same_tag: bool = True,
            property_values: str = 'none',
            push_to_gitlab: bool = False):
        
        """Searches for matching annotations in 2 AnnotationCollections and copies all matches in a third AnnotationCollection.
        By default only matching Property Values get copied.

        Args:
            ac_1_name (str): AnnotationCollection 1 Name.
            ac_2_name (str): AnnnotationCollection 2 Name.
            gold_ac_name (str): AnnotationCollection Name for Gold Annotations.
            excluded_tags (list, optional): Annotations with this Tags will not be included in the Gold Annotations. Defaults to None.
            min_overlap (float, optional): The minimal overlap to genereate a gold annotation. Defaults to 1.0.
            same_tag (bool, optional): Whether both annotations need to be the same tag. Defaults to True.
            property_values (str, optional): Whether only matching Property Values from AnnonationCollection 1 shall be copied.\
                Default to 'matching'. Further options: 'none'.
            push_to_gitlab (bool, optional): Whether the gold annotations shall be uploaded to the CATMA GitLab. Default to False.
        """
        create_gold_annotations(
            project=self,
            ac_1_name=ac_1_name,
            ac_2_name=ac_2_name,
            gold_ac_name=gold_ac_name,
            excluded_tags=excluded_tags,
            min_overlap=min_overlap,
            same_tag=same_tag,
            property_values=property_values,
            push_to_gitlab=push_to_gitlab
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

    def plot_annotation_progression(self) -> go.Figure:
        """Plot the annotation progression for every annotator in a CATMA project.

        Returns:
            go.Figure: Plotly scatter plot.
        """
        return plot_annotation_progression(project=self)

    def plot_interactive(self, color_col: str = 'annotation collection') -> go.Figure:
        """This function generates one Plotly scatter plot per annotated document in a CATMA project.
        By default the colors represent the annotation collections.
        By that they can be deactivated with the interactive legend.

        Args:
            color_col (str, optional): 'annotation collection', 'annotator', 'tag' or any property with the prefix 'prop:'. Defaults to 'annotation collection'.

        Returns:
            go.Figure: Plotly scatter plot.
        """
        return plot_interactive(catma_project=self, color_col=color_col)

    def plot_annotations(self, color_col: str = 'annotation collection') -> go.Figure:
        """This function generates one Plotly scatter plot per annotated document in a CATMA project.
        By default the colors represent the annotation collections.
        By that they can be deactivated with the interactive legend.

        Args:
            color_col (str, optional): 'annotation collection', 'annotator', 'tag' or any property with the prefix 'prop:'. Defaults to 'annotation collection'.

        Returns:
            go.Figure: Plotly scatter plot.
        """
        return plot_interactive(catma_project=self, color_col=color_col)

    def cooccurrence_network(
        self,
        annotation_collections: Union[str, List[str]] = 'all',
        character_distance: int = 100,
        included_tags: list = None,
        excluded_tags: list = None,
        level: str = 'tag',
        plot_stats: bool = False,
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
            level (str, optional): 'tag' or any property name with 'prop:' as prefix. Defaults to 'tag'.
            plot_stats (bool, optional): Whether to return network stats. Defaults to False.
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

        if save_as_gexf:
            nw.to_gexf(filename=f'{save_as_gexf}.gexf')

        return nw.plot(plot_stats=plot_stats)

    def disagreement_network(
        self,
        annotation_collections: Union[str, List[str]] = 'all',
        included_tags: list = None,
        excluded_tags: list = None,
        level: str = 'tag',
        plot_stats: bool = False,
        save_as_gexf: Union[bool, str] = False):
        """Draws disagreement network.

        Every edge in the network represents two overlapping annotations from different annotation collections
        and with different tags or property values. 

        Args:
            annotation_collections (Union[str, List[str]], optional): List with the names of the included annotation collections.\
                If set to 'all' all annotation collections are included. Defaults to 'all'.
            included_tags (list, optional): List of included tags. Defaults to None.
            excluded_tags (list, optional): List of excluded tags. Defaults to None.
            level (str, optional): 'tag' or any property name with 'prop:' as prefix. Defaults to 'tag'.
            plot_stats (bool, optional): Whether to return network stats. Defaults to False.
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
            edge_func='overlapping',
            included_tags=included_tags,
            excluded_tags=excluded_tags,
            level=level
        )
        
        if save_as_gexf:
            nw.to_gexf(filename=f'{save_as_gexf}.gexf')

        return nw.plot(plot_stats=plot_stats)

    def compare_annotation_collections(
        self,
        annotation_collections: List[str],
        color_col: str = 'tag') -> go.Figure:
        """Plots annotations of multiple annotation collections of the same texts as line plot.

        Args:
            annotation_collections (list): A list of annotation collection names. 
            color_col (str, optional): Either 'tag' or one property name with prefix 'prop:'. Defaults to 'tag'.

        Raises:
            ValueError: If one of the annotation collection's names does not exist.

        Returns:
            go.Figure: Plotly Line Plot.
        """
        from gitma._vizualize import compare_annotation_collections
        return compare_annotation_collections(
            catma_project=self,
            annotation_collections=annotation_collections,
            color_col=color_col
        )

    def get_iaa(
        self,
        ac1_name: str,
        ac2_name: str,
        tag_filter: list = None,
        filter_both_ac: bool = False,
        level: str = 'tag',
        include_empty_annotations: bool = True,
        distance: str = 'binary',
        return_as_dict: bool = False) -> None:
        """Computes Inter Annotator Agreement for 2 Annotation Collections.
        See the [demo notebook](https://github.com/forTEXT/gitma/blob/main/demo_notebooks/inter_annotator_agreement.ipynb)
        for details.

        Args:
            ac1_name (str): AnnotationCollection name to be compared.
            ac2_name (str): AnnotationCollection name to be compared with.
            tag_filter (list, optional): Which Tags should be included. If None all are included. Default to None.
            filter_both_ac (bool, optional): Whether the tag filter shall be aplied to both annotation collections.\
                Defaults to False.
            level (str, optional): Whether the Annotation Tag or a specified Property should be compared.\
                Defaults to 'tag'.
            include_empty_annotations (bool, optionale): If `False` only annotations with a overlapping annotation in the second collection\
                get included. Defaults to True.
            distance (str, optional): The IAA distance function. Either 'binary' or 'interval'.\
            See the [NLTK API](https://www.nltk.org/api/nltk.metrics.html) for further informations. Defaults to 'binary'.
        """
        from nltk.metrics.agreement import AnnotationTask
        from nltk.metrics import interval_distance, binary_distance

        if distance == 'interval':
            distance_function = interval_distance
        else:
            distance_function = binary_distance

        ac1 = self.ac_dict[ac1_name]
        ac2 = self.ac_dict[ac2_name]

        # create pairs of best matching annotations
        annotation_pairs = get_annotation_pairs(
            ac1=ac1,
            ac2=ac2,
            tag_filter=tag_filter,
            filter_both_ac=filter_both_ac,
            property_filter=level.replace(
                'prop:', '') if 'prop:' in level else None
        )

        # transform annotation pairs to data format the nltk AnnotationTask class takes as input
        data = list(get_iaa_data(annotation_pairs, level=level, include_empty_annotations=include_empty_annotations))

        annotation_task = AnnotationTask(data=data, distance=distance_function)

        try:
            pi = annotation_task.pi()
            kappa = annotation_task.kappa()
            alpha = annotation_task.alpha()
        except ZeroDivisionError:
            print(f"Couldn't find compute IAA for {level} due to missing overlapping annotations with the given settings.")
            pi, kappa, alpha = (0, 0, 0)

        print(textwrap.dedent(
            f"""
            Results for "{level}"
            -------------{len(level) * '-'}-
            Scott's Pi:          {pi}
            Cohen's Kappa:       {kappa}
            Krippendorf's Alpha: {alpha}
            ===============================================
            """
        ))

        if return_as_dict:
            return {
                "Scott's Pi": pi,
                "Cohen's Kappa": kappa,
                "Krippendorf's Alpha": alpha
            }
        else:
            print(textwrap.dedent(
                f"""Confusion Matrix
                -------
                """
            ))
            return get_confusion_matrix(pair_list=annotation_pairs, level=level)

    def gamma_agreement(
        self,
        annotation_collections: List[AnnotationCollection],
        alpha: int = 3,
        beta: int = 1,
        delta_empty: float = 0.01,
        n_samples: int = 30,
        precision_level: int = 0.01):
        gamma_agreement(
            project=self,
            annotation_collections=annotation_collections,
            alpha=alpha,
            beta=beta,
            delta_empty=delta_empty,
            n_samples=n_samples,
            precision_level=precision_level
        )

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


if __name__ == '__main__':

    project = CatmaProject(
        project_directory='gitma/test/demo_project/',
        project_uuid='test_corpus_root'
    )
    print(project.stats())
