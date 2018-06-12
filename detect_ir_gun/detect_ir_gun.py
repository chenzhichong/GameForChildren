#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from detect_ir import *
from receive_gun_cmd import receive_gun_cmd
import Queue
import time

if __name__ == "__main__":
    print("Main gogogo!!!")
    rgc = receive_gun_cmd(0.1)
    rgc.start()
    di = detect_ir()
    # di.get_coordinate()
    # di.start_get_pic()
    time.sleep(5)
    rgc.stop()
    # di.stop_get_pic()
