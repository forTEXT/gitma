FROM continuumio/miniconda3:4.10.3p1

LABEL maintainer="GitMA Team" \
      version="0.0.2"

WORKDIR /opt/gitma

SHELL ["/bin/bash", "-c"]

RUN apt update && apt install -y git \
    && git clone https://github.com/forTEXT/gitma.git src \
    && conda create -q -y -n gitma python=3.9 \
    && source /opt/conda/bin/activate \
    && conda activate gitma \
    && pip install -q git+https://github.com/forTEXT/gitma \
    && pip install -q pygamma-agreement \
    && conda deactivate


ENTRYPOINT ["bash", "-c", "source /opt/conda/bin/activate && conda activate gitma \
&& jupyter notebook --notebook-dir=./src/demo_notebooks/ --ip='*' --port=8888 --no-browser --allow-root"]
