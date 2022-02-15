from gitma.project import CatmaProject
from gitma.catma import Catma


# load a complete project

project_directory = './'
project_uuid = 'CATMA_13BFDD7D-0F8F-40A5-ACB1-3B058F67BBF0_test_corpus_root'

project = CatmaProject(
    project_directory=project_directory,
    project_uuid=project_uuid,
)

print(project.stats())


# use the Catma class, see all your projects and load some annotation collections from 1 project

my_catma = Catma(gitlab_access_token='')
print(my_catma.project_name_list)

my_catma.load_local_project(
    project_directory='',
    project_name='',
    included_acs=[]
)

print(my_catma.project_dict[''].stats())
