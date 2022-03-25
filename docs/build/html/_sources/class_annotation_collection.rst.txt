AnnotationCollection
=====================

.. autoclass:: gitma.AnnotationCollection
   :members:
   :undoc-members:
   :show-inheritance:


Examples
--------

Add property values via csv table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``AnnotationCollection`` class can be used to add property values to existing annotations using a csv table.

**Step 1:** Load your project and create a csv table to annotate the existing annotations/properties:
::

   import gitma

   project = gitma.CatmaProject(
      project_name='<your_project_name>',
      project_directory='<your_backup_folder>'
   )

   project.ac_dict['<your_annotation_collection_name>'].write_annotation_csv(
      filename='PropertyAnnotationTable'  # default name
   )

The method ``write_annotation_csv`` creates a csv table in in this format:

==========================================  =====================  ========================================================================  =============  ===========  ================
id                                          annotation_collection  text                                                                      tag            property     values
==========================================  =====================  ========================================================================  =============  ===========  ================
CATMA_95259D62-E441-4009-AD8D-7F5124BF2323  bettelweib-event_type  Am Fuße der Alpen, bei Locarno im oberen Italien, befand sich ein Schloß  stative_event  characters   marquis,marquise
CATMA_AB9A223C-C6F7-495A-817F-ED57E1B69A70  bettelweib-event_type  das man jetzt in Schutt und Trümmern liegen sieht                         process_event  intentional  yes
CATMA_AB9A223C-C6F7-495A-817F-ED57E1B69A70  bettelweib-event_type  das man jetzt in Schutt und Trümmern liegen sieht                         process_event  characters   
CATMA_2A4C8A4E-2842-44D2-B2E2-F9A6AE2B8063  bettelweib-event_type  wenn man  vom St. Gotthard kommt                                          non_event      characters   
==========================================  =====================  ========================================================================  =============  ===========  ================

**Step 2:** Add property values:

For every property per annotation a table row will be created.

.. caution::
   In these tables only the values column is editable!

If you want to add multiple values for a property seperate the values by a comma.
It is recommended to use a csv editor like https://edit-csv.net/.
Finish your annotations by saving the csv file.


**Step 3:** Load the added property values in your CATMA project

After you finished the property annotations within the csv file you can load the annotations to the CATMA gitlab.
::

   project.ac_dict['<your_annotation_collection_name'].read_annotation_csv(
      filename='PropertyAnnotationTable.csv',   # default name
      push_to_gitlab=True                       # default is False
   )


.. caution::
   The push to gitlab will only work if you have git installed and your CATMA access token is stored in the git credential manager.

**Step 4 (optional):** Import your annotation to CATMA

If ``push_to_gitlab=False`` you can push the changed annotations to gitlab on your own.
To do so the ``read_annotation_csv`` method will print the annotation collection's directory.
Use the git bash or another terminal, go to the annotation collection's directory and run::
   
   git add .
   git commit -m 'new property annotations'
   git push origin HEAD:master
