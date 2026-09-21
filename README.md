# GitMA

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6330464.svg)](https://doi.org/10.5281/zenodo.6330464)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/forTEXT/gitma/HEAD?labpath=demo%2Fnotebooks%2Fexplore_annotations.ipynb)

## Description

Python package to access and process CATMA projects via the CATMA GitLab backend.

This package makes use of [CATMA's Git Access](https://catma.de/documentation/git-access/).
For further information see the [GitMA Documentation](https://gitma.readthedocs.io/en/latest/index.html).

## Demo Jupyter Notebooks and Docker Image

You'll find 4 Jupyter Notebooks in the demo/notebooks directory:

- [Cloning and loading your CATMA project with the package](https://github.com/forTEXT/gitma/blob/main/demo/notebooks/load_project_from_gitlab.ipynb)
- [Exploring your annotations](https://github.com/forTEXT/gitma/blob/main/demo/notebooks/explore_annotations.ipynb)
- [Gold annotation support](https://github.com/forTEXT/gitma/blob/main/demo/notebooks/gold_annotation_support.ipynb)
- [Inter annotator agreement](https://github.com/forTEXT/gitma/blob/main/demo/notebooks/inter_annotator_agreement.ipynb)

We have also created a ready to use [Docker image](https://github.com/forTEXT/gitma/blob/main/docker/README.md) that includes GitMA and all dependencies, as
well as the above notebooks. This is a good way to see what GitMA can do.

## Installation

Install using `pip install git+https://github.com/forTEXT/gitma`

To install locally for development use: `pip install -e .`

## Additional Notes

Git related functionality is implemented using [pygit2](https://www.pygit2.org/). Make sure to have the access token for CATMA Gitlab instance. See the demo notebooks for instructions on how to set up the access token.