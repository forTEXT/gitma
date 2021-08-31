import setuptools

setuptools.setup(
    name="catma-gitlab",
    version="0.1.1",
    author="Michael Vauth",
    packages=setuptools.find_packages(),
    description="Load CATMA annotations from their git data",
    url="https://github.com/michaelvauth/catma_gitlab",
    python_requires=">=3.5",
    install_requires=["pandas"]
)
