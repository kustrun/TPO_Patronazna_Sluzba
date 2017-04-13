# -*- coding: utf-8 -*-

"""
WSGI config for TPO_Patronazna_sluzba project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "TPO_Patronazna_sluzba.settings")

application = get_wsgi_application()
