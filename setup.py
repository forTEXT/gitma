import setuptools

setuptools.setup(
    name="gitma",
    version="1.5.5",
    author="Michael Vauth",
    packages=setuptools.find_packages(),
    description="Load CATMA annotations from their Git data",
    url="https://github.com/forTEXT/gitma",
    python_requires=">=3.7",
    install_requires=[
        "cvxopt==1.2.7",
        "jupyter",
        "networkx",
        "nltk",
        "numpy",
        "pandas",
        "plotly",
        "pygit2",
        "python-gitlab",
        "scipy",
        "spacy",
        "tabulate"
    ]
)
