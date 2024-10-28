# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'MultiModuleTestStandUI'
copyright = '2024, ltsai'
author = 'ltsai'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
        'sphinx.ext.autodoc',
        'sphinx.ext.napoleon', ## google or numpy style
        'myst_parser', ## conda install myst_parser ### allow markdown syntax
        ]

myst_heading_anchors = 3  # Anchors for H1, H2, and H3


templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

import sys
import os
sys.path.insert(0, os.path.abspath('/home/ltsai/workspace/MultiModuletestStandUI/MultiModuletestStandUI/WebUI_Flask/kkk'))
