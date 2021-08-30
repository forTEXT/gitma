import subprocess
import os
import json
import gitlab
from typing import List, Union
from catma_gitlab.text_class import Text
from catma_gitlab.tagset_class import Tagset
from catma_gitlab.annotation_class import Annotation, get_annotation_segments
from catma_gitlab.annotation_collection_class import AnnotationCollection
from catma_gitlab.write_annotation import write_annotation_json, find_tag_by_name
from catma_gitlab.catma_gitlab_vizualize import plot_annotation_progression
from catma_gitlab.catma_gitlab_metrics import test_overlap, test_max_overlap, get_overlap_percentage


def load_gitlab_project(private_gitlab_token: str, project_name: str, project_dir: str) -> str:
    """Downloads a CATMA Project with git

    Args:
        private_gitlab_token (str): GitLab Access Token.
        project_name (str): The CATMA Project name.
        project_dir (str): Where to locate the CATMA Project.

    Raises:
        Exception: If no CATMA Project with the given name could be found.

    Returns:
        str: The CATMA Project UUID
    """
    gl = gitlab.Gitlab(
        url='https://git.catma.de/',
        private_token=private_gitlab_token
    )

    try:
        project_gitlab_id = gl.projects.list(search=project_name)[0].id
    except IndexError:
        raise Exception("Couldn't find the given CATMA Project!")

    project_uuid = gl.projects.get(id=project_gitlab_id).name
    project_url = f"https://git.catma.de/{project_uuid[:-5]}/{project_uuid}.git"

    # clone the project in current direction
    subprocess.call(
        ['git', 'clone', '--recurse-submodules', project_url])

    return project_uuid


def test_intrinsic(project_uuid: str, direction: str, test_positive=True) -> bool:
    """Tests if a Catma Annotation Collection is intrinsic markup.

    Args:
        project_uuid (str): CATMA gitlab root project uuids
        direction (str): annotation collection direction
        test_positive (bool, optional): what should be returned if it is intrinsic markup. Defaults to True.

    Returns:
        bool: if its annotation collection is intrinsic markup returns parameter test_positive
    """
    with open(f'{project_uuid}/collections/{direction}/header.json', 'r') as header_input:
        header_dict = json.load(header_input)

    if header_dict['name'] == 'Intrinsic Markup':
        return test_positive


def write_ac_header(
        direction: str,
        author: str,
        doc_id: str,
        doc_version: str,
        ac_name: str = None):
    header_str = {
        "author": author,
        "description": "",
        "name": ac_name,
        "publisher": None,
        "sourceDocumentId": doc_id,
        "sourceDocumentVersion": doc_version
    }

    with open(direction, 'w') as json_output:
        json_output.write(json.dumps(header_str))


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
        project_direction: str = '.',
        project_uuid: str = None,
        filter_intrinsic_markup: bool = True,
        load_from_gitlab: bool = False,
        private_gitlab_token: str = None,
        project_name: str = None
    ):
        """This Project represents a CATMA Project including all Documents, Tagsets
        and Annotation Collections.
        You can eather load the Project from a local git clone or you load it directly
        from GitLab after generating a private_gitlab_token in the CATMA GUI.

        Args:
            project_direction (str, optional): [description]. Defaults to '.'.
            project_uuid (str, optional): [description]. Defaults to None.
            filter_intrinsic_markup (bool, optional): [description]. Defaults to True.
            load_from_gitlab (bool, optional): [description]. Defaults to False.
            private_gitlab_token (str, optional): [description]. Defaults to None.
            project_name (str, optional): [description]. Defaults to None.

        Raises:
            Exception: [description]
        """
        # Clone CATMA Project
        if load_from_gitlab:
            self.uuid = load_gitlab_project(
                private_gitlab_token=private_gitlab_token,
                project_name=project_name
            )
        else:
            self.uuid = project_uuid

        # get the current direction to return after loaded the project
        cwd = os.getcwd()
        self.project_direction = project_direction
        os.chdir(self.project_direction)

        # Load Tagsets
        tagsets_direction = project_uuid + '/tagsets/'
        self.tagsets = [
            Tagset(
                project_uuid=project_uuid,
                catma_id=direction
            ) for direction in os.listdir(tagsets_direction)
        ]
        self.tagset_dict = {tagset.name: tagset for tagset in self.tagsets}

        # Load Texts
        texts_direction = project_uuid + '/documents/'
        self.texts = [
            Text(
                project_uuid=project_uuid,
                catma_id=direction
            ) for direction in os.listdir(texts_direction)
        ]
        self.text_dict = {text.title: text for text in self.texts}

        # Load Annotation Collections
        collections_direction = project_uuid + '/collections/'
        self.annotation_collections = [
            AnnotationCollection(
                project_uuid=project_uuid,
                catma_id=direction
            ) for direction in os.listdir(collections_direction)
            if not test_intrinsic(
                project_uuid,
                direction,
                filter_intrinsic_markup
            )
        ]
        self.ac_dict = {
            ac.name: ac for ac in self.annotation_collections}

        os.chdir(cwd)

    def create_gold_annotations(
            self,
            ac_1_name: str,
            ac_2_name: str,
            gold_ac_name: str,
            excluded_tags: list,
            min_overlap: float = 1.0,
            same_tag: bool = True,
            property_values: str = 'matching'):
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
        os.chdir(f'{self.project_direction}{self.uuid}/')

        ac1 = self.ac_dict[ac_1_name]
        ac2 = self.ac_dict[ac_2_name]

        gold_uuid = self.ac_dict[gold_ac_name].uuid

        if not os.path.isdir(f'collections/{gold_uuid}/annotations/'):
            os.mkdir(f'collections/{gold_uuid}/annotations/')

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

            # get best matching annotation and compare tag
            an2 = compare_annotations(
                an1=an,
                al2=overlapping_annotations,
                min_overlap=min_overlap,
                same_tag=same_tag
            )

            compare_annotation = an2 if property_values == 'matching' else None
            if an2:
                copied_annotations += 1
                an.copy(
                    annotation_collection=gold_uuid,
                    compare_annotation=compare_annotation)

        # os.chdir(f'collections/{gold_uuid}')
        # subprocess.call(['git', 'add', '.'])
        # subprocess.call(['git', 'commit', '-m', 'new gold annotations'])
        # subprocess.call(['git', 'push', 'origin' 'HEAD:master'])

        print(
            f"""
            Found {len(al1)} annotations in Annotation Collection: '{ac_1_name}'.
            Found {len(al2)} annotations in Annotation Collection: '{ac_2_name}'.
            -------------
            Wrote {copied_annotations} gold annotations in Annotation Collection '{gold_ac_name}'.
            """
        )
        os.chdir(cwd)

    def write_annotation(
            self, annotation_collection_name: str, tagset_name: str, text_title: str, tag_name: str,
            start_points: list, end_points: list, property_annotations: dict, author: str):

        cwd = os.getcwd()
        os.chdir(self.project_direction)

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
        from catma_gitlab.catma_gitlab_metrics import get_iaa
        get_iaa(
            ac1=self.ac_dict[ac1],
            ac2=self.ac_dict[ac2],
            tag_filter=tag_filter,
            filter_both_ac=filter_both_ac,
            level=level
        )

    def plot_progression(self, ac_filter: list = None):
        plot_annotation_progression(self, ac_filter=ac_filter)
