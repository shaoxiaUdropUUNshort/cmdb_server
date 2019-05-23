#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "nothing"
# Date: 2019/5/23
import time
import hashlib
from django.http import JsonResponse
from cmdb_pro.settings import ASSET_AUTH_KEY, ASSET_AUTH_TIME

# 以访问过的列表， 也可以适应redis 这种数据库来做。 可以添加过期时间的。

ENCRYPT_LIST = []

# ASSET_AUTH_KEY = '299095cc-1330-11e5-b06a-a45e60bec08b'
# ASSET_AUTH_TIME = 2


def api_auth_method(request):
    auth_key = request.META.get('HTTP_AUTH_KEY')
    # {'auth-key': '99910e57e237bd10982338115c470a12|1558609626.815717'}
    if not auth_key:
        return False
    sp = auth_key.split("|")
    if len(sp) != 2:
        return False
    encrypt, timestamp = sp

    # 判断时间是否超时。
    timestamp = float(timestamp)
    limit_time = time.time() - ASSET_AUTH_TIME  # 服务器当前时间 减去一个过期时间。
    if limit_time > timestamp:
        # 如果 客户端发来的timestamp  比 limit_time 还要小的话。说明时间太久远了。直接忽视掉
        return False

    # 验证 两个MD5 是否相同
    m = hashlib.md5()
    m.update(bytes('%s|%s' % (ASSET_AUTH_KEY, timestamp), encoding='utf-8'))
    result = m.hexdigest()
    if encrypt != result:
        return False

    # 检查在访问列表中是否已经存在过
    exist = False
    del_keys = []
    for k, v in enumerate(ENCRYPT_LIST):
        m = v['time']
        n = v['encrypt']
        if limit_time > m:  # 列表中的访问记录是否大于，这个过期时间
            del_keys.append(k)
            continue
        if n == encrypt:
            exist = True  # 相等就代表，该md5已被使用过。不允许在被使用

    # 删除已过期的访问记录
    for k in del_keys:
        del ENCRYPT_LIST[k]

    if exist:
        return False
    ENCRYPT_LIST.append({'encrypt': encrypt, 'time':timestamp})
    return True


def api_auth(func):
    def inner(request, *args, **kwargs):
        if not api_auth_method(request):
            return JsonResponse({'code': 1001, 'message': 'API授权失败'}, json_dumps_params={'ensure_ascii': False})
        return func(request, *args, **kwargs)
    return inner


