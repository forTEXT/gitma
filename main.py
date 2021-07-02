from catma_gitlab.project_class import CatmaProject

project_direction = '../../catma_backup2'
project_uuid = 'CATMA_DD5E9DF1-0F5C-4FBD-B333-D507976CA3C7_EvENT_root'
project = CatmaProject(
    project_direction=project_direction,
    root_direction=project_uuid,
    filter_intrinsic_markup=False)

project.plot_progression(ac_filter=['Effi_Briest_MW', 'Effi_Briest_GS'])
