# Contributing to GitMA

Thanks for your interest in improving GitMA. Bug reports, feature requests and
pull requests are all welcome via the
[issue tracker](https://github.com/forTEXT/gitma/issues).

## Development setup

GitMA uses [uv](https://docs.astral.sh/uv/) for dependency management. Install it
following the [official instructions](https://docs.astral.sh/uv/getting-started/installation/),
then:

```bash
git clone https://github.com/forTEXT/gitma.git
cd gitma
uv sync --group dev
```

`uv sync` creates a virtual environment in `.venv` using the interpreter pinned in
`.python-version`, installs the pinned dependencies from `uv.lock` and installs
GitMA itself in editable mode. There is no need to activate the environment -
prefix commands with `uv run`:

```bash
uv run pytest              # run the test suite
uv run python main.py      # run the example script
```

To work with the demo notebooks, sync the `notebooks` group first - JupyterLab is
deliberately not a dependency of the library itself:

```bash
uv sync --group notebooks
uv run jupyter lab
```

To include the optional [pygamma-agreement](https://pypi.org/project/pygamma-agreement/)
support, add `--extra pygamma`.

## Tests

Tests live in `tests/` and are written with `unittest`, but are run with pytest:

```bash
uv run pytest
```

They can be run from anywhere - paths are resolved relative to the test files, not
to the working directory. The tests read from, and write into, the demo project in
`demo/projects/`; each one cleans up the page files it creates, so
`git status demo/` should stay clean. Select annotation collections by name
(`project.ac_dict['ac_1']`) rather than by index, since index order depends on the
filesystem.

Please add or update tests alongside behaviour changes. There is no CI, so run
the suite yourself before opening a pull request, and say in the description
which platform you ran it on.

The sdist ships the tests together with the demo project they read from, so the
distribution can be verified on its own. If you add a file the tests need, add it
to `[tool.hatch.build.targets.sdist]` in `pyproject.toml` too, then check that the
suite still passes from an unpacked sdist:

```bash
uv build
tar -xf dist/gitma-*.tar.gz -C /tmp
cd /tmp/gitma-*/ && uv run --with pytest pytest
```

## Documentation

The documentation is built with Sphinx from `docs/source` and published on
[Read the Docs](https://gitma.readthedocs.io/). Docstrings use Google style and
may contain Markdown.

```bash
uv sync --extra docs
uv run sphinx-build -b html docs/source docs/build/html
```

Open `docs/build/html/index.html` in a browser to preview. The `docs/build/`
directory is generated output and is not committed.

## Dependencies

Runtime dependencies are declared in `[project.dependencies]` in
`pyproject.toml`; optional feature sets go in `[project.optional-dependencies]`
and development-only tooling in `[dependency-groups]`. After changing any of
them, regenerate and commit the lockfile:

```bash
uv lock
```

Verify the result with `uv sync --locked`, which fails if `uv.lock` is out of date
with `pyproject.toml`. Nothing checks this automatically, so a stale lockfile will
only surface for the next person who syncs.

Two rules keep the dependency list honest:

- **Only declare what the package imports.** `[project.dependencies]` is what
  every user installs, and they install from Git without the lockfile, so anything
  listed there that GitMA does not `import` is dead weight for everyone. Tooling
  that only the notebooks, the docs or the tests need belongs in an extra or a
  dependency group. The one deliberate exception is `scipy`, which `networkx`
  needs for the default `kamada_kawai_layout` but only declares as an extra; it is
  commented as such.
- **Give every runtime dependency a lower bound.** The lockfile pins exact
  versions for local development, but users get a fresh resolution, so the bounds
  in `pyproject.toml` are the only thing standing between them and an unusably old
  release.

## Pull requests

- Branch off `main` and keep pull requests focused on one change.
- Add a bullet to the `## [Unreleased]` section of [CHANGELOG.md](CHANGELOG.md)
  describing the change from a user's point of view.
- Do not bump the version in a feature pull request; that happens as part of the
  release, see [RELEASING.md](RELEASING.md).
