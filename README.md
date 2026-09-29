# GitMA

[![Documentation](https://readthedocs.org/projects/gitma/badge/?version=latest)](https://gitma.readthedocs.io/en/latest/)
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

To run the notebooks from a clone of this repository instead, sync the
`notebooks` dependency group, which provides JupyterLab:

```
uv sync --group notebooks
uv run jupyter lab
```

JupyterLab is deliberately not a dependency of the library itself, so installing
GitMA does not pull in the whole Jupyter stack; the Docker image and Binder each
bring their own.

## Installation

GitMA requires Python 3.13 (3.14 is not supported yet) and is installed directly
from this repository:

```
pip install git+https://github.com/forTEXT/gitma
```

If you manage your project with [uv](https://docs.astral.sh/uv/), add it with:

```
uv add git+https://github.com/forTEXT/gitma
```

To pin a specific [release](https://github.com/forTEXT/gitma/releases), append the
tag:

```
pip install git+https://github.com/forTEXT/gitma@2.2.0
```

Gamma agreement support is an optional extra:

```
pip install "gitma[pygamma] @ git+https://github.com/forTEXT/gitma"
```

Releases from 2.2.0 onwards also have a prebuilt wheel and source distribution
attached, which you can install instead of building from the repository.

Cloning and reading a project works with GitMA alone. Updating a project or
pushing annotations back to CATMA also requires a `git` installation with saved
credentials for your CATMA account - see [Additional Notes](#additional-notes).

For a local development setup see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contributing and Releases

- [CONTRIBUTING.md](CONTRIBUTING.md) — development setup, tests, documentation
- [CHANGELOG.md](CHANGELOG.md) — what changed in each version
- [RELEASING.md](RELEASING.md) — how maintainers cut a release

## Additional Notes

Some functions in this package still rely on calling Git via subprocess. We are working on changing these to use pygit2 instead, so that a separate Git
installation (with valid saved credentials for your CATMA account) will no longer be required in future.
