# Changelog

All notable changes to GitMA are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.1.0] - 2026-09-29

### Added

- Krippendorff's alpha as an inter-annotator agreement measure, including a
  `property_filter` parameter and an example in the IAA demo notebook.
- Generation of a co-occurrence matrix for annotations.
- Separate Scott's pi and Cohen's kappa IAA methods.
- `verbose` parameter to suppress detailed IAA output.

### Changed

- **Breaking:** the default for the `filter_both_ac` parameter in the IAA score
  calculations is now `True`. Results of previous runs are not directly
  comparable; see the inter-annotator agreement demo notebook for details.
- **Breaking:** the minimum supported Python version is now 3.13 (previously 3.9),
  and dependencies were updated accordingly.
- IAA score names now match the spelling used in the literature (capitalised
  author name, lower-case Greek letter).
- IAA result handling was unified in a single `_return_iaa_result` function, and
  `get_cooccurrence_matrix` / `get_annotation_pairs_for_multiple_annotators` moved
  to `gitma/_metrics.py`.
- Packaging now uses `pyproject.toml` with the Hatchling build backend and a
  `uv.lock` lockfile. `setup.py` has been removed; project metadata lives in
  exactly one place.
- The package version is declared only in `pyproject.toml` and exposed at runtime
  as `gitma.__version__`. Sphinx reads it from the installed metadata rather than
  from a hard-coded value.
- Documentation dependencies are declared as the `docs` extra in
  `pyproject.toml`. The unmaintained `docs/requirements.txt` was removed, and
  Read the Docs now builds with Python 3.13 instead of 3.9.
- The Docker demo image was bumped to 0.0.13. It now takes the GitMA git ref as a
  `GITMA_VERSION` build argument, so a published image can be tied to a release
  tag instead of to whatever `main` was at build time.
- The Docker demo image no longer uses conda. It is built from `python:3.13-slim`
  and installs everything, including the `pygamma` solver stack, from PyPI wheels.
  conda was needed when CBC had no usable Python wheel; `cylp` now ships manylinux
  wheels with CBC vendored in, for both amd64 and arm64. The compiler toolchain
  (`build-essential`, `cmake`) is gone with it, as are `matplotlib` and `tabulate`,
  which nothing imported. The menu's "update" option now upgrades via pip only.
- **Breaking:** installing GitMA no longer installs the Jupyter stack. The demo
  notebooks now get JupyterLab from the `notebooks` dependency group
  (`uv sync --group notebooks`); the Docker image and Binder provide their own.
- Runtime dependencies now carry lower bounds instead of being unconstrained.
  Users install from Git and so get a fresh resolution, which previously could
  pick up arbitrarily old releases of pandas, numpy and friends.
- `nltk` is constrained to >= 3.10.2. Versions 3.10.0 and 3.10.1 shipped an import
  hook that refused any import originating inside the working directory, which
  made `import gitma` fail from a project directory containing a virtual
  environment - the standard `uv` layout. Upstream removed the hook in 3.10.2.

### Fixed

- Krippendorff's alpha output is now labelled correctly.
- A bug in `merge_annotations_per_document`.

### Removed

- The generated `docs/build/` output is no longer committed to the repository.
- `Cython`, `jupyter` and `tabulate` are no longer runtime dependencies: nothing
  in the package imports them. `cvxopt` moved to the `pygamma` extra, where it is
  a transitive dependency of `pygamma-agreement`. `ipython` is now declared
  explicitly, since `gitma/_network.py` imports it and it was previously only
  present by accident, via `jupyter`.

### Infrastructure

- [RELEASING.md](https://github.com/forTEXT/gitma/blob/main/RELEASING.md)
  documents the release process: the checks to run, the version bump, the tag,
  and how to publish a GitHub Release with the built distributions attached. The
  process is entirely manual.
- The sdist ships the test suite together with the demo project it reads from, so
  the distribution can be verified on its own.
- The test suite no longer depends on the working directory it is started from,
  and picks annotation collections by name rather than by `os.listdir` position.
- The tests clean up the page files they write via `addCleanup`, so cleanup also
  runs when an assertion fails. Previously a failing test left its page file
  behind in `demo/projects/`, and the next run appended to that file instead of
  creating it - so the suite stayed red until the file was deleted by hand.
- `binder/requirements.txt` and `binder/runtime.txt` restore the Binder demo:
  repo2docker does not recognise projects that only have a `pyproject.toml`, so
  removing `setup.py` had left it unable to install GitMA. `runtime.txt` pins the
  interpreter, which repo2docker takes neither from `pyproject.toml` nor from
  `.python-version`.
- `.python-version` pins the interpreter that `uv` provisions.

## [2.0.5] - 2025-06-05

## [2.0.4] - 2025-02-07

## [2.0.3] - 2024-07-05

## [2.0.2] - 2024-07-04

## [2.0.1] - 2023-11-14

## [2.0.0] - 2023-10-19

## [1.4.9] - 2022-03-05

## [1.0.0] - 2021-11-10

Changes for releases up to and including 2.0.5 predate this changelog. Use the
comparison links below to review the commits that went into each of them.

[Unreleased]: https://github.com/forTEXT/gitma/compare/2.1.0...HEAD
[2.1.0]: https://github.com/forTEXT/gitma/compare/2.0.5...2.1.0
[2.0.5]: https://github.com/forTEXT/gitma/compare/2.0.4...2.0.5
[2.0.4]: https://github.com/forTEXT/gitma/compare/2.0.3...2.0.4
[2.0.3]: https://github.com/forTEXT/gitma/compare/2.0.2...2.0.3
[2.0.2]: https://github.com/forTEXT/gitma/compare/2.0.1...2.0.2
[2.0.1]: https://github.com/forTEXT/gitma/compare/2.0.0...2.0.1
[2.0.0]: https://github.com/forTEXT/gitma/compare/1.4.9...2.0.0
[1.4.9]: https://github.com/forTEXT/gitma/compare/1.0.0...1.4.9
[1.0.0]: https://github.com/forTEXT/gitma/releases/tag/1.0.0
