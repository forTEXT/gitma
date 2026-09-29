# Sample build command (run from this directory). GITMA_VERSION must name a
# released GitMA tag: without it the build falls back to whatever `main` happens
# to be, and the published image is not reproducible.
#
#   docker buildx build --platform linux/amd64,linux/arm64 \
#       --build-arg GITMA_VERSION=2.2.0 \
#       --tag maltem/gitma-demo:0.0.13 --tag maltem/gitma-demo:latest --push .
#
# Consider adding --no-cache as per https://docs.docker.com/build/building/best-practices/#rebuild-your-images-often

# Debian (glibc) on purpose. This image is built entirely from PyPI wheels, and
# the manylinux wheels it depends on - cylp above all - are not published for
# musl, so an Alpine base would force a source build of CBC and friends.
FROM python:3.13-slim

LABEL maintainer="GitMA Team" \
      version="0.0.13"

# The GitMA git ref to build the image from. The default is for local test builds
# only - published images are built from a release tag, see the build command above.
ARG GITMA_VERSION=main

WORKDIR /opt/gitma

SHELL ["/bin/bash", "-c"]

# git is a *runtime* dependency, not just a build-time one: GitMA shells out to it
# to pull, commit and push annotations.
#
# Note what is deliberately absent: there is no compiler toolchain. Every native
# dependency has to arrive as a wheel, so if one ever stops publishing wheels for
# a platform this build fails loudly here instead of silently compiling from
# source (or, worse, producing an image that only breaks at runtime). Pure-Python
# sdists such as textgrid still install fine without a compiler.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        git \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --depth 1 --branch "${GITMA_VERSION}" https://github.com/forTEXT/gitma.git ./src \
    && cp -R ./src ./src_backup

# jupyterlab is what the demo menu launches. It is intentionally not a GitMA
# runtime dependency (see the `notebooks` dependency group in pyproject.toml), so
# this image has to ask for it explicitly. Everything else - pandas, spacy, the
# pygamma solver stack - is resolved from GitMA's own metadata.
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        jupyterlab \
        "gitma[pygamma] @ git+https://github.com/forTEXT/gitma@${GITMA_VERSION}"

# Guard the one assumption that is easy to get silently wrong. pygamma-agreement
# uses the CBC solver only if `import cylp` succeeds and otherwise falls back to
# GLPK, which the PyPI cvxopt wheels are not built with - so a bad install would
# not surface until a user computed a gamma agreement. Checking it at build time
# means a broken image never gets published.
RUN python -c "import cylp, cvxpy, gitma; \
    assert cvxpy.CBC in cvxpy.installed_solvers(), \
    f'CBC solver missing, got {cvxpy.installed_solvers()}'"

COPY gitma.sh .

ENTRYPOINT ["/bin/bash", "-c", "./gitma.sh"]
