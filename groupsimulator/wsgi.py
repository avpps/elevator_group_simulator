"""
WSGI config for groupsimulator project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "groupsimulator.settings")

<<<<<<< HEAD
application = get_wsgi_application()
=======
application = get_wsgi_application() 
>>>>>>> d6ef397b75d5ef7882bff7f59fb0ade5740d3a9b
