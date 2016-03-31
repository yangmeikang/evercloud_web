#!/usr/bin/env python

import os
import sys
import site

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
#ROOT_DIR = '/var/www/evercloud_web/evercloud_web'
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "evercloud_web.settings")

application = get_wsgi_application()
