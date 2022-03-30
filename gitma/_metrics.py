from ast import AnnAssign
import os
import numpy as np
import pandas as pd
import textwrap
from typing import List, Tuple
from gitma.annotation import Annotation
from gitma.annotation_collection import AnnotationCollection


def filter_ac_by_tag(
        ac1: AnnotationCollection,
        ac2: AnnotationCollection,
        tag_filter: list = None,
        filter_both_ac: bool = True) -> Tuple[List[Annotation]]:
    """Returns lists of annotations filtered by tags.
    If `filter_both_ac=False` only the first collection's annotations get filtered.

    Args:
        ac1 (AnnotationCollection): First annotation collection.
        ac2 (AnnotationCollection): Second annotation collection.
        tag_filter (list, optional): The list of tags to be included. Defaults to None.
        filter_both_ac (bool, optional): If `True` both collections get filtered . Defaults to True.

    Returns:
        Tuple[List[Annotation]]: Two filtered list of annotations.
    """
    if tag_filter:
        ac1_annotations = [
            an for an in ac1.annotations if an.tag.name in tag_filter]
        if filter_both_ac:
            ac2_annotations = [
                an for an in ac2.annotations if an.tag.name in tag_filter]
        else:
            ac2_annotations = ac2.annotations
    else:
        ac1_annotations = ac1.annotations
        ac2_annotations = ac2.annotations

    return ac1_annotations, ac2_annotations


def get_same_text(
    annotation_list1: List[Annotation],
    annotation_list2: List[Annotation]) -> Tuple[List[Annotation]]:
    """All text parts annotated only by one annotator get excluded.

    Args:
        annotation_list1 (List[Annotation]): Annotations from first collection.
        annotation_list2 (List[Annotation]): Annotations from second collection.

    Returns:
        Tuple[List[Annotation]]: Annotations from both collections.
    """
    ac1 = [an for an in annotation_list1 if an.start_point <=
           annotation_list2[-1].start_point]
    ac2 = [an for an in annotation_list2 if an.start_point <=
           annotation_list1[-1].end_point]
    return ac1, ac2


def test_max_overlap(
    silver_annotation: Annotation,
    second_annotator_annotations: List[Annotation]) -> Annotation:
    """Looks for best matching Annotation in second annotator annotations.

    Args:
        silver_annotation (Annotation): Annotation that will be matched
        second_annotator_annotations (list): List of Annotations

    Returns:
        Annotation: Annotation Object
    """

    start_span = [abs(an.start_point - silver_annotation.start_point)
                  for an in second_annotator_annotations]
    end_span = [abs(an.end_point - silver_annotation.end_point)
                for an in second_annotator_annotations]

    # sum start span and end span
    sum_span = [an + end_span[index] for index, an in enumerate(start_span)]

    # return annotation with minimal sum span
    return second_annotator_annotations[sum_span.index(min(sum_span))]


def test_overlap(an1: Annotation, an2: Annotation) -> bool:
    """Test if annotation 2 starts or ends within annotations 1 span.

    Args:
        an1 (Annotation): First annotation.
        an2 (Annotation): Second annotation.

    Returns:
        bool: True if any overlap exists.
    """
    # test if an2 starts before or in an2
    start_match = an1.start_point <= an2.start_point < an1.end_point

    # test if an2 ends in or with an1
    end_match = an1.start_point < an2.end_point <= an1.end_point

    # test if an2 starts before and ends after an1 -> includes an1
    included_match = an2.start_point < an1.start_point and an2.end_point > an1.end_point

    if start_match or end_match or included_match:
        return True


def get_overlap_percentage(an_pair: List[Annotation]) -> float:
    """Computes the overlap percentage of two annotations by averaging
    the overlapping proportion of both annotation spans.

    Args:
        an_pair (List[Annotation]): Two overlapping annotations.

    Returns:
        float: Overlap percentage between 0 and 1.0.
    """
    an1 = an_pair[0]
    an2 = an_pair[1]

    start_overlap = max([an1.start_point, an2.start_point])
    end_overlap = min([an1.end_point, an2.end_point])

    overlap_span = end_overlap - start_overlap

    start_min = min([an1.start_point, an2.start_point])
    end_max = max([an1.end_point, an2.end_point])

    full_span = end_max - start_min

    diff_percentage = overlap_span / full_span
    return diff_percentage


def get_confusion_matrix(pair_list: List[Tuple[Annotation]], level: str = 'tag') -> pd.DataFrame:
    """Generates confusion matrix for two 

    Args:
        pair_list (List[Tuple[Annotation]]): List of overlapping annotations as tuples.
        level (str, optional): 'tag' or any property with prefix 'prop:' in the annotation collections.\
            Defaults to 'tag'.

    Returns:
        pd.DataFrame: Confusion matrix as pandas data frame.
    """
    if level == 'tag':
        tags = set(
            [p[0].tag.name for p in pair_list] +
            [p[1].tag.name for p in pair_list]
        )
        # dict of dict to count the tag permutations
        tag_dict = {tag: {t: 0 for t in tags} for tag in tags}
        for pair in pair_list:
            an1, an2 = pair[0], pair[1]
            tag_dict[an1.tag.name][an2.tag.name] += 1
    else:
        level = level.replace('prop:', '')
        tags = set(
            [p[0].properties[level][0] for p in pair_list] +
            [p[1].properties[level][0] for p in pair_list]
        )
        # dict of dict to count the tag permutations
        tag_dict = {tag: {t: 0 for t in tags} for tag in tags}
        for pair in pair_list:
            an1, an2 = pair[0], pair[1]
            tag_dict[an1.properties[level][0]][an2.properties[level][0]] += 1

    return pd.DataFrame(tag_dict)


class EmptyTag:
    """Helper class for missing annotations.
    """
    def __init__(self):
        self.name = '#None#'


class EmptyAnnotation:
    """Helper class for missing annotations.

    Args:
        start_point (int): Text pointer.
        end_point (int): Text pointer.
        property_dict (dict): Property dictionary
    """
    def __init__(self, start_point: int, end_point: int, property_dict: dict):
        self.start_point = start_point
        self.end_point = end_point
        self.tag = EmptyTag()
        self.properties = property_dict


def get_annotation_pairs(
        ac1: AnnotationCollection,
        ac2: AnnotationCollection,
        tag_filter: list = None,
        filter_both_ac: bool = False,
        property_filter: str = None) -> List[Tuple[Annotation]]:
    """Returns list of all overlapping annotations in two annotation collections.
    tag_filter can be defined as list of tag names if not all annotations are included.


    Args:
        ac1 (AnnotationCollection): First annotation collection.
        ac2 (AnnotationCollection): Second annotation collection.
        tag_filter (list, optional): List of included tag names. Defaults to None.
        filter_both_ac (bool, optional): If `True` both annotation collections get filterde.\
            Defaults to False.
        property_filter (str, optional): List of included properties. Defaults to None.

    Returns:
        List[Tuple[Annotation]]: List of paired annotations.
    """
    ac1_annotations, ac2_annotations = filter_ac_by_tag(ac1=ac1, ac2=ac2, tag_filter=tag_filter,
                                                        filter_both_ac=filter_both_ac)
    ac1_annotations, ac2_annotations = get_same_text(
        ac1_annotations, ac2_annotations)

    if property_filter:
        ac1_annotations = [
            an for an in ac1_annotations
            if property_filter in an.properties             # test if property exists
            and len(an.properties[property_filter]) > 0     # test if property is annotated
        ]
        ac2_annotations = [
            an for an in ac2_annotations
            if property_filter in an.properties             # test if property exists
            and len(an.properties[property_filter]) > 0     # test if property is annotated
        ]

    pair_list = []
    missing_an2_annotations = 0

    for an1 in ac1_annotations:
        # collect all overlapping annotations
        overlapping_annotations = [
            an2 for an2 in ac2_annotations if test_overlap(an1, an2)]

        # test if any matching annotations in an2 was found
        if len(overlapping_annotations) < 1:
            missing_an2_annotations += 1
            pair_list.append(
                (
                    an1,
                    EmptyAnnotation(
                        start_point=an1.start_point,
                        end_point=an1.end_point,
                        property_dict={key: '#None#' for key in an1.properties}
                    )
                )
            )
        else:
            best_matching_annotation = test_max_overlap(
                silver_annotation=an1,
                second_annotator_annotations=overlapping_annotations
            )
            pair_list.append(
                # pairs first overlapping annotation
                (an1, best_matching_annotation)
            )

    string_difference = np.mean(
        [get_overlap_percentage(
            an_pair) for an_pair in pair_list if an_pair[1].tag.name != '#None#']
    ) * 100

    print(
        textwrap.dedent(
            f"""
            ==============================================
            ==============================================
            Finished search for overlapping annotations in:
            - {ac1.name}
            - {ac2.name}
            Could match {len(pair_list)} annotations.
            Average overlap is {round(string_difference, 2)} %.
            Couldn't match {missing_an2_annotations} annotation(s) in first annotation collection.
            """
        )
    )

    return pair_list


def get_iaa_data(
    annotation_pairs: List[Tuple[Annotation]],
    level='tag') -> List[Tuple[int, int, str]]:
    """Yields 3-tuples (Coder, Item, Label) for nltk.AnnotationTask data input.
    If level is not "tag" it has to be a property name, which exists in all annotations.
    ```
    an_list = [
        (Annotation(), Annotation()),
        (Annotation(), Annotation()),
        (Annotation(), Annotation()),
        (Annotation(), Annotation())
    ]
    ```
    --- to ---

    ```
    aTask_data = [
        (1, 1, 'non_event'),
        (2, 1, 'non_event'),
        (1, 2, 'non_event'),
        (2, 2, 'non_event'),
        (3, 3, 'non_event'),
        (3, 3, 'stative_event'),
    ]
    ```

    Args:
        annotation_pairs (List[Tuple[Annotation]]): List of annotation pairs.
        level (str, optionale): 'tag' or any property in the annotation collections with\
            the prefix 'prop:'.

    """
    for index, pair in enumerate(annotation_pairs):
        for an_index, an in enumerate(pair):
            if level == 'tag':
                yield an_index, index, an.tag.name
            elif an.properties and level.replace('prop:', '') in an.properties:
                yield an_index, index, an.properties[level.replace('prop:', '')][0]
            else:
                yield an_index, index, an.properties[level.replace('prop:', '')][0]


def get_iaa(
        project,
        ac1_name: str,
        ac2_name: str,
        tag_filter: list = None,
        filter_both_ac: bool = False,
        level: str = 'tag',
        distance: str = 'binary',
        return_as_dict: bool = False):
    """Computes Inter Annotator Agreement for 2 Annotation Collections.

    Args:
        project (CatmaProject): CatmaProject object.
        ac1_name (str): AnnotationCollection name to be compared.
        ac2_name (str): AnnotationCollection name to be compared with.
        tag_filter (list, optional): Which Tags should be included. If None all are included. Default to None.
        filter_both_ac (bool, optional): Whether the tag filter shall be aplied to both annotation collections. Default to False.
        level (str, optional): Whether the Annotation Tag or a specified Property should be compared.
        distance (str, optional): The IAA distance function. Either 'binary' or 'interval'.\
            See the [NLTK API](https://www.nltk.org/api/nltk.metrics.html) for further informations. Default to 'binary'.
    """

    from nltk.metrics.agreement import AnnotationTask
    from nltk.metrics import interval_distance, binary_distance

    if distance == 'inteval':
        distance_function = interval_distance
    else:
        distance_function = binary_distance

    ac1 = project.ac_dict[ac1_name]
    ac2 = project.ac_dict[ac2_name]

    annotation_pairs = get_annotation_pairs(
        ac1=ac1,
        ac2=ac2,
        tag_filter=tag_filter,
        filter_both_ac=filter_both_ac,
        property_filter=level.replace(
            'prop:', '') if 'prop:' in level else None
    )

    data = list(get_iaa_data(annotation_pairs, level=level))

    annotation_task = AnnotationTask(data=data, distance=distance_function)

    print(textwrap.dedent(
        f"""Results for "{level}"
        -------------{len(level) * '-'}-
        Scott's Pi:          {annotation_task.pi()}
        Cohen's Kappa:       {annotation_task.kappa()}
        Krippendorf's Alpha: {annotation_task.alpha()}
        ===============================================
        """
    ))

    if return_as_dict:
        return {
            "Scott's Pi": annotation_task.pi(),
            "Cohen's Kappa": annotation_task.kappa(),
            "Krippendorf's Alpha": annotation_task.alpha()
        }
    else:
        print(textwrap.dedent(
            f"""
            Confusion Matrix
            -------
            """
        ))
        return get_confusion_matrix(pair_list=annotation_pairs, level=level)


def gamma_agreement(
        project,
        annotation_collections: List[AnnotationCollection],
        alpha: int = 3,
        beta: int = 1,
        delta_empty: float = 0.01,
        n_samples: int = 30,
        precision_level: int = 0.01):
    """Computes Gamma IAA based on Mathet et. al "The Unified and Holistic Method Gamma"
    using the `pygamma-agreement` library. For further installation steps of pygamma-agreement
    and different disagreement options see the [Github site](https://github.com/bootphon/pygamma-agreement).

    Args:
        project (_type_): The CATMA project that holds the used annotation collections.
        annotation_collections (List[AnnotationCollection]): List of annotation collections to be included.
        alpha (int, optional): Coefficient weighting the positional dissimilarity value. Defaults to 3.
        beta (int, optional): Coefficient weighting the categorical dissimilarity value. Defaults to 1.
        delta_empty (float, optional): _description_. Defaults to 0.01.
        n_samples (int, optional): Number of random continuum sampled from this continuum. Defaults to 30.
        precision_level (int, optional): Optional float or "high", "medium", "low" error percentage of the gamma estimation. Defaults to 0.01.

    Raises:
        ImportWarning: If pygamma has not been installed.
    """

    try:
        from pygamma_agreement import Continuum, CombinedCategoricalDissimilarity, CategoricalDissimilarity, PrecomputedCategoricalDissimilarity
    except ImportError:
        raise ImportWarning(
            'To compute the gamma Agreement you need to install pygamma-agreement.\
             See https://github.com/bootphon/pygamma-agreement for details.')

    ac_data_frames = [
        ac.to_pygamma_table() for ac in project.annotation_collections
        if ac.name in annotation_collections
    ]

    # all annotation collection data frames to one data frame
    concat_df = pd.concat(ac_data_frames)

    # temp. save the concat_df
    concat_df.to_csv(
        'temp_gamma.csv',
        index=False,
        header=False,
        encoding='utf-8',
        sep=','
    )

    continuum = Continuum.from_csv('temp_gamma.csv')
    os.remove('temp_gamma.csv')

    # cat_dissim = CategoricalDissimilarity(
    #     categories=continuum.categories, delta_empty=1)
    dissimilarity = CombinedCategoricalDissimilarity(
        delta_empty=delta_empty,
        alpha=alpha,
        beta=beta,
        # cat_dissim=cat_dissim
    )

    gamma_results = continuum.compute_gamma(
        dissimilarity,
        n_samples=n_samples,
        precision_level=precision_level)

    print(f"The gamma agreement is {gamma_results.gamma}")

