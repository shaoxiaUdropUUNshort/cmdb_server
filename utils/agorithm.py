#!/usr/bin/env python
# -*- coding:utf-8 -*-


def get_intersection(*args):
    '''
    获取所有set的并集
    :param args: set集合
    :return:并集列表
    '''
    base = args[0]
    result = base.intersection(*args)
    # intersection 求两个集合的并集。
    return list(result)


def get_exclude(total,part):
    '''传参时， total在前返回的结果就是。  total 中不在 part中存在的哪些。差集'''
    result = []
    for item in total:
        if item in part:
            pass
        else:
            result.append(item)
    return result


