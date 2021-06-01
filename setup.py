import setuptools

setuptools.setup(
    name="catma-gitlab",
    version="0.0.1",
    author="Michael Vauth",
    description="Load CATMA annotations from their git data",
    url="https://github.com/michaelvauth/catma_gitlab",
    package_dir={},
    python_requires=">=3.5",
    install_requires=["pandas"]
)
