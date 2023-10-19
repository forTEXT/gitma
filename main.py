from gitma.catma import Catma


if __name__ == '__main__':
    # using the Catma class, see all your projects
    my_catma = Catma(gitlab_access_token='insert token here')
    print(f'Found the following projects:\n{my_catma.project_name_list}')

    # load a local project that has already been cloned and print some statistics
    print('\nLoading local project:\n')
    my_catma.load_local_project(
        projects_directory='./demo/projects/',
        project_name='CATMA_9385E190-13CD-44BE-8A06-32FA95B7EEFA_GitMA_Demo_Project'
    )
    print('\n')
    print(my_catma.project_dict['CATMA_9385E190-13CD-44BE-8A06-32FA95B7EEFA_GitMA_Demo_Project'].stats())

    # load a project from the GitLab backend and print some statistics
    print('\nLoading project from the GitLab backend:\n')
    my_catma.load_project_from_gitlab(
        project_name='insert project name here',
        backup_directory='./user_projects/'
    )
    print('\n')
    print(my_catma.project_dict['insert project name here'].stats())
