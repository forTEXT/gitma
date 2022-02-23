import setuptools

setuptools.setup(
    name="gitma",
    version="1.3.5",
    author="Michael Vauth",
    packages=setuptools.find_packages(),
    description="Load CATMA annotations from their git data",
    url="https://github.com/forTEXT/gitma",
    python_requires=">=3.5",
    install_requires=["pandas", "python-gitlab",
                      "matplotlib", "plotly", "spacy", "tabulate"]
)
