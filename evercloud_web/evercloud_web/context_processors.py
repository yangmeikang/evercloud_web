#!/usr/bin/env python
# coding=utf-8

from django.conf import settings


def evercloud(request):

    return settings.SITE_CONFIG
