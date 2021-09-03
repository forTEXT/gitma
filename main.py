from catma_gitlab.project import CatmaProject
from catma_gitlab.catma import Catma

project_directory = './'
project_uuid = 'CATMA_13BFDD7D-0F8F-40A5-ACB1-3B058F67BBF0_test_corpus_root'

project = CatmaProject(
    project_directory=project_directory,
    project_uuid=project_uuid,
)

print(project.stats())
