# Module for CATMA gitlab access

## Description
Classes for CATMA Projects, Annotation Collections and Tagsets.
The module makes use of CATMAs git access: https://catma.de/documentation/git-access/



## Example

### Import

    from catma_gitlab.catma_gitlab_classes import CatmaProject
    
### Load Project
    
    project_direction = your_project_direction  # where your CATMA projects are located 
    project_uuid = your_project_uuid            # your CATMA project git clone folder 
    project = CatmaProject(
        project_direction=project_direction,
        project_uuid=project_uuid,
        filter_intrinsic_markup=False
    )
    
### Show Annotation Collections
    
    for ac in project.annotation_collections:
        print(ac.name)
        
### Show Annotations as Pandas DataFrame

    for ac in project.annotation_collections:
        print(ac.df.head(5))
        
### Show Tagsets and Tags
    for tagset in project.tagsets:
        print(tagset.name)
        print([tag.name for tag in tagset.tag_list])
        
### Change Property Values
    your_annotation_collection_name = ''
    ac = project.ac_dict[your_annotation_collection_name]
    for annotation in ac.annotations:
        annotation.set_property_values(
            tag='tag_name',
            prop='property_name',
            value=['property_value']
        )
        
### Compute Inter Annotator Agreement
    project.iaa(
        ac1='first_annotation_collection_name',
        ac2='second_annotation_collection_name',
        tag_filter=None,                     # else list with tag names
        filter_both_ac=False,
    )
        
    
    