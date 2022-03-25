from typing import List, Dict
import gitlab
from gitma.project import CatmaProject


class Catma:
    """Class which represents all Projects of 1 CATMA User.

    Args:
        gitlab_access_token (str): Token for gitlab access. Use the CATMA UI (https://app.catma.de/catma/)\
            or the CATMA Gitlab (https://git.catma.de/users/sign_in) to get your personal access token.
    """

    def __init__(self, gitlab_access_token: str) -> None:
        #: The access token of the CATMA account.
        self.gitlab_access_token = gitlab_access_token

        gl: gl.Gitlab = gitlab.Gitlab(
            url='https://git.catma.de/',
            private_token=gitlab_access_token
        )

        #: List of all projects within a CATMA account.
        self.project_name_list: List[str] = [
            p.name[43:-5] for p in gl.projects.list(search='_root')]

        #: A dictionary with project names as keys an projects UUIDs as values.
        self.project_uuid_dict: Dict[str, str] = {
            p.name[43:-5]: p.name for p in gl.projects.list(search='_root')
        }

        #: A dictionary with project names as keys and instances of the CatmaProject class as values.
        #: The dict is empty as long as no projects have been loaded.
        self.project_dict: dict = {}

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
        """Loads all CATMA projects in your account after creating a local Git clone
        of these projects.
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
            included_acs (list, optional): Annotation Collections to load. If set to None and excluded_acs is None too all annotation collections get loaded. Defaults to None.
            excluded_acs (list, optional): Annotation Collections not to load. Defaults to None.
        """
        self.project_dict[project_name] = CatmaProject(
            project_directory=project_directory,
            project_uuid=self.project_uuid_dict[project_name],
            included_acs=included_acs,
            excluded_acs=excluded_acs
        )

    def git_clone_command(self, project_name: str) -> str:
        """Creates Git clone command for the given CATMA project.

        Args:
            project_name (str): The project's name.

        Returns:
            str: Git clone command.
        """
        project_uuid = self.project_uuid_dict[project_name]
        project_url = f"https://git.catma.de/{project_uuid[:-5]}/{project_uuid}.git"
        return f'git clone --recurse-submodules {project_url}'
