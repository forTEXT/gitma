============
Introduction
============


**GitMA** is a Python package to process, analyze and manipulate `CATMA <https://catma.de/>`_ annotations via the `CATMA Git Access <https://catma.de/documentation/git-access/>`_.

Like the instances of the CATMA app, the GitMA package is hierarchically structured
by the following Python classes.

* Catma
  
  - CatmaProject

    + AnnotationCollection
  
      + Annotation
  
    + Text
    + Tagset

      + Tag

        + Property

All analytical methods in the package operate at the level of a 
:doc:`CatmaProject <class_project>`
or an
:doc:`AnnotationCollection <class_annotation_collection>`.

:doc:`AnnotationCollections <class_annotation_collection>`,
:doc:`Tagsests <class_tagset>`,
:doc:`Texts <class_text>` and
:doc:`Annotations <class_annotation_collection>` with their
:doc:`Tags <class_tag>` and
:doc:`Properties <class_property>`
are accessible via the
:doc:`CatmaProject class <class_project>`
and should not get loaded separately!


As a Python API for your annotation data, GitMA's main goal is the managing of large annotation projects.
The most important functionalities get introduced in the demo Jupyter Notebooks:

- `Load Annotation Data <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/load_project_from_gitlab.ipynb>`_
- `Explore Annotation <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/explore_annotations.ipynb>`_
- `Inter Annotator Agreement <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/inter_annotator_agreement.ipynb>`_
- `Gold Annotation Support <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/gold_annotation_support.ipynb>`_

---------------------------------------------------------
Examples
---------------------------------------------------------

Some examples used in the demo notebooks follow here:

Load your CATMA project
~~~~~~~~~~~~~~~~~~~~~~~
::

    from gitma import CatmaProject

    my_project = CatmaProject(
        project_name='<your_project>',
        gitlab_access_token='<your_access_token>',
        load_from_gitlab=True
    )


Explore your annotations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    my_project.ac_dict['<your_annotation_collection>'].plot_annotations()

.. raw:: html
   :file: img/plot_annotations.html



Process your annotation collections as Pandas DataFrame
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

    my_project.ac_dict['<your_annotation_collection>'].df


====  ======================  ===============================  ===========  =============  ==================================================  ====================================================================================================================================================================================  ==================================================  =============  ===========  ===================  ==========================  ==================
  ..  document                annotation collection            annotator    tag            left_context                                        annotation                                                                                                                                                                            right_context                                         start_point    end_point  date                 prop:characters             prop:intentional
====  ======================  ===============================  ===========  =============  ==================================================  ====================================================================================================================================================================================  ==================================================  =============  ===========  ===================  ==========================  ==================
   0  bettelweib_von_locarno  bettelweib-event_type-demo_user  DemoUser     stative_event  Weimar other Das Bettelweib von Locarno             Am Fuße der Alpen, bei Locarno im oberen Italien, befand sich ein altes, einem Marchese gehöriges Schloß                                                                              , das man jetzt, wenn man vom St. Gotthard kommt,            2320         2424  2022-03-03 14:55:18  []                          ['nan']
   1  bettelweib_von_locarno  bettelweib-event_type-demo_user  DemoUser     stative_event  sich ein altes, einem Marchese gehöriges Schloß,    das man jetzt in Schutt und Trümmern liegen sieht                                                                                                                                     : ein Schloß mit hohen und weitläufigen Zimmern, i           2426         2509  2022-03-03 14:56:02  []                          ['nan']
====  ======================  ===============================  ===========  =============  ==================================================  ====================================================================================================================================================================================  ==================================================  =============  ===========  ===================  ==========================  ==================



Cooccurrence networks
~~~~~~~~~~~~~~~~~~~~~
Plots cooccurrent annotations of the same document
(`Docs <https://gitma.readthedocs.io/en/latest/class_annotation_collection.html#gitma.AnnotationCollection.cooccurrence_network>`_):
::

    project.ac_dict['<your_first_annotation_collection>'].cooccurrence_network(
        character_distance=50,
        level='prop:characters'
    )
.. raw:: html
   :file: img/cooccurrence_network.html


Disagreement networks
~~~~~~~~~~~~~~~~~~~~~
Plots overlapping annotations of the same document by different annotation collections
(`Docs <https://gitma.readthedocs.io/en/latest/class_project.html#gitma.CatmaProject.disagreement_network>`_):
::

    project.disagreement_network(
        annotation_collections=[
            '<your_first_annotation_collection>',
            '<your_second_annotation_collection>',
        ],
        level='prop:characters'
    )

.. raw:: html
   :file: img/disagreement_network.html
