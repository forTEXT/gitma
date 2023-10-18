import os
import subprocess
import textwrap
from typing import List, Union
from gitma.annotation import Annotation, get_annotation_segments
from gitma._metrics import test_overlap, test_max_overlap, get_overlap_percentage


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


def create_gold_annotations(
        project,
        ac_1_name: str,
        ac_2_name: str,
        gold_ac_name: str,
        excluded_tags: list,
        min_overlap: float = 1.0,
        same_tag: bool = True,
        property_values: str = 'matching',
        push_to_gitlab=False) -> None:
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
    cwd = os.getcwd()

    ac1 = project.ac_dict[ac_1_name]
    ac2 = project.ac_dict[ac_2_name]

    gold_uuid = project.ac_dict[gold_ac_name].uuid

    if not os.path.isdir(f'{project.projects_directory}{project.uuid}/collections/{gold_uuid}/annotations/'):
        os.mkdir(f'{project.projects_directory}{project.uuid}/collections/{gold_uuid}/annotations/')
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
                    annotation_collection_name=gold_ac_name,
                    compare_annotation=compare_annotation
                )

    if push_to_gitlab:
        # upload gold annotations via git
        os.chdir(f'{project.projects_directory}{project.uuid}/collections/{gold_uuid}')
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'new gold annotations'])
        subprocess.run(['git', 'push', 'origin', 'HEAD:master'])

    print(textwrap.dedent(
        f"""
            Found {len(al1)} annotations in Annotation Collection: '{ac_1_name}'.
            Found {len(al2)} annotations in Annotation Collection: '{ac_2_name}'.
            -------------
            Wrote {copied_annotations} gold annotations in Annotation Collection '{gold_ac_name}'.
        """
    ))
    os.chdir(cwd)
