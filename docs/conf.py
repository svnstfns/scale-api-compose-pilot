"""Sphinx configuration for Scale API Compose Pilot documentation."""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so Sphinx can find the package
sys.path.insert(0, os.path.abspath('..'))

# Import the package to get version and metadata
from scale_api_compose_pilot import __version__, __author__

# -- Project information -----------------------------------------------------

project = 'Scale API Compose Pilot'
copyright = '2024, sst'
author = __author__
version = __version__
release = __version__

# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.automodule',
    'sphinx.ext.autosummary',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']
source_suffix = '.rst'
master_doc = 'index'

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_title = f"{project} {version}"
html_short_title = project

# -- Options for autodoc ----------------------------------------------------

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# -- Options for napoleon ---------------------------------------------------

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# -- Options for intersphinx ------------------------------------------------

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'aiohttp': ('https://docs.aiohttp.org/en/stable/', None),
}

# -- Options for autosummary ------------------------------------------------

autosummary_generate = True
autosummary_generate_overwrite = False