Installation
============

GitMA requires Python 3.13.

Installation via ``pip``
------------------------

GitMA is installed directly from its GitHub repository:

.. code-block:: console

   pip install git+https://github.com/forTEXT/gitma

To pin a specific release, append the tag:

.. code-block:: console

   pip install git+https://github.com/forTEXT/gitma@2.2.0

Optional extras
---------------

Gamma agreement support (`pygamma-agreement <https://pypi.org/project/pygamma-agreement/>`_)
is an optional extra:

.. code-block:: console

   pip install "gitma[pygamma] @ git+https://github.com/forTEXT/gitma"

Prebuilt distributions
----------------------

Each `release <https://github.com/forTEXT/gitma/releases>`_ has a wheel and a
source distribution attached, which can be installed directly if you prefer not to
build from the repository.

Installation via Docker
-----------------------

Additionally, you can `install GitMA with Docker <https://catma.de/documentation/git-access/gitma-docker-image/>`_ and use the demo Jupyter Notebooks within a Docker Container.

Development installation
------------------------

GitMA uses `uv <https://docs.astral.sh/uv/>`_ for development:

.. code-block:: console

   git clone https://github.com/forTEXT/gitma.git
   cd gitma
   uv sync --group dev

See `CONTRIBUTING.md <https://github.com/forTEXT/gitma/blob/main/CONTRIBUTING.md>`_
for details.
