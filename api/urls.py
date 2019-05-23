#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "nothing"
# Date: 2019/5/20


from django.urls import path, include
from api import views

urlpatterns = [
    path('asset', views.AssetView.as_view())
]