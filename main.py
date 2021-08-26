from catma_gitlab.project_class import CatmaProject

project_direction = '.'
project_uuid = 'CATMA_13BFDD7D-0F8F-40A5-ACB1-3B058F67BBF0_test_corpus_root'
project = CatmaProject(
    project_direction=project_direction,
    root_direction=project_uuid,
    filter_intrinsic_markup=False,
)

project.create_gold_annotations(
    ac_1_name='ac_1',
    ac_2_name='ac_2',
    gold_ac_name='gold_annotation',
    excluded_tags=[],
    min_overlap=0.95,
    property_values='matching'
)
