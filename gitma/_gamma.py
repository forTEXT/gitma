import os
import pandas as pd


def gamma_agreement(
        project,
        annotation_collections: list,
        alpha: int = 3,
        beta: int = 1,
        delta_empty: float = 0.01,
        n_samples: int = 30,
        precision_level: int = 0.01):
    """Computes Gamma IAA based on Mathed et. al "The Unified and Holistic Method Gamma"
    using https://github.com/bootphon/pygamma-agreement. For installation of pygamma-agreement
    see the Github site.
    Args:
        project ([type]): [description]
        annotation_collections (list): [description]
        alpha (int, optional): [description]. Defaults to 3.
        beta (int, optional): [description]. Defaults to 1.
        delta_empty (float, optional): [description]. Defaults to 0.01.
        n_samples (int, optional): [description]. Defaults to 30.
        precision_level (int, optional): [description]. Defaults to 0.01.
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
