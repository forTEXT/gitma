CatmaProject
============

.. autoclass:: gitma.CatmaProject
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

Load a local CATMA project
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you load a CATMA project you already have cloned only the project's name and its location
are required to load the project::

   project = gitma.CatmaProject(
      project_name='DemoProject',
      projects_directory='../user_projects/'
   )

Adding the paramter ``included_acs``, ``excluded_acs`` and ``ac_filter_keyword``, you can select which annotation collections
get loaded.
Assuming you have a project with three annotation collections named 'ac1', 'ac2' and 'AC3' you can select the two first annotation
collections by any of these methods::
   
   # option 1
   project = gitma.CatmaProject(
      project_name='DemoProject',
      projects_directory='../user_projects/',
      included_acs=['ac1', 'ac2']
   )

   # option 2
   project = gitma.CatmaProject(
      project_name='DemoProject',
      projects_directory='../user_projects/',
      excluded_acs=['AC3']
   )

   # option 3
   project = gitma.CatmaProject(
      project_name='DemoProject',
      projects_directory='../user_projects/',
      ac_filter_keyword='ac'
   )


Load a remote CATMA project
~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you load your project from the CATMA gitlab three further paramters are required::

   project = gitma.CatmaProject(
      project_name='DemoProject',
      load_from_gitlab=True,
      gitlab_access_token='<your_access_token>',
      backup_directory='../user_projects/'
   )

By loading a remote CATMA project it will be cloned in the ``backup_directory``.
After you loaded a CATMA project in this directory once you have to load this project as a local project, as demonstrated above.


Plot a cooccurrence network for the annotations in your project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can plot coocurrent annotations::
   
   project.cooccurrence_network()


You can customize your network by the following parameters::

   project.cooccurrence_network(
      annotation_collections=[      # define the included annotation collections
         '<your_first_annotation_collection>',
         '<your_second_annotation_collection>'
      ],
      level='prop:<your_property>', # set a property as level
      character_distance=50,        # define which distance is considered cooccurrent
      included_tags=None,           # define a list with tags included
      excluded_tags=None,           # define a list with tags excluded
      save_as_gexf='my_gephi_file'  # save your network as Gephi file
   )