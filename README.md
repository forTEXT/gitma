# Module for CATMA gitlab access

## Description
Classes for CATMA Projects, Annotation Collections and Tagsets.
The module is based on CATMAs git access: https://catma.de/documentation/git-access/



## Example

### Import

    from catma_gitlab.catma_gitlab_classes import CatmaProject
    
### Load project
    
    project_direction = your_project_direction  # where your CATMA projects are located 
    project_uuid = your_project_uuid            # your CATMA project git clone folder 
    project = CatmaProject(
        project_direction=project_direction,
        project_uuid=project_uuid,
        filter_intrinsic_markup=False
    )
    
### Show annotation collections
    
    for ac in project.annotation_collections:
        print(ac.name)
        
### Show annotations as pandas DataFrame

    for ac in project.annotation_collections:
        print(ac.df.head(5))
        
### Show tagsets and tags
    for tagset in project.tagsets:
        print(tagset.name)
        print([tag.name for tag in tagset.tag_list])
    