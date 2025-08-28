# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys


sys.path.insert(0, os.path.abspath('.'))  # Add your source directory


project = 'MindRoot'
copyright = '2025, Jason Livesay'
author = 'Jason Livesay'
release = '9.10.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',      # Auto API docs
    'sphinx.ext.viewcode',     # View source code
    'sphinx.ext.napoleon',     # Google/NumPy docstrings
    'sphinx.ext.autosummary',  # Summary tables
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Switch to Furo theme for built-in dark mode
html_theme = 'furo'
html_theme_options = {
    'light_css_variables': {
        'color-brand-primary': '#007acc',
        'color-brand-content': '#007acc',
    },
    'dark_css_variables': {
        'color-brand-primary': '#ff7b72',
        'color-brand-content': '#ff7b72',
    },
    'sidebar_hide_name': True,
}

html_static_path = ['_static']

# Add custom CSS for additional dark mode styling
html_css_files = ['custom.css']
