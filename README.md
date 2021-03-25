# Module for CATMA gitlab access

## Description
Classes for CATMA Projects, Annotation Collections and Tagsets.
The module is based on CATMAs git access: https://catma.de/documentation/git-access/



## Example

    from catma_gitlab.catma_gitlab_classes import Project
    
    # load project
    project_direction = your_project_direction  # where your CATMA projects are located 
    project_uuid = your_project_uuid            # your CATMA project git clone folder 
    project = Project(
        project_direction=project_direction,
        project_uuid=project_uuis,
        filter_intrinsic_markup=False
    )
    
    # show annotation collection
    for ac in project.annotation_collections:
        print(ac.name)
        
    # show annotations as pandas DataFrame
    for ac in project.annotation_collections:
        print(ac.df.head(5))
        
    # show tagsets and tags
    for tagset in project.tagsets:
        print(tagset.name)
        print([tag.name for tag in tagset.tag_list])
    