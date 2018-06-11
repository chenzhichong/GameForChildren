#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
from detect_ir import detect_ir
from receive_gun_cmd import receive_gun_cmd
import Queue

if __name__ == "__main__":
    print("Main gogogo!!!")
    rgc = receive_gun_cmd()
    rgc.run()
