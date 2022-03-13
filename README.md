# GitMA

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.6330464.svg)](https://doi.org/10.5281/zenodo.6330464)

## Description

Python Package to access and process CATMA Projects via the CATMA GitLab Backend.

This package makes use of [CATMA's Git Access](https://catma.de/documentation/git-access/).
For further infortmations see the [GitMA Documentation](https://gitma.readthedocs.io/en/latest/index.html).

## Installation

Install using `pip install git+https://github.com/forTEXT/gitma`

To install locally for development use: `pip install -e .`

## Demo

You'll find 4 Jupyter Notebooks in the demo_notebooks directory:

- [Cloning and loading your CATMA Project with the package](https://github.com/forTEXT/gitma/blob/main/demo_notebooks/load_project_from_gitlab.ipynb)
- [Exploring your annotations](https://github.com/forTEXT/gitma/blob/main/demo_notebooks/explore_annotations.ipynb)
- [Gold Annotation Support](https://github.com/forTEXT/gitma/blob/main/demo_notebooks/gold_annotation_support.ipynb)
- [Inter Annotator Agreement](https://github.com/forTEXT/gitma/blob/main/demo_notebooks/inter_annotator_agreement.ipynb)

## Additional Notes

Some functions in this package still rely on calling Git via subprocess. We are working on changing these to use pygit2
instead, so that a separate Git installation (with valid saved credentials for your CATMA account) will no longer be
required in future.