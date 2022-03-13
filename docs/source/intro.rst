============
Introduction
============


**GitMA** is a python Package to process, analyze and manipulate `CATMA <https://catma.de/>`_ annotations via the `CATMA Git Access <https://catma.de/documentation/git-access/>`_.

------------
Architecture
------------

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

----------
Motivation
----------

As a Python API for your annotation data, GitMA's main goal is the managing of large annotation projects.
The most important functionalities get introduced in the demo Jupyter Notebooks.

---------------------------------------------------------
Access your CATMA profile and load your CATMA annotations
---------------------------------------------------------

`In the first Notebook <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/load_project_from_gitlab.ipynb>`_ you can use **GitMA** to access your CATMA account via an access token.

**Load your CATMA project with the** ``CatmaProject`` **class**::

    from gitma import CatmaProject

    my_project = CatmaProject(
        project_name='<your_project>',
        gitlab_access_token='<your_access_token>',
        load_from_gitlab=True
    )


------------------------------------------
Explore and analyze your CATMA annotations
------------------------------------------

`The second Notebook <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/inter_annotator_agreement.ipynb>`_ provides methods to explore your annotations with interactive vizualisations and analyze your annotation data with pandas.

**Explore all annotation collections in your CATMA project with the** ``plot_interactive()`` **method**::

    my_project.plot_interactive()

**Explore all annotations in a selected annotation collection using the** ``ac_dict`` **and the** ``plot_annotations()`` **method**::

    my_project.ac_dict['<your_annotation_collection>'].plot_annotations()

**Get your annotation collections as Pandas DataFrame**::

    my_project.ac_dict['<your_annotation_collection>'].df


====  ======================  ===============================  ===========  =============  ==================================================  ====================================================================================================================================================================================  ==================================================  =============  ===========  ===================  ==========================  ==================
  ..  document                annotation collection            annotator    tag            left_context                                        annotation                                                                                                                                                                            right_context                                         start_point    end_point  date                 prop:characters             prop:intentional
====  ======================  ===============================  ===========  =============  ==================================================  ====================================================================================================================================================================================  ==================================================  =============  ===========  ===================  ==========================  ==================
   0  bettelweib_von_locarno  bettelweib-event_type-demo_user  DemoUser     stative_event  Weimar other Das Bettelweib von Locarno             Am Fuße der Alpen, bei Locarno im oberen Italien, befand sich ein altes, einem Marchese gehöriges Schloß                                                                              , das man jetzt, wenn man vom St. Gotthard kommt,            2320         2424  2022-03-03 14:55:18  []                          ['nan']
   1  bettelweib_von_locarno  bettelweib-event_type-demo_user  DemoUser     stative_event  sich ein altes, einem Marchese gehöriges Schloß,    das man jetzt in Schutt und Trümmern liegen sieht                                                                                                                                     : ein Schloß mit hohen und weitläufigen Zimmern, i           2426         2509  2022-03-03 14:56:02  []                          ['nan']
   2  bettelweib_von_locarno  bettelweib-event_type-demo_user  DemoUser     non_event      s, einem Marchese gehöriges Schloß, das man jetzt,  wenn man vom St. Gotthard kommt                                                                                                                                                       , in Schutt und Trümmern liegen sieht: ein Schloß            2440         2472  2022-03-03 14:56:14  []                          ['nan']
   3  bettelweib_von_locarno  bettelweib-event_type-demo_user  DemoUser     process_event  thard kommt, in Schutt und Trümmern liegen sieht:   ein Schloß mit hohen und weitläufigen Zimmern, in deren einem einst, auf Stroh, das man ihr unterschüttete, eine alte kranke Frau von der Hausfrau aus Mitleiden gebettet worden war  . Der Marchese, der, bei der Rückkehr von der Jagd           2511         2741  2022-03-03 14:57:07  ['bettelweib', 'marquise']  ['yes']
   4  bettelweib_von_locarno  bettelweib-event_type-demo_user  DemoUser     process_event  as man ihr unterschüttete, eine alte kranke Frau,   die sich bettelnd vor der Tür eingefunden hatte                                                                                                                                       , von der Hausfrau aus Mitleiden gebettet worden w           2642         2689  2022-03-03 14:59:17  ['bettelweib']              ['yes']
====  ======================  ===============================  ===========  =============  ==================================================  ====================================================================================================================================================================================  ==================================================  =============  ===========  ===================  ==========================  ==================


------------------------------------------------
Evaluate your CATMA annotations with IAA metrics
------------------------------------------------

`The third Notebook <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/explore_annotations.ipynb>`_ shows how to cumpute the Inter Annotator Agreemment (IAA) for your Annotations::
    
    my_project.get_iaa(
        ac1_name='<your_first_annotation_collection>',
        ac2_name='<your_second_annotation_collection>'
    )



------------------------------------
Support your gold annotation process
------------------------------------

With `the fourth Notebook <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/gold_annotation_support.ipynb>`_ you learn how to automate parts of your gold annotation process::

    my_project.create_gold_annotations(
        ac_1_name='<your_first_annotation_collection>',               
        ac_2_name='<your_second_annotation_collection>',               
        gold_ac_name='<your_gold_annotation_collection>',
        excluded_tags=[],
        min_overlap=0.95,               
        same_tag=True,
        property_values='matching',     
        push_to_gitlab=False            
    )
