#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "nothing"
# Date: 2019/5/24

from django.urls import re_path, path
from web.views import asset

urlpatterns = [
    path('asset.html/', asset.AssetView.as_view()),
    path('asset-json.html/', asset.AssetJsonView.as_view())
]


