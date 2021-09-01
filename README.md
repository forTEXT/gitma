# Package for CATMA gitlab access

## Description
Classes for CATMA Projects, Annotation Collections and Tagsets.
The package makes use of CATMAs git access: https://catma.de/documentation/git-access/

## Installation
Install using `pip install git+https://github.com/michaelvauth/catma_gitlab`

To install locally for development use: `pip install -e .`

## Example

### Import

    from catma_gitlab.project_class import CatmaProject
    
### Load local Project
    
    project_direction = your_project_direction  # where your CATMA projects are located 
    project_uuid = your_project_uuid            # your CATMA project git clone folder 
    project = CatmaProject(
        project_direction=project_direction,
        project_uuid=project_uuid,
        filter_intrinsic_markup=False
    )

### Load Project from CATMA GitLab

    project = CatmaProject(
        load_from_gitlab=True,
        private_gitlab_token=your_gitlab_token,  # accessible over the CATMA GUI
        project_name=your_catma_project_name
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
        
    
    