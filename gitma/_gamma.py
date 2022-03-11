import os
import pandas as pd
from typing import List
from gitma.annotation_collection import AnnotationCollection


"""Computes Gamma IAA based on Mathet et. al "The Unified and Holistic Method Gamma"
using https://github.com/bootphon/pygamma-agreement. For further installation steps of pygamma-agreement
and different disagreement computing see the Github site.

Args:
    project (CatmaProject): The CATMA project that holds the used annotation collections.
    annotation_collections (list): [description]
    alpha (int, optional): [description]. Defaults to 3.
    beta (int, optional): [description]. Defaults to 1.
    delta_empty (float, optional): [description]. Defaults to 0.01.
    n_samples (int, optional): [description]. Defaults to 30.
    precision_level (int, optional): [description]. Defaults to 0.01.
"""


def gamma_agreement(
        project,
        annotation_collections: List[AnnotationCollection],
        alpha: int = 3,
        beta: int = 1,
        delta_empty: float = 0.01,
        n_samples: int = 30,
        precision_level: int = 0.01):
    """Computes Gamma IAA based on Mathet et. al "The Unified and Holistic Method Gamma"
    using https://github.com/bootphon/pygamma-agreement. For further installation steps of pygamma-agreement
    and different disagreement computing see the Github site.

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
