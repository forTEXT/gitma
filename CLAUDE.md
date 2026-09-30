# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

GitMA is a Python library (no CLI) for reading, analysing and writing back CATMA
annotation projects. A CATMA project *is* a Git repository hosted on CATMA's
GitLab backend (`https://git.catma.de/`); GitMA clones it and maps the on-disk
JSON files onto Python objects. `main.py` is an example script, not an entry point.

Requires Python 3.13 (`requires-python = ">=3.13, <3.14"` — the upper bound is
deliberate, see RELEASING.md).

## Commands

Dependencies are managed with `uv`; prefix everything with `uv run` (no need to
activate `.venv`).

```bash
uv sync --group dev                 # dev setup (adds pytest)
uv sync --group notebooks           # JupyterLab, for demo/notebooks only
uv sync --extra docs                # docs deps; --extra pygamma for gamma agreement
uv lock                             # after ANY dependency change; verify with `uv sync --locked`

uv run pytest                       # runs from anywhere; paths are anchored on __file__
uv run pytest tests/test__write_annotation.py::TestWriteAnnotation::test_write_annotation_json

uv run sphinx-build -b html docs/source docs/build/html
uv build                            # sdist, then wheel built from that sdist
```

### Things that bite when touching tests or dependencies

The reasons behind these are in `CONTRIBUTING.md` (tests, dependencies),
`RELEASING.md` (Python version) and the comments in `pyproject.toml`.

- **Never index into `project.annotation_collections` in a test** — use
  `project.ac_dict['ac_1']`; list order is filesystem-dependent.
- **Never lower the `nltk` floor below 3.10.2.**
- **`[project.dependencies]` must contain only what the package imports**
  (`scipy` is the one commented exception).
- **New test fixtures need an entry in `[tool.hatch.build.targets.sdist]`.**
- **Tests write into `demo/projects/`** — a new write test must clean up via
  `addCleanup`, so `git status demo/` stays clean.
- **The Python version is declared in six places** — change them together, per
  "New Python releases" in `RELEASING.md`.

## Architecture

### On-disk CATMA project layout

Everything in the object model is a direct read of this structure:

```
CATMA_<uuid>_<project name>/         # the GitLab project name; `CatmaProject.uuid`
  documents/D_<uuid>/                # header.json + <uuid>.txt (the plain text)
  tagsets/T_<uuid>/                  # header.json + <tag uuid>/propertydefs.json per tag
  collections/C_<uuid>/              # header.json + annotations/<author>_<page no>.json
```

Annotation page files are JSON-LD arrays; a new page is started when appending
would push the current one past `MAX_ANNOTATION_PAGE_FILE_SIZE_BYTES` (`_write_annotation.py`).
Character offsets in annotations index into `Text.plain_text`.

### Object model (all eagerly loaded in `CatmaProject.__init__`)

`Catma` (all projects of one GitLab account) → `CatmaProject` → `Tagset` → `Tag`
→ `Property`, and `CatmaProject` → `AnnotationCollection` → `Annotation` →
`Selector`. Each level is exposed both as a list and as a lookup dict
(`tagset_dict` by UUID, `ac_dict` by name, `text_dict` by title, `tag_dict` by
UUID). `Annotation` resolves its tag via `project.tagset_dict[...].tag_dict[...]`,
so an annotation cannot be constructed without its parent project.

`AnnotationCollection` keeps a second, flattened representation: `self.df`, a
pandas DataFrame with the columns in `annotation_collection.df_columns` plus one
`prop:<name>` column per property. Analysis and plotting code works on the
DataFrame; mutation works on the objects.

### Public class / private module split

The user-facing classes are thin. Heavy functionality lives in underscore-prefixed
modules and is imported into methods of `CatmaProject` / `AnnotationCollection`:

- `_metrics.py` — annotation pairing, confusion & co-occurrence matrices, IAA data
  prep, gamma agreement. Backs `get_iaa`, `calculate_scotts_pi`,
  `calculate_cohens_kappa`, `calculate_krippendorffs_alpha` (nltk `AnnotationTask`).
- `_network.py` — `Network` class, co-occurrence / disagreement graphs (networkx).
- `_vizualize.py` — all Plotly figures.
- `_write_annotation.py` — serialises a new annotation into a page file.
- `_gold_annotation.py` — matches annotations across two collections into a third.
- `_export_annotations.py` — Stanford TSV export (spaCy tokenisation).

Add new analysis code to the relevant `_module.py` and expose it as a method,
rather than growing the class files.

### `os.chdir` is load-bearing

`CatmaProject.__init__` does `os.chdir(projects_directory)` and every path below
it (`Tagset`, `Text`, `AnnotationCollection`, `load_annotations`) is relative to
that directory. Only `__init__` restores the previous cwd in a `finally`;
`write_annotation_json` (and so `Annotation._copy`) and the methods that shell out
to `git` restore it only on success (a known wart), so an exception there leaves
the process in the project directory. Keep
this in mind when adding paths — a bare relative path means "relative to
`projects_directory`" in loading code but "relative to the project clone" inside
`write_annotation_json`, which also builds paths by string concatenation and so
needs `projects_directory` to end in a separator.

### Git access is split between pygit2 and subprocess

Cloning uses `pygit2` (`load_gitlab_project`), but pull/commit/push still shell out
to `git` (`CatmaProject.update`, `AnnotationCollection.push_annotations`,
`create_gold_annotations`, `write_annotation_csv`) and therefore require a `git`
install with saved CATMA credentials. Pushes target `master`, not `main`.
Migrating the remaining calls to pygit2 is a known goal (README, "Additional Notes").

## Conventions

- **Consistency is valued highly.** When there is an established way of doing
  something here, follow it rather than introducing a second one. If you find the
  codebase already doing the same thing two different ways, don't quietly pick a
  side and don't add a third: say so, and propose how to make it uniform, with the
  trade-offs of each option. Where the inconsistency is deliberate, record why,
  next to the exception (as the `scipy` entry in `pyproject.toml` does).
- User-facing messages from the library are plain `print()` throughout, including
  warnings — there is no `logging` or `warnings` usage. Don't introduce either in
  one place; if it's needed, propose switching over as a whole.
- Indentation is 4 spaces (`.editorconfig`). No formatter or linter is configured,
  and existing code mixes line lengths and quote styles, so match the surrounding
  file and don't reformat code you aren't otherwise changing.
- Docstrings are Google style and may contain Markdown (`commonmark` converts them
  in `docs/source/conf.py`); attribute docs use `#:` comments so Sphinx picks them up.
- The version lives **only** in `pyproject.toml`. `gitma.__version__` and the Sphinx
  `release` both read it back from installed distribution metadata — never hard-code it.
- Feature PRs add a bullet under `## [Unreleased]` in `CHANGELOG.md` and do *not*
  bump the version; releases are cut per RELEASING.md (tag = bare version number,
  which must be kept in sync with `pyproject.toml` by hand — the release process
  is entirely manual, there is no CI).
- `docs/build/` is generated and gitignored. Demo notebooks in `demo/notebooks/`
  are user-facing documentation — keep them runnable against `demo/projects/`.

### Working with the user

Unless you have been sent off to work unattended, agree the design before you
build it:

- Put design decisions to the user before implementing — which approach, what the
  trade-offs are, anything you had to assume. Answer any questions they've asked
  and confirm the details they've asked you to confirm, then wait for a go-ahead
  rather than starting.
- Don't commit on your own initiative while questions are open, or while it's
  likely you'll be asked to change what you've just done. In an active session,
  finish the work, report it, and let the user ask for the commit.

### Where documentation belongs

Put an explanation next to the thing it explains, at the narrowest scope that
fits, and write it only once:

- **What a public function or class does** → its docstring, which is also what
  Sphinx publishes as the API reference.
- **Why code or a workaround exists** → a `#` comment beside it. This is the
  default for anything surprising: a version pin, a `chdir` that must not be
  removed, a guard that looks redundant. Someone editing the file must be able to
  see the reason without consulting git.
- **How a subsystem fits together** → this file, at a level that stays true as the
  code changes. Don't restate what a docstring or comment already says.
- **Anything a library user or contributor has to know or do** → `README.md`,
  `docs/source/`, `CONTRIBUTING.md` or `RELEASING.md`; a user-visible change also
  gets its `CHANGELOG.md` bullet.
- **Why a change was made** → the commit message.
- **Work you've identified but aren't doing** → `TODO.md`, unless a plan already
  covers it. Don't leave it in user-facing documentation or as a speculative
  comment in the code. That file collects AI-identified follow-up work only,
  grouped by the branch or task the note came out of — add the entry under the
  section for the branch you're on, creating the file or section if needed.

### Commit messages

Subject in the imperative, then a blank line, then prose explaining **why**. Keep
it short — a sentence or two is usually plenty, and a reader who wants more has
the diff, the code comments and this file. Err on the side of leaving things out.

- Explain the motivation and any non-obvious consequence. Don't list what changed
  file by file — the diff already says that.
- **Don't explain how the new code works.** That belongs in the code, or a comment
  beside it, where someone changing it will see it. A commit message describing
  the mechanism is both a duplicate and the copy that goes stale.
- **Say no more about the old behaviour than it takes to see why the change was
  made.** Naming the machinery that went away is noise.
- **Nothing here is written for a library user.** Anything someone has to *do* —
  an install step, a changed call, a migration — goes in the README, the docs or
  the CHANGELOG, because that is where they will look. A breaking change to the
  public API is worth a line, as it tells a reader how far the commit reaches.
- State conclusions directly. Don't narrate the investigation that produced them
  ("diffing X against Y shows…", "after checking…") and don't cite evidence for
  your own claims.
- If a detail is needed to work on the code rather than to understand the change,
  it belongs in a comment, not here.
