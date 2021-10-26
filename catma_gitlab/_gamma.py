import os
import pandas as pd
from pygamma_agreement import Continuum, CombinedCategoricalDissimilarity


def gamma_agreement(
        project,
        annotation_collections: list,
        alpha: int = 3,
        beta: int = 1,
        delta_empty: float = 0.01,
        n_samples: int = 30,
        precision_level: int = 0.01):
    ac_data_frames = [
        ac.to_pygamma_table() for ac in project.annotation_collections
        if ac.name in annotation_collections
    ]

    concat_df = pd.concat(ac_data_frames)

    concat_df.to_csv(
        'temp_gamma.csv',
        index=False,
        header=False,
        encoding='utf-8',
        sep=','
    )

    continuum = Continuum.from_csv('temp_gamma.csv')
    os.remove('temp_gamma.csv')

    dissimilarity = CombinedCategoricalDissimilarity(
        delta_empty=delta_empty,
        alpha=alpha,
        beta=beta,)

    gamma_results = continuum.compute_gamma(
        dissimilarity,
        n_samples=n_samples,
        precision_level=precision_level)

    print(f"The gamma agreement is {gamma_results.gamma}")
