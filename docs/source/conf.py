# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import os
import sys
sys.path.insert(0, os.path.abspath('../../'))

# -- Use commonmark for markdown in docstrings
import commonmark
def docstring(app, what, name, obj, options, lines):
    md = '\n'.join(lines)
    ast = commonmark.Parser().parse(md)
    rst = commonmark.ReStructuredTextRenderer().render(ast)
    lines.clear()
    lines += rst.splitlines()


def setup(app):
    app.connect('autodoc-process-docstring', docstring)


# -- Project information -----------------------------------------------------

project = 'GitMA'
copyright = '2022, Michael Vauth'
author = 'Michael Vauth'

# The full version, including alpha/beta/rc tags
release = '1.5.1'

doctest_global_setup = "import gitma"
autodoc_default_flags = ['members']
autodoc_default_options = {
    'member-order': 'bysource'
}
autosummary_generate = True
master_doc = 'index'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.napoleon',      # reads docstrings in Google format
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'myst_parser',
    # 'sphinx.ext.githubpages',
    'sphinx_autodoc_typehints'
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []
add_module_names = False


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'pydata_sphinx_theme'
html_logo = "catma-gitlab-combo-favicon.png"

html_theme_options = {
    "icon_links": [
        {
            # Label for this link
            "name": "GitHub",
            # URL where the link will redirect
            "url": "https://github.com/forTEXT/gitma",  # required
            # Icon class (if "type": "fontawesome"), or path to local image (if "type": "local")
            "icon": "fab fa-github-square",
            # Whether icon should be a FontAwesome class, or a local file
        }
    ],
    "favicons": [
      {
         "rel": "icon",
         "sizes": "16x16",
         "href": "catma-gitlab-combo-favicon.png",
      }
    ]
}

html_sidebars = {
    "**": [
        # "logo-text.html",
        "searchbox.html",
        "sidebar-nav-bs.html",
        # "globaltoc.html",
        # "localtoc.html",
    ]
}


# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
