import setuptools

setuptools.setup(
    name="gitma",
    version="2.0.4",
    author="Michael Vauth",
    packages=setuptools.find_packages(),
    description="Load CATMA annotations from their Git data",
    url="https://github.com/forTEXT/gitma",
    python_requires=">3.9",
    install_requires=[
        "cvxopt",
        "jupyter",
        "networkx",
        "nltk",
        "numpy",
        "pandas",
        "plotly",
        "pygit2",
        "python-gitlab",
        "scipy",
        "Cython",
        # avoid spacy >=3.8.0 for now due to install problem on ARM Linux, ref: https://github.com/explosion/cython-blis/issues/117#issuecomment-2596810409
        "spacy<3.8.0",
        "tabulate"
    ]
)
