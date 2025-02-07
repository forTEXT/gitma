# Sample build command: docker buildx build --platform linux/amd64,linux/arm64 --tag maltem/gitma-demo:0.0.10 --tag maltem/gitma-demo:latest --push .
# Consider adding --no-cache as per https://docs.docker.com/build/building/best-practices/#rebuild-your-images-often

FROM  condaforge/miniforge3
LABEL maintainer="GitMA Team" \
      version="0.0.10"

WORKDIR /opt/gitma

SHELL ["/bin/bash", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y \
        build-essential \
        cmake \
        git \
    && apt-get clean -y

RUN git clone https://github.com/forTEXT/gitma.git ./src \
    && cp -R ./src ./src_backup

RUN conda create --yes \
    --name gitma  \
    --channel conda-forge \
        python=3.9 \
        cvxopt=1.2.7 \
        coin-or-cbc \
        cvxpy \
        glpk \
        jupyterlab \
        matplotlib \
        networkx \
        nltk \
        numpy \
        pandas \
        pip \
        plotly \
        pygit2 \
        python-gitlab \
        qdldl-python \
        scipy \
        # avoid spacy >=3.8.0 for now due to install problem on ARM Linux, ref: https://github.com/explosion/cython-blis/issues/117#issuecomment-2596810409
        spacy\<3.8.0 \
        tabulate

RUN source /opt/conda/bin/activate \
    && conda activate gitma \
    && conda init bash \
    && python -m pip install \
        git+https://github.com/forTEXT/gitma \
        "pygamma-agreement[CBC]==0.5.6" \
    && conda clean -afy \
    && find /opt/conda/ -follow -type f -name '*.a' -delete \
    && find /opt/conda/ -follow -type f -name '*.pyc' -delete \
    && find /opt/conda/ -follow -type f -name '*.js.map' -delete

COPY gitma.sh .

ENTRYPOINT ["/bin/bash", "-c", "./gitma.sh"]
