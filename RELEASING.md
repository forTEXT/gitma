# Releasing GitMA

GitMA is distributed from GitHub rather than PyPI: users install it with
`pip install git+https://github.com/forTEXT/gitma`. A release therefore consists
of a version bump, a git tag, and a GitHub Release with the built distributions
attached.

Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

There is no release automation - every step below is performed by hand, so work
through the checklist in order.

## Checklist

1. **Run the checks locally**, from a clean checkout of up-to-date `main`:

   ```bash
   uv sync --locked --group dev     # fails if uv.lock is stale
   uv run pytest
   uv build                         # sdist, then wheel built from that sdist
   uv sync --extra docs
   uv run sphinx-build -b html docs/source docs/build/html
   ```

   Also check the built wheel installs and imports on its own:

   ```bash
   uv venv --python 3.13 /tmp/gitma-smoke
   VIRTUAL_ENV=/tmp/gitma-smoke uv pip install dist/*.whl
   /tmp/gitma-smoke/bin/python -c "import gitma; print(gitma.__version__)"
   ```

   The version it prints must match the one you are about to release.

2. **Bump the version.** Edit `version` in `pyproject.toml`. This is the only
   place the version is written down - `gitma.__version__` and the Sphinx docs
   both read it from there. Nothing verifies that the tag and this value agree,
   so take care that they do.

3. **Update `CHANGELOG.md`.** Rename the `## [Unreleased]` heading to
   `## [<version>] - <YYYY-MM-DD>`, then add a fresh empty `## [Unreleased]`
   above it. At the bottom of the file, repoint `[Unreleased]` at the new version
   and add a `[<version>]` link for the range it covers. There must be exactly one
   `## [<version>]` heading when you are done - step 7 extracts the first match,
   so a leftover duplicate would publish empty release notes.

4. **Refresh the lockfile if dependencies changed.**

   ```bash
   uv lock
   ```

5. **Open a pull request with the bump** and merge it once reviewed.

6. **Tag the merge commit on `main` and push the tag.** Use the bare version
   number, matching the existing tags (`1.0.0` ... `2.2.0`):

   ```bash
   git checkout main && git pull
   git tag -a 2.3.0 -m "GitMA 2.3.0"
   git push origin 2.3.0
   ```

7. **Build the distributions from the tag and publish the GitHub Release.**
   Build from a clean tree so that no local edits leak into the artifacts:

   ```bash
   git checkout 2.3.0
   rm -rf dist/
   uv build
   ```

   Then create the release, either in the GitHub web UI (Releases → Draft a new
   release → pick the tag, paste the changelog section, attach both files from
   `dist/`), or with the `gh` CLI:

   ```bash
   gh release create 2.3.0 dist/* \
       --title "2.3.0" \
       --notes-file <(awk '/^## \[2\.2\.0\]/{c=1;next} c&&/^## \[/{exit} c' CHANGELOG.md)
   ```

8. **Check the results:**
   - the [GitHub Release](https://github.com/forTEXT/gitma/releases) has the right
     notes and both distribution files,
   - [Zenodo](https://doi.org/10.5281/zenodo.6330464) has archived the release and
     minted a DOI,
   - [Read the Docs](https://gitma.readthedocs.io/) has built the new version.
     Note that RTD reads `.readthedocs.yaml` from the commit it builds, so a
     config fix only takes effect for builds of commits that contain it.

9. **Rebuild and publish the Docker demo image** if the release should be
   reflected there. The image carries its own version, independent of the GitMA
   version; the canonical build command is the comment at the top of
   [docker/Dockerfile](docker/Dockerfile), and
   [docker/README.md](docker/README.md) covers only how end users pull and run it.

   - Bump the image version in three places, keeping them in sync: the `LABEL` in
     [docker/Dockerfile](docker/Dockerfile), the logo footer in
     [docker/gitma.sh](docker/gitma.sh), and the sample build command at the top
     of the Dockerfile. Never re-push an already-published image tag - the example
     below uses 0.0.14 because 0.0.13 is the version currently in the tree.
   - The logo footer also carries a date next to the version. Set it to the date
     you make the bump, in the same edit - it is the only part of the container's
     greeting a user can date the image by, and nothing checks it.
   - Build with `--build-arg GITMA_VERSION=<the tag pushed in step 6>`. This is
     what makes the image reproducible: omit it and the build falls back to the
     `main` default, so the published image contains whatever `main` happened to
     be at build time rather than the release.

     ```bash
     docker buildx build --platform linux/amd64,linux/arm64 \
         --build-arg GITMA_VERSION=2.3.0 \
         --tag maltem/gitma-demo:0.0.14 --tag maltem/gitma-demo:latest --push .
     ```

   - Open a pull request with the version bumps and merge it. They are not part
     of the tagged release, since the image is versioned separately.

## If something goes wrong

The tag is what identifies the release, so a bad tag can simply be replaced
before anyone depends on it:

```bash
git tag -d 2.3.0
git push origin :refs/tags/2.3.0
```

Then fix the problem and re-tag. If the GitHub Release was already created, delete
it in the web UI first.

## Recurring maintenance

- **New Python releases.** `requires-python` in `pyproject.toml` is capped at
  `<3.14` on purpose: `spacy==3.8.14` is the only remaining *core* dependency
  without wheels for newer interpreters. (`cvxopt==1.3.2` and
  `pygamma-agreement==0.5.9` are capped too, but they now live in the `pygamma`
  extra and so only constrain users who ask for it.) When the spaCy pin is
  relaxed - or if spaCy is made optional, since only `to_stanford_tsv` uses it -
  the cap can be widened. Widening means: update `requires-python` and the
  `Programming Language :: Python :: 3.x` classifiers, bump `.python-version`,
  and update `binder/runtime.txt`, the `python` version in `.readthedocs.yaml`
  and the `FROM` line of `docker/Dockerfile`.
- **Dependency updates.** There is no automated dependency bot, so run
  `uv lock --upgrade` periodically, re-run the checks in step 1, and commit the
  refreshed lockfile. Watch GitHub's Dependabot security alerts for the
  advisories that matter most.
