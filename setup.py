import setuptools

setuptools.setup(
    name="gitma",
    version="2.1.0",
    author="Michael Vauth",
    packages=setuptools.find_packages(),
    description="Load CATMA annotations from their Git data",
    url="https://github.com/forTEXT/gitma",
    python_requires=">=3.13, <3.14",
    install_requires=[
        "cvxopt==1.3.2",
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
        "spacy==3.8.14",
        "tabulate"
    ]
)
