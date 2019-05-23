#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "nothing"
# Date: 2019/5/23


class BaseResponse(object):
    '''响应对象，用来保存 在更新资产途中的日志信息。 最后这些信息需要返回给前端页面，让管理员能看到'''
    def __init__(self):
        self.status = True
        self.message = None
        self.data = None
        self.error = None

