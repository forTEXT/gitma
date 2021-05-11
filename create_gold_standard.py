"""
Function to create a annotation gold standard for 2 or more annotation collections.
"""

import catma_gitlab.catma_gitlab_classes as cgc


def find_matching_annotations(ac1, ac2):
    pass


def create_gold(
    project: cgc.CatmaProject,
    list_of_annotation_collections: list,
    silver_collection: cgc.AnnotationCollection,
    gold_collection: cgc.AnnotationCollection,
    documentation_collection: cgc.AnnotationCollection,
    tagset: cgc.Tagset,
    documentation_tagset: cgc.Tagset
    ):

    test_collections = [ac for ac in list_of_annotation_collections if ac != silver_collection]
    for an in silver_collection.annotations:
        pass
