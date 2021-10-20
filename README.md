# Package for CATMA gitlab access

## Description
Classes for CATMA Projects, Annotation Collections and Tagsets.
The package makes use of CATMAs git access: https://catma.de/documentation/git-access/

## Installation
Install using `pip install git+https://github.com/forTEXT/catma_gitlab`

To install locally for development use: `pip install -e .`

## Demo

### Import

    from catma_gitlab import Catma, CatmaProject

### Load your CATMA Profile
To load your projects you can use the `Catma` class.
That may be useful if you want to load multiple CATMA projects or just list your Project Names.

    my_catma = Catma(gitlab_access_token='')    # accessible in the CATMA UI
    print(my_catma.project_name_list)

### Load a local CATMA Project with the `Catma` class
In most cases it is recomended to load (local) CATMA projects with the `CatmaProject` class.
    
    project_directory = ''

    # select a project's name that is located in direction
    project_name = my_catma.project_name_list[0]

    my_catma.load_local_project(
        project_directory=project_directory,
        project_name=project_name,
        excluded_acs=None,
    )

    # access project and show annotation progress
    my_catma.project_dict[project_name].plot_annotation_progression()



### Load a local Project
    
    project_directory = your_project_directory  # where your CATMA projects are located 
    project_uuid = your_project_uuid            # your CATMA project git clone folder 
    project = CatmaProject(
        project_directory=project_directory,
        project_uuid=project_uuid,
        filter_intrinsic_markup=False
    )

### Load a Project from CATMA GitLab

    project = CatmaProject(
        load_from_gitlab=True,
        gitlab_access_token=your_gitlab_token,  # accessible over the CATMA GUI
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
        
    
    