from catma_gitlab.project_class import CatmaProject

project_direction = 'demo_project/'
project_uuid = 'CATMA_13BFDD7D-0F8F-40A5-ACB1-3B058F67BBF0_test_corpus_root'
project = CatmaProject(
    project_direction=project_direction,
    project_uuid=project_uuid,
    filter_intrinsic_markup=False,
)

print(project.stats())
