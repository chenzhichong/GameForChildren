#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from detect_ir import *
from receive_gun_cmd import receive_gun_cmd
from event_engine import *
from cmd_enum import cmd_enum
import Queue
import time

# L = []

# 定义事件驱动引擎
class detect_ir_gun(event_engine):
    pass

def main():
    def handler_shoot(evt):
        print(evt.dict["instance"])
        inst = evt.dict["instance"]
        print("handle shoot event!")
        inst.send_cmd(inst.wrap_gun_cmd("p", cmd_enum.cmd_respone.value))
        time.sleep(0.05)
        di.get_coordinate(True, L)

    def handler_confirm(evt):
        print(evt.dict["instance"])
        inst = evt.dict["instance"]
        print("handle confirm event!")
        global adjust_count
        print("adjust_count is [{}]".format(adjust_count))
        if (adjust_count < 4):
            inst.send_cmd(inst.wrap_gun_cmd("p", cmd_enum.cmd_respone.value))
            di.stop_send_pic()
        else :
            # 如果4个点ok了就发送一个end cmd，arduino端会停止adjust模式
            inst.send_cmd(inst.wrap_gun_cmd("p", cmd_enum.cmd_end.value))
            di.stop_send_pic()
            return
        # 获取4个点做透视变换
        di.get_coordinate(False)
        L[adjust_count] = di.get_coordinate(False)
        adjust_count += 1
        di.start_send_pic()

    def handler_adjust(evt):
        print(evt.dict["instance"])
        inst = evt.dict["instance"]
        print("handle adjust event!")
        inst.send_cmd(inst.wrap_gun_cmd("p", cmd_enum.cmd_respone.value))
        global adjust_count
        adjust_count = 0
        # del L[:]
        di.start_send_pic()

    # 定义一个全局变量记录校正取样次数
    global adjust_count
    # 定义一个全局列表用于保存变换坐标
    L = [[129,65],[579,90],[109,323],[599,334]]
    # 实例一个事件驱动引擎
    dig = detect_ir_gun()
    dig.start()
    dig.register(EVENT_SHOOT, handler_shoot)
    dig.register(EVENT_CONFIRM, handler_confirm)
    dig.register(EVENT_ADJUST, handler_adjust)
    # 实例一个接收gun cmd的类
    rgc = receive_gun_cmd(0.1, dig)
    rgc.start()
    di = detect_ir()
    # di.get_coordinate()
    # di.start_get_pic()
    # time.sleep(100)
    str = raw_input("Enter any key, will end: ");
    rgc.stop()
    # di.stop_get_pic()

if __name__ == "__main__":
    print("Main gogogo!!!")
    main()
