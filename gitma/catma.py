"""
Module that defines the Catma class including all Projects.


Usage Example:

my_catma = Catma(gitlab_access_token='')
print(my_catma.project_list)

project_direction = ''
my_local_project = my_catma.load_local_project(
    project_directory=project_direction,
    project_name=''
)
print(my_local_project.stats())
"""

from typing import Dict
import gitlab
from gitma.project import CatmaProject


class Catma:
    def __init__(self, gitlab_access_token: str) -> None:
        """Class which represents all Projects of 1 CATMA User.

        Args:
            gitlab_access_token (str): Token for gitlab access.
        """
        self.gitlab_access_token = gitlab_access_token

        gl = gitlab.Gitlab(
            url='https://git.catma.de/',
            private_token=gitlab_access_token
        )

        self.project_name_list = [
            p.name[43:-5] for p in gl.projects.list(search='_root')]
        self.project_uuid_dict = {
            p.name[43:-5]: p.name for p in gl.projects.list(search='_root')
        }

        self.project_dict = {}

    def load_project_from_gitlab(self, project_name: str, backup_directory: str = './') -> None:
        """Load a CATMA Project from GitLab.

        Args:
            project_name (str): The CATMA Project name.
            backup_directory (str): Where to store the project.
        """
        self.project_dict[project_name] = CatmaProject(
            load_from_gitlab=True,
            gitlab_access_token=self.gitlab_access_token,
            project_name=project_name,
            backup_directory=backup_directory
        )

    def load_all_projects_from_gitlab(self) -> None:
        """Loads all CATMA project from GitLab in current directory.
        """
        for project_name in self.project_name_list:
            self.load_project_from_gitlab(project_name=project_name)

    def load_local_project(
            self,
            project_directory: str,
            project_name: str,
            included_acs: list = None,
            excluded_acs: list = None) -> None:
        """Loads a local CATMA Project and stores it in the project_dict.

        Args:
            project_directory (str): Directory where the CATMA Project is located.
            project_name (str): The CATMA Project name.
            included_acs (list, optional): Annotation Collections to load. Defaults to None.
            excluded_acs (list, optional): Annotation Collections not to load. Defaults to None.
        """
        self.project_dict[project_name] = CatmaProject(
            project_directory=project_directory,
            project_uuid=self.project_uuid_dict[project_name],
            included_acs=included_acs,
            excluded_acs=excluded_acs
        )

    def git_clone_command(self, project_name: str):
        project_uuid = self.project_uuid_dict[project_name]
        project_url = f"https://git.catma.de/{project_uuid[:-5]}/{project_uuid}.git"
        return f'git clone --recurse-submodules {project_url}'
