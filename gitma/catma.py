from typing import List, Dict
import gitlab
from gitma.project import CatmaProject


class Catma:
    """Class which represents all projects of a single CATMA user.

    Args:
        gitlab_access_token (str): A valid access token for CATMA's GitLab backend. Use the CATMA UI (https://app.catma.de)\
            or the GitLab backend (https://git.catma.de/users/sign_in) to get your personal access token.
    """
    def __init__(self, gitlab_access_token: str) -> None:
        #: The access token of the CATMA account.
        self.gitlab_access_token = gitlab_access_token

        gl = gitlab.Gitlab(
            url='https://git.catma.de/',
            private_token=gitlab_access_token
        )

        self._gitlab_projects = [
            # here we filter out CATMA 6 projects and resources by:
            # 1. using the search parameter (within GitLab, CATMA projects always have the 'CATMA_' prefix)
            # 2. excluding any projects with the '_root' suffix
            # 3. excluding any projects whose names are <= 42 characters long (resource projects imported from older versions of CATMA also have the 'CATMA_'
            #    prefix followed only by a GUID, as opposed to the newer 'D_', 'C_' and 'T_' prefixes for the different resource types)
            project for project in gl.projects.list(get_all=True, per_page=100, search='CATMA')
            if not project.name.endswith('_root') and not len(project.name) <= 42
        ]

        #: List of all projects that the CATMA account has access to.
        self.project_name_list: List[str] = [
            # NB: the actual name can be different if the project is renamed or the name contains whitespace or special characters
            project.name[43:] for project in self._gitlab_projects
        ]

        #: A dictionary with project names (excluding UUID) as keys and full project names (including UUID) as values.
        self.project_uuid_dict: Dict[str, str] = {
            project.name[43:]: project.name for project in self._gitlab_projects
        }

        #: A dictionary with project names (excluding UUID) as keys and instances of the CatmaProject class as values.
        #: The dict is empty as long as no projects have been loaded.
        self.project_dict: dict = {}

    def load_project_from_gitlab(self, project_name: str, backup_directory: str = './') -> None:
        """Loads a CATMA project from the GitLab backend.

        Args:
            project_name (str): The CATMA project name (or a part thereof - a search is performed in the GitLab backend using this value).
            backup_directory (str, optional): Where to clone the CATMA project. Defaults to './'.
        """
        self.project_dict[project_name] = CatmaProject(
            load_from_gitlab=True,
            gitlab_access_token=self.gitlab_access_token,
            project_name=project_name,
            backup_directory=backup_directory
        )

    def load_all_projects_from_gitlab(self) -> None:
        """Loads all projects that your CATMA account has access to after creating a local Git clone of these projects."""
        for project_name in self.project_name_list:
            self.load_project_from_gitlab(project_name=project_name)

    def load_local_project(
            self,
            projects_directory: str,
            project_name: str,
            included_acs: list = None,
            excluded_acs: list = None) -> None:
        """Loads a local CATMA project.

        Args:
            projects_directory (str): The directory where the CATMA project is located.
            project_name (str): The CATMA project name.
            included_acs (list, optional): The names of annotation collections to load. If set to None and excluded_acs is also None,\
                all annotation collections are loaded. Defaults to None.
            excluded_acs (list, optional): The names of annotation collections not to load. Defaults to None.
        """
        self.project_dict[project_name] = CatmaProject(
            projects_directory=projects_directory,
            project_name=project_name,
            included_acs=included_acs,
            excluded_acs=excluded_acs
        )

    def git_clone_command(self, project_name: str) -> str:
        """Returns the Git clone command for the given CATMA project.

        Args:
            project_name (str): The CATMA project's name.

        Returns:
            str: Git CLI clone command.
        """
        project_uuid = self.project_uuid_dict[project_name]
        project = [project for project in self._gitlab_projects if project.name == project_uuid][0]
        return f'git clone {project.http_url_to_repo}'
