#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from detect_ir import *
from receive_gun_cmd import receive_gun_cmd
from event_engine import *
from cmd_enum import cmd_enum
import Queue
import time

# 定义事件驱动引擎
class detect_ir_gun(event_engine):
    pass

def simpletest(evt):
    print(evt.dict["instance"])
    inst = evt.dict["instance"]
    inst.send_cmd(inst.wrap_gun_cmd("p", cmd_enum.cmd_respone.value))

def main():
    # 实例一个事件驱动引擎
    dig = detect_ir_gun()
    dig.start()
    dig.register(EVENT_SHOOT, simpletest)
    dig.register(EVENT_CONFIRM, simpletest)
    dig.register(EVENT_ADJUST, simpletest)
    # 实例一个接收gun cmd的类
    rgc = receive_gun_cmd(0.1, dig)
    rgc.start()
    # di = detect_ir()
    # di.get_coordinate()
    # di.start_get_pic()
    # time.sleep(100)
    str = raw_input("Enter any key, will end: ");
    rgc.stop()
    # di.stop_get_pic()

if __name__ == "__main__":
    print("Main gogogo!!!")
    main()
