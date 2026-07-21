import os
import sys
import django

sys.path.insert(
    0,
    os.path.abspath('../..')
)

os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'ntandos_news.settings'
)

django.setup()

project = "Ntando's News"
copyright = "2026, Ntando Mtimkulu"
author = "Ntando Mtimkulu"
release = "1.0"

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = []

html_theme = 'alabaster'
html_static_path = ['_static']

autodoc_preserve_defaults = True
autodoc_member_order = 'bysource'
