"""
Module that defines the Catma class.


Usage Example:

my_catma = Catma(gitlab_access_token='')
print(my_catma.project_list)

project_direction = ''
my_local_project = my_catma.load_local_project(
    project_directory=project_direction,
    project_name='EvENT'
)
print(my_local_project.stats())
"""

from re import search
import gitlab
from catma_gitlab.project import CatmaProject


class Catma:
    def __init__(self, gitlab_access_token: str) -> None:
        """Class which represent all Projects of 1 CATMA User.

        Args:
            gitlab_access_token (str): Token for gitlab access.
        """
        self.gitlab_acces_token = gitlab_access_token

        gl = gitlab.Gitlab(
            url='https://git.catma.de/',
            private_token=gitlab_access_token
        )

        self.project_list = [
            p.name[43:-5] for p in gl.projects.list(search='_root')]
        self.project_dict = {
            p.name[43:-5]: p.name for p in gl.projects.list(search='_root')
        }

    def load_project_from_gitlab(self, project_name: str) -> CatmaProject:
        return CatmaProject(
            load_from_gitlab=True,
            gitlab_access_token=self.gitlab_acces_token,
            project_name=project_name
        )

    def load_local_project(self, project_directory: str, project_name: str) -> CatmaProject:
        return CatmaProject(
            project_directory=project_directory,
            project_uuid=self.project_dict[project_name]
        )
