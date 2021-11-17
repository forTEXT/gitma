import setuptools

setuptools.setup(
    name="catma-gitlab",
    version="1.1.1",
    author="Michael Vauth",
    packages=setuptools.find_packages(),
    description="Load CATMA annotations from their git data",
    url="https://github.com/forTEXT/catma_gitlab",
    python_requires=">=3.5",
    install_requires=["pandas", "python-gitlab",
                      "matplotlib", "plotly", "spacy", "tabulate"]
)
