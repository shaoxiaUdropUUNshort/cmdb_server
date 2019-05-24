#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "nothing"
# Date: 2019/5/24
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
# 这两个包组合使用，用于在CBV模式中，可以单独为某个类方法，取消token 验证
import json
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, reverse
from django.views import View

from repository import models


# import logging
# from repository import models
# from functools import update_wrapper
# HttpResponse, HttpResponseGone, HttpResponseNotAllowed, ImproperlyConfigured
# HttpResponsePermanentRedirect, HttpResponseRedirect, Http404
# from django.template.response import TemplateResponse
# from django.urls import reverse
# from django.utils.decorators import classonlymethod


class AssetView(View):
    # 扩展点，dispatch 在其他请求有共同的需求时使用
    # def dispatch(self, request, *args, **kwargs)
    def get(self, request, *args, **kwargs):
        # 数据库中取出数据。 全部通过ajax访问进行处理。
        return render(request, 'asset.html')

    def post(self, request, *args, **kwargs):
        return HttpResponse('OK')


# http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
class AssetJsonView(View):
    '''专门的处理 ajax 各种类型请求的， 视图'''

    def get(self, request, *args, **kwargs):
        table_config = [  # 这里确定的是列，有几个数据，就显示几列
            # display 用于控制页面的显示或隐藏
            {"query": 'id', 'title': "ID", "display": False,
             'text': {}},

            {"query": 'business_unit', 'title': "业务线", "display": True,
             'text': {'content': "{n}", 'kwargs': {'n': '@business_unit'}}},

            {"query": 'idc', 'title': "机房", "display": True,
             'text': {'content': "{n}", 'kwargs': {'n': '@idc'}}},

            {"query": 'cabinet_num', 'title': "机柜号", "display": True,
             'text': {'content': "{n}", 'kwargs': {'n': '@cabinet_num'}}},

            {"query": 'cabinet_order', 'title': "机柜中序号", "display": True,
             'text': {'content': "{n}", 'kwargs': {'n': '@cabinet_order'}}},

            {"query": 'device_type_id', 'title': "资产类型", "display": True,
             'text': {'content': "{n}", 'kwargs': {'n': '@@device_type_choices'}}},

            {"query": 'device_status_id', 'title': "资产状态", "display": True,
             'text': {'content': "{n}", 'kwargs': {'n': '@@device_status_choices'}}},

            {"query": None, 'title': "操作", "display": True,
             'text': {'content': "<a href='/web/asset-detail/{m}'>{n}</a>", 'kwargs': {'n': '查看详细', 'm': '@id'}}},
        ]

        # 单 @ 符号，表示需要从数据库去查询的，内容。前端js 需要从， data_list中找匹配的值。

        # [{'id': 1, 'business_unit': 1, 'idc': 1, 'cabinet_num': '11A', 'cabinet_order': '1'},
        # {'id': 2, 'business_unit': 2, 'idc': 2, 'cabinet_num': '12B', 'cabinet_order': '2'}]

        query_list = []
        for i in table_config:
            if not i['query']:
                continue
            query_list.append(i['query'])

        data_list = list(models.Asset.objects.values(*query_list))

        response = {
            "table_config": table_config,
            "data_list": data_list,
            'global_dict': {
                'device_type_choices': models.Asset.device_type_choices,  # 获取choice字段文本的信息。
                'device_status_choices': models.Asset.device_status_choices,  # 获取choice字段文本的信息。
            },

        }

        return JsonResponse(response)
