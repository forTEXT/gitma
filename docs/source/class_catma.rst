Catma
=====

.. autoclass:: gitma.Catma
   :members:
   :undoc-members:
   :show-inheritance:

Examples
--------

For details see the `demo notebook <https://github.com/forTEXT/gitma/blob/main/demo_notebooks/load_project_from_gitlab.ipynb>`_.

Load your account informations
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   >>> from gitma import Catma


   >>> my_catma = Catma(gitlab_access_token='<your_access_token>')
   >>> my_catma.project_name_list
   ['<project1>', '<project2>', '<project3>']


Load a project from the CATMA gitlab
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
::

   >>> my_catma.load_project_from_gitlab(
   ...   project_name='<insert your project name here>',
   ...   backup_directory='../projects/'
   ... )
   Loading Tagsets ...
	   Found 2 Tagset(s).
   Loading Documents ...
      Found 2 Document(s).
   Loading Annotation Collections ...
      Annotation Collection BETTELWEIB-EVENT_TYPE-DEMO_USER for BETTELWEIB_VON_LOCARNO
         Annotations: 72/72
      Annotation Collection BETTELWEIB-EVENT_TYPE-GOLD for BETTELWEIB_VON_LOCARNO
         Annotations: 48/48
      Annotation Collection INTRINSIC MARKUP for MICHAEL_KOHLHAAS
         Annotations: 216/216
      Annotation Collection INTRINSIC MARKUP for BETTELWEIB_VON_LOCARNO
         Annotations: 67/67


Access your project data
~~~~~~~~~~~~~~~~~~~~~~~~
::

   >>> my_catma.project_dict['project1'].plot_annotation_progression()

.. raw:: html
   :file: img/annotation_progression.html