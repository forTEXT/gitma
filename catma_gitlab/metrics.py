import numpy as np
import pandas as pd
from catma_gitlab.annotation import Annotation
from catma_gitlab.annotation_collection import AnnotationCollection


def filter_ac_by_tag(ac1: AnnotationCollection, ac2: AnnotationCollection, tag_filter=None, filter_both_ac=True):
    """
    Returns list of filtered annotations.
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


def get_same_text(annotation_list1, annotation_list2):
    """
    All text parts only annotate by one coder get excluded.
    """
    an1 = [an for an in annotation_list1 if an.start_point <=
           annotation_list2[-1].start_point]
    an2 = [an for an in annotation_list2 if an.start_point <=
           annotation_list1[-1].end_point]
    return an1, an2


def test_max_overlap(silver_annotation: Annotation, second_annotator_annotations: list) -> Annotation:
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


def test_overlap(an1: Annotation, an2: Annotation):
    """
    Test if annotation 2 starts or ends within annotations 1 span.
    """
    # test if an2 starts before or in an2
    start_match = an1.start_point <= an2.start_point < an1.end_point

    # test if an2 ends in or with an1
    end_match = an1.start_point < an2.end_point <= an1.end_point

    # test if an2 starts before and ends after an1 -> includes an1
    included_match = an2.start_point < an1.start_point and an2.end_point > an1.end_point

    if start_match or end_match or included_match:
        return True


def get_overlap_percentage(an_pair) -> float:
    """
    Computes the overlap percentage of two annotations.
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


def get_confusion_matrix(pair_list) -> pd.DataFrame:
    tags = set([p[0].tag.name for p in pair_list] +
               [p[1].tag.name for p in pair_list])
    tag_dict = {tag: {t: 0 for t in tags} for tag in tags}
    for pair in pair_list:
        an1, an2 = pair[0], pair[1]
        tag_dict[an1.tag.name][an2.tag.name] += 1

    return pd.DataFrame(tag_dict)


class EmptyTag:
    def __init__(self):
        self.name = '#None#'


class EmptyAnnotation:
    def __init__(self, start_point, end_point):
        self.start_point = start_point
        self.end_point = end_point
        self.tag = EmptyTag()


def get_annotation_pairs(
        ac1: AnnotationCollection,
        ac2: AnnotationCollection,
        tag_filter=None,
        filter_both_ac=False):
    """
    Returns list of all overlapping annotations in two annotation collections.
    tag_filter can be defined as list of tag names if not all annotations are included.
    To avoid pairing of embedded annotations in case of discontinuous annotations
    only the first overlapping annotation by second annotator gets paired.
    """
    ac1_annotations, ac2_annotations = filter_ac_by_tag(ac1=ac1, ac2=ac2, tag_filter=tag_filter,
                                                        filter_both_ac=filter_both_ac)
    ac1_annotations, ac2_annotations = get_same_text(
        ac1_annotations, ac2_annotations)

    pair_list = []
    missing_an2_annotations = 0
    for an1 in ac1_annotations:

        # collect all overlapping annotations
        overlapping_annotations = [
            an2 for an2 in ac2_annotations if test_overlap(an1, an2)]

        # test if any matching annotations in an2 was found
        if len(overlapping_annotations) < 1:
            missing_an2_annotations += 1
            pair_list.append((an1, EmptyAnnotation(
                start_point=an1.start_point, end_point=an1.end_point)))
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

    print(f"""
Finished search for overlapping annotations.
Could match {len(pair_list)} items.
Average overlap is {round(string_difference, 2)} %.
Couldn't match {missing_an2_annotations} annotation(s) in first annotation collection.

Confusion Matrix:
{get_confusion_matrix(pair_list).to_markdown()}
        """)

    return pair_list


def get_iaa_data(annotation_pairs: list, level='tag'):
    """
    Yields 3-tuples (Coder, Item, Label) for nltk.AnnotationTask data input.
    If level is not "tag" it has to be a property name, which exists in all annotations.
    """
    for index, pair in enumerate(annotation_pairs):
        for an_index, an in enumerate(pair):
            if level == 'tag':
                yield an_index, index, an.tag.name
            else:
                yield an_index, index, an.properties[level]


def get_iaa(ac1: AnnotationCollection, ac2: AnnotationCollection,
            tag_filter=None, filter_both_ac=False,
            level='tag', distance='binary'):
    from nltk.metrics.agreement import AnnotationTask as AnTa
    from nltk.metrics import interval_distance, binary_distance

    if distance == 'inteval':
        distance_function = interval_distance
    else:
        distance_function = binary_distance

    annotation_pairs = get_annotation_pairs(
        ac1, ac2, tag_filter=tag_filter, filter_both_ac=filter_both_ac)
    data = list(get_iaa_data(annotation_pairs, level=level))
    annotation_task = AnTa(data=data, distance=distance_function)
    print(f"""
        Cohen's Kappa: {annotation_task.kappa()}
        Krippendorf Alpha: {annotation_task.alpha()}
        """)

    return get_confusion_matrix(pair_list=annotation_pairs)
