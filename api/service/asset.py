#! /usr/bin/env python
# -*- coding: utf-8 -*-
# __author__ = "nothing"
# Date: 2019/5/23
import traceback
import datetime
from utils.response import BaseResponse
from utils import agorithm
from repository import models
from django.db.models import Q


def get_untreated_servers():
    response = BaseResponse()
    '''
    __gt 大于 
    __gte 大于等于
    __lt 小于 
    __lte 小于等于
    '''
    try:
        current_date = datetime.date.today()  # 拿到今天的时间

        # 查询今日未 采集资产的主机名
        condition_date = Q()
        condition_date.connector = "OR"  # 使添加进来条件是 OR 关系。
        condition_date.children.append(('asset__latest_date__lt', current_date))  # 最后一次更新时间 小于当前天数的。
        condition_date.children.append(("asset__latest_date", None))  # 最后一次更新时间是 空的。

        # 在线状态的服务器
        condition_status = Q()
        condition_status.children.append(('asset__device_status_id', '2'))  # 在线状态 choice 选项为2

        # 嵌套两个 Q 查询。 类似于  (id=1 or id=2 and (id=3 or id =4))
        condition = Q()
        condition.add(condition_date, 'AND')
        condition.add(condition_status, 'AND')
        # 这两个套嵌的条件， 关系为 AND

        # 过滤出符合条件的 服务器的。 主机名
        result = models.Server.objects.filter(condition).values('hostname')
        response.data = list(result)
        response.status = True
    except Exception as e:
        response.status = False
        models.ErrorLog.objects.create(asset_obj=None, title='get_untreated_servers', content=traceback.format_exc())

    return response

# ############# 操作基本信息（cpu和主板） #############
# 操作基本，并记录操作日志
# 更新cpu和主板信息
class HandleBasic(object):
    '''
    "os_platform": "Linux",
    "hostname": "c1.com",
    "os_version": "CentOS release 6.6 (Final)",

    "cpu": {
        "status": True, "message": "null",
        "data": {"cpu_count": 24, "cpu_physical_count": 2, "cpu_model": " Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.10GHz"},
        "error": "null"
    },

    "main_board": {
        "status": True, "message": "null",
        "data": {"manufacturer": "Parallels Software International Inc.",
                 "model": "Parallels Virtual Platform",
                 "sn": "Parallels-1A 1B CB 3B 64 66 4B 13 86 B0 86 FF 7E 2B 20 30"},
        "error": "null"
    },
    '''

    @staticmethod
    def process(server_obj, server_info, user_obj):
        '''对资产进行更新'''
        response = BaseResponse()
        try:
            log_list = []
            main_board = server_info['main_board']['data']
            cpu = server_info['cpu']['data']
            if server_obj.os_platform != server_info['os_platform']:
                log_list.append('操作系统由%s变更为%s' % (server_obj.os_platform, server_info['os_platform']))
                server_obj.os_platform = server_info['os_platform']

            if server_obj.os_version != server_info['os_version']:
                log_list.append('操作系统版本由%s变更为%s' % (server_obj.os_version, server_info['os_version']))
                server_obj.os_version = server_info['os_version']

            if server_obj.sn != main_board['sn']:
                log_list.append('主板由%s变更为%s' % (server_obj.sn, main_board['sn']))
                server_obj.sn = main_board['sn']

            if server_obj.manufacturer != main_board['manufacturer']:
                log_list.append('主板厂商由%s变更为%s' % (server_obj.manufacturer, main_board['manufacturer']))
                server_obj.os_platform = main_board['manufacturer']

            if server_obj.model != main_board['model']:
                log_list.append('主板型号由%s变更为%s' % (server_obj.model, main_board['model']))
                server_obj.model = main_board['manufacturer']

            if server_obj.cpu_count != cpu['cpu_count']:
                log_list.append(u'CPU逻辑核数由%s变更为%s' % (server_obj.cpu_count, cpu['cpu_count'],))
                server_obj.model = cpu['cpu_count']

            if server_obj.cpu_physical_count != cpu['cpu_physical_count']:
                log_list.append(
                    u'CPU物理核数由%s变更为%s' % (server_obj.cpu_physical_count, cpu['cpu_physical_count'],))
                server_obj.cpu_physical_count = cpu['cpu_physical_count']

            if server_obj.cpu_model != cpu['cpu_model']:
                log_list.append(u'CPU型号由%s变更为%s' % (server_obj.cpu_model, cpu['cpu_model'],))
                server_obj.cpu_model = cpu['cpu_model']

            server_obj.save()
            if log_list:
                models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj,
                                                  content=';'.join(log_list))
        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset, title='basic-run',
                                           content=traceback.format_exc())
        return response

    @staticmethod
    def update_last_time(server_obj, user_obj):
        '''记录一下 最后一次更新资产的时间。'''
        response = BaseResponse()
        try:
            current_date = datetime.date.today()  # 2018-01-11
            server_obj.asset.latest_date = current_date
            server_obj.asset.save()
            models.AssetRecord.objects.create(asset_obj=server_obj, content='资产汇报', creator=user_obj)
        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset, title='basic-run',
                                           content=traceback.format_exc())
        return response


# ############# 操作网卡信息 #############
# 操作网卡，并记录操作日志
# 添加网卡
# 删除网卡
# 更新网卡信息
class HandleNic(object):
    '''
    "nic": {"status": True, "message": "null",
    "data": {"eth0": {"up": True, "hwaddr": "00:1c:42:a5:57:7a", "ipaddrs": "10.211.55.4",
                      "netmask": "255.255.255.0"}},
    "error": "null"
    }'''
    @staticmethod
    def process(server_obj, server_info, user_obj):
        response = BaseResponse()
        nic_info = server_info['nic']
        if not nic_info['status']:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_info, title='nic-agent', content=nic_info['error'])
            return response
        client_nic_dict = nic_info['data']
        nic_obj_list = models.NIC.objects.filter(server_obj=server_obj)
        nic_name_list = map(lambda x: x, (item.name for item in nic_obj_list))

        # 数据库有 新汇报的也有， 但是数据不相同的.
        # 根据网卡的名字进行判断， 因为其他的信息都是，绑定在这张网卡上的。 使用名字进行判定就足够了
        update_list = agorithm.get_intersection(set(client_nic_dict.keys()), set(nic_name_list))
        # 数据库没有 但是新汇报的 有的。 求的是数据库中不存在的
        add_list = agorithm.get_exclude(client_nic_dict, nic_name_list)
        # 数据库有 但是新汇报的 没有的
        del_list = agorithm.get_exclude(nic_name_list, client_nic_dict)

        HandleNic._add_nic(add_list, client_nic_dict, server_obj, user_obj)  # 添加
        HandleNic._update_nic(update_list, nic_obj_list, client_nic_dict, server_obj, user_obj)  # 更新
        HandleNic._del_nic(del_list, nic_obj_list, server_obj, user_obj)  # 删除

        return response

    @staticmethod
    def _add_nic(add_list, client_nic_dict, server_obj, user_obj):
        for item in add_list:  # add_list中存储的是 网卡的name字段
            cur_nic_dict = client_nic_dict[item]  # 从汇报的数据中取出对应的数据
            cur_nic_dict['name'] = item  # 汇报来的信息是没有 name 键的。保存到数据库时添加上这个 name 的键，并以 eth0 为值
            cur_nic_dict['server_obj'] = server_obj
            log_str = '[新增网卡]{name}:mac地址为{hwaddr};状态为{up};掩码为{netmask};IP地址为{ipaddrs}'.format(**cur_nic_dict)
            models.NIC.objects.create(**cur_nic_dict)
            # 增加一条网卡信息
            models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)
            # 增加一条资产变更记录

    @staticmethod
    def _del_nic(del_list, nic_obj_list, server_obj, user_obj):
        for item in nic_obj_list:
            if item.name in del_list:
                log_str = '[移除网卡]{name}:mac地址为{hwaddr};状态为{up};掩码为{netmask};IP地址为{ipaddrs}'.format(**item.__dict__)
                # 因为需要从 表模型中才能拿到完整的数据， 表模型也是类 使用  __dict__ 取出字典格式的数据。
                item.delete()  # 执行删除命令
                models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)
                # 添加资产变更记录

    @staticmethod
    def _update_nic(update_list, nic_obj_list, client_nic_dict, server_obj, user_obj):
        '''资产的更新，需要更加详细的。汇报'''
        for item in nic_obj_list:
            print(item, type(item))
            if item.name in update_list:
                log_list = []

                new_hwaddr = client_nic_dict[item.name]['hwaddr']
                if new_hwaddr != item.hwaddr:
                    log_list.append(u'更新网卡%s:mac地址由%s变更为%s' % (item.name, item.hwaddr, new_hwaddr))
                    item.hwaddr = new_hwaddr
                new_up = client_nic_dict[item.name]['up']
                if item.up != new_up:
                    log_list.append(u"[更新网卡]%s:状态由%s变更为%s" % (item.name, item.up, new_up))
                    item.up = new_up
                new_netmask = client_nic_dict[item.name]['netmask']
                if item.netmask != new_netmask:
                    log_list.append(u"[更新网卡]%s:掩码由%s变更为%s" % (item.name, item.netmask, new_netmask))
                    item.netmask = new_netmask
                new_ipaddrs = client_nic_dict[item.name]['ipaddrs']
                if item.ipaddrs != new_ipaddrs:
                    log_list.append(u"[更新网卡]%s:IP地址由%s变更为%s" % (item.name, item.ipaddrs, new_ipaddrs))
                    item.ipaddrs = new_ipaddrs
                item.save()
                if log_list:  # 如果有变更的信息，就更新资产记录表. 每条每条的单独记录
                    models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj,
                                                      content=';'.join(log_list))


# ############# 操作内存信息 #############
# 操作内存，并记录操作日志
# 添加内存
# 删除内存
# 更新内存信息
class HandleMemory(object):
    '''
    "memory": {"status": True, "message": "null",
           "data": {"DIMM #0": {"capacity": 1024, "slot": "DIMM #0", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"},
                    "DIMM #1": {"capacity": 0, "slot": "DIMM #1", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"},
                    "DIMM #2": {"capacity": 0, "slot": "DIMM #2", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"},
                    "DIMM #3": {"capacity": 0, "slot": "DIMM #3", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"},
                    "DIMM #4": {"capacity": 0, "slot": "DIMM #4", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"},
                    "DIMM #5": {"capacity": 0, "slot": "DIMM #5", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"},
                    "DIMM #6": {"capacity": 0, "slot": "DIMM #6", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"},
                    "DIMM #7": {"capacity": 0, "slot": "DIMM #7", "model": "DRAM", "speed": "667 MHz",
                                "manufacturer": "Not Specified", "sn": "Not Specified"}},
           "error": "null"
           },

    '''
    @staticmethod
    def process(server_obj, server_info, user_obj):
        response = BaseResponse()
        try:
            mem_info = server_info['memory']
            if not mem_info['status']:
                models.ErrorLog.objects.create(asset_obj=server_obj.asset, title='memory-agent',
                                               content=mem_info['error'])
                response.status = False
                return response

            client_mem_dict = mem_info['data']

            mem_obj_list = models.Memory.objects.filter(server_obj=server_obj)

            mem_slots = map(lambda x: x, (item.slot for item in mem_obj_list))

            update_list = agorithm.get_intersection(set(client_mem_dict.keys()), set(mem_slots))
            add_list = agorithm.get_exclude(client_mem_dict.keys(), update_list)
            del_list = agorithm.get_exclude(mem_slots, update_list)

            HandleMemory._add_memory(add_list, client_mem_dict, server_obj, user_obj)
            HandleMemory._update_memory(update_list, mem_obj_list, client_mem_dict, server_obj, user_obj)
            HandleMemory._del_memory(del_list, mem_obj_list, server_obj, user_obj)
        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset, title='memory-run',
                                           content=traceback.format_exc())

        return response

    @staticmethod
    def _add_memory(add_list, client_mem_dict, server_obj, user_obj):
        for item in add_list:
            cur_mem_dict = client_mem_dict[item]
            log_str = '[新增内存]插槽为{slot};容量为{capacity};类型为{model};速度为{speed};厂商为{manufacturer};SN号为{sn}'.format(
                **cur_mem_dict)
            cur_mem_dict['server_obj'] = server_obj
            models.Memory.objects.create(**cur_mem_dict)
            models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _del_memory(del_list, mem_objs, server_obj, user_obj):
        for item in mem_objs:
            if item.slot in del_list:
                log_str = '[移除内存]插槽为{slot};容量为{capacity};类型为{model};速度为{speed};厂商为{manufacturer};SN号为{sn}'.format(
                    **item.__dict__)
                item.delete()
                models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _update_memory(update_list, mem_objs, client_mem_dict, server_obj, user_obj):
        for item in mem_objs:
            if item.slot in update_list:
                log_list = []

                new_manufacturer = client_mem_dict[item.slot]['manufacturer']
                if item.manufacturer != new_manufacturer:
                    log_list.append(u"[更新内存]%s:厂商由%s变更为%s" % (item.slot, item.manufacturer, new_manufacturer))
                    item.manufacturer = new_manufacturer

                new_model = client_mem_dict[item.slot]['model']
                if item.model != new_model:
                    log_list.append(u"[更新内存]%s:型号由%s变更为%s" % (item.slot, item.model, new_model))
                    item.model = new_model

                new_capacity = client_mem_dict[item.slot]['capacity']
                if item.capacity != new_capacity:
                    log_list.append(u"[更新内存]%s:容量由%s变更为%s" % (item.slot, item.capacity, new_capacity))
                    item.capacity = new_capacity

                new_sn = client_mem_dict[item.slot]['sn']
                if item.sn != new_sn:
                    log_list.append(u"[更新内存]%s:SN号由%s变更为%s" % (item.slot, item.sn, new_sn))
                    item.sn = new_sn

                new_speed = client_mem_dict[item.slot]['speed']
                if item.speed != new_speed:
                    log_list.append(u"[更新内存]%s:速度由%s变更为%s" % (item.slot, item.speed, new_speed))
                    item.speed = new_speed

                item.save()
                if log_list:
                    models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj,
                                                      content=';'.join(log_list))


# ############# 操作硬盘信息 #############
# 操作硬盘，并记录操作日志
# 添加硬盘
# 删除硬盘
# 更新硬盘信息
class HandleDisk(object):
    '''
        "disk": {
        "status": True, "message": "null",
        "data": {"0": {"slot": "0", "pd_type": "SAS", "capacity": "279.396",
                       "model": "SEAGATE ST300MM0006     LS08S0K2B5NV"},
                 "1": {"slot": "1", "pd_type": "SAS", "capacity": "279.396",
                       "model": "SEAGATE ST300MM0006     LS08S0K2B5AH"},
                 "2": {"slot": "2", "pd_type": "SATA", "capacity": "476.939",
                       "model": "S1SZNSAFA01085L     Samsung SSD 850 PRO 512GB               EXM01B6Q"},
                 "3": {"slot": "3", "pd_type": "SATA", "capacity": "476.939",
                       "model": "S1AXNSAF912433K     Samsung SSD 840 PRO Series              DXM06B0Q"},
                 "4": {"slot": "4", "pd_type": "SATA", "capacity": "476.939",
                       "model": "S1AXNSAF303909M     Samsung SSD 840 PRO Series              DXM05B0Q"},
                 "5": {"slot": "5", "pd_type": "SATA", "capacity": "476.939",
                       "model": "S1AXNSAFB00549A     Samsung SSD 840 PRO Series              DXM06B0Q"}},
        "error": "null"
    },
    '''
    @staticmethod
    def process(server_obj, server_info, user_obj):
        response = BaseResponse()
        try:
            disk_info = server_info['disk']
            if not disk_info['status']:
                response.status = False
                models.ErrorLog.objects.create(asset_obj=server_obj.asset, title='disk-agent',
                                               content=disk_info['error'])
                return response

            client_disk_dict = disk_info['data']

            disk_obj_list = models.Disk.objects.filter(server_obj=server_obj)

            disk_slots = map(lambda x: x, (item.slot for item in disk_obj_list))

            update_list = agorithm.get_intersection(set(client_disk_dict.keys()), set(disk_slots))
            add_list = agorithm.get_exclude(client_disk_dict.keys(), update_list)
            del_list = agorithm.get_exclude(disk_slots, update_list)

            HandleDisk._add_disk(add_list, client_disk_dict, server_obj, user_obj)
            HandleDisk._update_disk(update_list, disk_obj_list, client_disk_dict, server_obj, user_obj)
            HandleDisk._del_disk(del_list, disk_obj_list, server_obj, user_obj)

        except Exception as e:
            response.status = False
            models.ErrorLog.objects.create(asset_obj=server_obj.asset, title='disk-run', content=traceback.format_exc())
        return response

    @staticmethod
    def _add_disk(add_list, client_disk_dict, server_obj, user_obj):
        for item in add_list:
            cur_disk_dict = client_disk_dict[item]
            log_str = '[新增硬盘]插槽为{slot};容量为{capacity};硬盘类型为{pd_type};型号为{model}'.format(**cur_disk_dict)
            cur_disk_dict['server_obj'] = server_obj
            models.Disk.objects.create(**cur_disk_dict)
            models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _del_disk(del_list, disk_objs, server_obj, user_obj):
        for item in disk_objs:
            if item.slot in del_list:
                log_str = '[移除硬盘]插槽为{slot};容量为{capacity};硬盘类型为{pd_type};型号为{model}'.format(**item.__dict__)
                item.delete()
                models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj, content=log_str)


    @staticmethod
    def _update_disk(update_list, disk_objs, client_disk_dict, server_obj, user_obj):
        for item in disk_objs:
            if item.slot in update_list:
                log_list = []

                new_model = client_disk_dict[item.slot]['model']
                if item.model != new_model:
                    log_list.append(u"[更新硬盘]插槽为%s:型号由%s变更为%s" % (item.slot, item.model, new_model))
                    item.model = new_model

                new_capacity = client_disk_dict[item.slot]['capacity']
                new_capacity = float(new_capacity)
                if item.capacity != new_capacity:
                    log_list.append(u"[更新硬盘]插槽为%s:容量由%s变更为%s" % (item.slot, item.capacity, new_capacity))
                    item.capacity = new_capacity

                new_pd_type = client_disk_dict[item.slot]['pd_type']
                if item.pd_type != new_pd_type:
                    log_list.append(u"[更新硬盘]插槽为%s:硬盘类型由%s变更为%s" % (item.slot, item.pd_type, new_pd_type))
                    item.pd_type = new_pd_type

                item.save()
                if log_list:
                    models.AssetRecord.objects.create(asset_obj=server_obj.asset, creator=user_obj,
                                                      content=';'.join(log_list))
