from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
# 这两个包组合使用，用于在CBV模式中，可以单独为某个类方法，取消token 验证
from django.views import View
from django.http import JsonResponse
import json
from importlib import import_module
from utils.auth import api_auth
from api import config
from api.service import asset
from repository import models


# import logging
# from repository import models
# from functools import update_wrapper
# from django.core.exceptions import ImproperlyConfigured
# HttpResponse, HttpResponseGone, HttpResponseNotAllowed,
# HttpResponsePermanentRedirect, HttpResponseRedirect, Http404
# from django.template.response import TemplateResponse
# from django.urls import reverse
# from django.utils.decorators import classonlymethod

# Create your views here.


class AssetView(View):
    @method_decorator(csrf_exempt)  # 这个类中的函数 使用csrf_exempt进行装饰。 忽略token的验证
    def dispatch(self, request, *args, **kwargs):
        return super(AssetView, self).dispatch(request, *args, **kwargs)

    @method_decorator(api_auth)
    def get(self, request, *args, **kwargs):
        """
        更新或者添加资产信息
        :param request:
        :param args:
        :param kwargs:
        :return: 1000 成功;1001 接口授权失败;1002 数据库中资产不存在
        """
        response = asset.get_untreated_servers()
        return JsonResponse(response.__dict__)

    @method_decorator(api_auth)
    def post(self, request, *args, **kwargs):
        """
        更新或者添加资产信息
        :param request:
        :param args:
        :param kwargs:
        :return: 1000 成功;1001 接口授权失败;1002 数据库中资产不存在
        """
        server_info = json.loads(request.body.decode('utf-8'))  # 解码获取到服务器的信息表的字符串格式,
        server_info = json.loads(server_info)  # 将字符串格式装化成 字典格式

        hostname = server_info['hostname']
        ret = {'code': 1000, 'message': '[%s]更新完成' % hostname}
        # server_info 最新汇报服务器所有信息
        server_obj = models.Server.objects.filter(hostname=hostname).select_related('asset').first()
        # 通过主机名找到这台主机，跨表找到 asset 资产表。
        # 做这些的前提是，需要在数据库中先  录入服务器的 基本的信息。 否则数据采集来之后，不知道这个数据是属于谁的。
        if not server_obj:
            ret['code'] = 1002
            ret['message'] = '[%s]资产不存在' % hostname
            return JsonResponse(ret)

        # 利用反射机制导入模块，获取类并 传入参数后执行。
        for k, v in config.PLUGINS_DICT.items():
            # 'basic': 'api.service.asset.HandleBasic',
            model_path, class_name = v.rsplit(".", maxsplit=1)
            cls = getattr(import_module(model_path), class_name)
            response = cls.process(server_obj, server_info, None)  # response对象是，自定义的一个类对象。

            if not response.status:  # 如果有出现异常的更新， 返回相应状态码。
                ret['code'] = 1003
                ret['message'] = '[%s]资产更新异常' % hostname

            if hasattr(cls, 'update_last_time'):  # 更新一下 最后一次的资产更新时间。
                cls.update_last_time(server_obj, None)

        return JsonResponse(ret)

