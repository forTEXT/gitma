import subprocess
import os
import json
import gitlab
import pandas as pd
from typing import Dict, List, Tuple, Union
from catma_gitlab.text import Text
from catma_gitlab.tagset import Tagset
from catma_gitlab.annotation import Annotation, get_annotation_segments
from catma_gitlab.annotation_collection import AnnotationCollection
from catma_gitlab.write_annotation import write_annotation_json, find_tag_by_name
from catma_gitlab.vizualize import plot_annotation_progression
from catma_gitlab.metrics import test_overlap, test_max_overlap, get_overlap_percentage


def load_gitlab_project(gitlab_access_token: str, project_name: str) -> str:
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

    # clone the project in current directory
    subprocess.run(
        ['git', 'clone', '--recurse-submodules', project_url])

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
        project_uuid: str,
        included_acs: list = None,
        excluded_acs: list = None) -> Tuple[List[AnnotationCollection], Dict[str, AnnotationCollection]]:
    """Generates List and Dict of CATMA Annotation Collections.

    Args:
        project_uuid (str): CATMA Project UUID
        included_acs (list): All listed Annotation Collections get loaded.
        excluded_acs (list): All listed Annotations Collections don't get loaded.
            If neither icluded nor excluded Annotation Collections are defined, all Annotation Collections get loaded.

    Returns:
        Tuple[List[AnnotationCollection], Dict[str, AnnotationCollection]]: List and Dict of Annotation Collections
    """
    collections_directory = project_uuid + '/collections/'

    if included_acs:
        annotation_collections = [
            AnnotationCollection(
                project_uuid=project_uuid,
                catma_id=directory
            ) for directory in os.listdir(collections_directory)
            if get_ac_name(project_uuid, directory) in included_acs
        ]
    elif excluded_acs:
        annotation_collections = [
            AnnotationCollection(
                project_uuid=project_uuid,
                catma_id=directory
            ) for directory in os.listdir(collections_directory)
            if get_ac_name(project_uuid, directory) not in excluded_acs
        ]
    else:
        annotation_collections = [
            AnnotationCollection(
                project_uuid=project_uuid,
                catma_id=directory
            ) for directory in os.listdir(collections_directory)
        ]

    ac_dict = {
        ac.name: ac for ac in annotation_collections}

    return annotation_collections, ac_dict


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
    ]
    tagset_dict = {tagset.name: tagset for tagset in tagsets}

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


def compare_annotations(
        an1: Annotation,
        al2: List[Annotation],
        min_overlap: float = 1.0,
        same_tag: bool = True) -> Union[Annotation, bool]:
    """Compares a given Annotation with the best machting Annotation in a given list of Annotations.

    Args:
        an1 (Annotation): An Annotation object
        al2 (List[Annotation]): A list of Annotation objects
        min_overlap (float, optional): The minimal overlap percentage. Defaults to 1.0.
        same_tag (bool, optional): Whethe both annotation have to be same tagged. Defaults to True.

    Returns:
        bool: True if Annotation1 (an1) and the best matching annotation in al2 fullfill the criteria.
    """

    an2 = test_max_overlap(
        silver_annotation=an1,
        second_annotator_annotations=al2
    )

    matching_percentage = get_overlap_percentage((an1, an2))

    # test span matching and discontious annotations
    an1_segments = get_annotation_segments(an1.data)
    an2_segments = get_annotation_segments(an2.data)

    if matching_percentage >= min_overlap and an1_segments == an2_segments:
        if same_tag:                        # if tags have to be the same
            if an1.tag.id == an2.tag.id:    # test tag matching
                return an2
            else:
                return False
        else:                               # if tags have not to be the same
            return an2
    else:
        return False


class CatmaProject:
    def __init__(
        self,
        project_directory: str = './',
        project_uuid: str = None,
        included_acs: list = None,
        excluded_acs: list = None,
        load_from_gitlab: bool = False,
        gitlab_access_token: str = None,
        project_name: str = None
    ):
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

        Raises:
            Exception: If the local or remote CATMA Project were not found.
        """
        # Clone CATMA Project
        if load_from_gitlab:
            self.uuid = load_gitlab_project(
                gitlab_access_token=gitlab_access_token,
                project_name=project_name
            )
        else:
            self.uuid = project_uuid

        # get the current directory to return after loaded the project
        cwd = os.getcwd()
        self.project_directory = project_directory
        os.chdir(self.project_directory)

        try:
            # Load Tagsets
            # test if any tagsets exists
            if os.path.isdir(project_uuid + '/tagsets/'):
                self.tagsets, self.tagset_dict = load_tagsets(
                    project_uuid=self.uuid)
            else:
                self.tagsets, self.tagset_dict = None, None

            # Load Texts
            self.texts, self.text_dict = load_texts(project_uuid=self.uuid)

            # Load Annotation Collections
            self.annotation_collections, self.ac_dict = load_annotation_collections(
                project_uuid=self.uuid,
                included_acs=included_acs,
                excluded_acs=excluded_acs
            )

        except FileNotFoundError:
            if load_from_gitlab:
                raise Exception(
                    """
Couldn't find your project!
Probably cloning the project didn't work.
Make sure that the project name and your access token are correct.
                    """
                )
            else:
                raise Exception(
                    """
Couldn't find your project!
Probably the project directory or uuid were not correct.
                    """
                )

        os.chdir(cwd)

    def create_gold_annotations(
            self,
            ac_1_name: str,
            ac_2_name: str,
            gold_ac_name: str,
            excluded_tags: list,
            min_overlap: float = 1.0,
            same_tag: bool = True,
            property_values: str = 'matching',
            push_to_gitlab=False):
        """Searches for matching annotations in 2 AnnotationCollections and copies all matches in a third AnnotationCollection.
        By default only matching Property Values get copied.

        Args:
            ac_1_name (str): AnnotationCollection 1 Name.
            ac_2_name (str): AnnnotationCollection 2 Name.
            gold_ac_name (str): AnnotationCollection Name for Gold Annotations.
            excluded_tags (list, optional): Annotations with this Tags will not be included in the Gold Annotations. Defaults to None.
            min_overlap (float, optional): The minimal overlap to genereate a gold annotation. Defaults to 1.0.
            same_tag (bool, optional): Whether both annotations need to be the same tag. Defaults to True.
            property_values (str, optional): Whether only matching Property Values from AnnonationCollection 1 shall be copied.
                Default to 'matching'. Further options: 'none'.
        """
        cwd = os.getcwd()
        os.chdir(f'{self.project_directory}{self.uuid}/')

        ac1 = self.ac_dict[ac_1_name]
        ac2 = self.ac_dict[ac_2_name]

        gold_uuid = self.ac_dict[gold_ac_name].uuid

        if not os.path.isdir(f'collections/{gold_uuid}/annotations/'):
            os.mkdir(f'collections/{gold_uuid}/annotations/')
        else:
            for f in os.listdir(f'collections/{gold_uuid}/annotations/'):
                # removes all files in gold annotation collection to prevent double gold annotations:
                os.remove(f'collections/{gold_uuid}/annotations/{f}')

        al1 = [an for an in ac1.annotations if an not in excluded_tags]
        al2 = [an for an in ac2.annotations if an not in excluded_tags]

        copied_annotations = 0
        for an in al1:
            # get all overlapping annotations
            overlapping_annotations = [
                a for a in al2 if test_overlap(
                    an1=an,
                    an2=a
                )
            ]

            # test if any annotation from ac2 matches the annotation from ac1
            if len(overlapping_annotations) > 0:
                an2 = compare_annotations(
                    an1=an,
                    al2=overlapping_annotations,
                    min_overlap=min_overlap,
                    same_tag=same_tag
                )

                # get best matching annotation and compare tag
                compare_annotation = an2 if property_values == 'matching' else None
                if an2:
                    copied_annotations += 1

                    # copy annotation
                    an.copy(
                        annotation_collection=gold_uuid,
                        compare_annotation=compare_annotation)

        if push_to_gitlab:
            # upload gold annotations via git
            os.chdir(f'collections/{gold_uuid}')
            subprocess.run(['git', 'add', '.'])
            subprocess.run(['git', 'commit', '-m', 'new gold annotations'])
            subprocess.run(['git', 'push', 'origin', 'HEAD:master'])

        print(
            f"""
            Found {len(al1)} annotations in Annotation Collection: '{ac_1_name}'.
            Found {len(al2)} annotations in Annotation Collection: '{ac_2_name}'.
            -------------
            Wrote {copied_annotations} gold annotations in Annotation Collection '{gold_ac_name}' and pushed the new annotations to CATMA GitLab.
            """
        )
        os.chdir(cwd)

    def write_annotation(
            self, annotation_collection_name: str, tagset_name: str, text_title: str, tag_name: str,
            start_points: list, end_points: list, property_annotations: dict, author: str):

        cwd = os.getcwd()
        os.chdir(self.project_directory)

        write_annotation_json(
            project_uuid=self.uuid,
            annotation_collection=self.ac_dict[annotation_collection_name],
            tagset=self.tagset_dict[tagset_name],
            text=self.text_dict[text_title],
            tag=find_tag_by_name(self.tagset_dict[tagset_name], tag_name),
            start_points=start_points,
            end_points=end_points,
            property_annotations=property_annotations,
            author=author
        )

        os.chdir(cwd)

    def iaa(self, ac1: str, ac2: str, tag_filter=None, filter_both_ac=False, level='tag'):
        """
        Computes Cohen's Kappa and Krippendorf's Alpha for 2 Annotation Collections.
        """
        from catma_gitlab.metrics import get_iaa
        get_iaa(
            ac1=self.ac_dict[ac1],
            ac2=self.ac_dict[ac2],
            tag_filter=tag_filter,
            filter_both_ac=filter_both_ac,
            level=level
        )

    def plot_progression(self, ac_filter: list = None):
        plot_annotation_progression(self, ac_filter=ac_filter)

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
        self.annotation_collections, self.ac_dict = load_annotations(
            project_uuid=self.uuid)

        print('Updated the CATMA Project')

        os.chdir(cwd)
