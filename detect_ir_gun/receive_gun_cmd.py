#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import threading
import time
from RF24 import *
import RPi.GPIO as GPIO
from cmd_enum import cmd_enum
import json
from event_type import *
from event_engine import event

# Setup for connected IRQ pin, GPIO 24 on RPi B+; uncomment to activate
# irq_gpio_pin = RPI_BPLUS_GPIO_J8_18
# irq_gpio_pin = 24

# irq_gpio_pin = None
class receive_gun_cmd(threading.Thread):
    def __init__(self, interval, event_engine):
        threading.Thread.__init__(self)
        self.radio = RF24(22, 0);
        self.pipes = [0xF0F0F0F0E1, 0xF0F0F0F0D2]
        self.millis = lambda: int(round(time.time() * 1000))

        print('Gun,gogogo!!!')
        self.radio.begin()
        self.radio.enableDynamicPayloads()
        self.radio.setRetries(5,15)
        self.radio.printDetails()

        print(' ************ Receive Setup *********** ')
        self.radio.openWritingPipe(self.pipes[1])
        self.radio.openReadingPipe(1, self.pipes[0])
        self.radio.startListening()
        self.thread_is_running = True
        self.interval = interval
        self._event_engine = event_engine
        self.gun_cmd_ID = 0
        self._value_lock = threading.Lock()

    def send_cmd(self, gun_cmd):
        with self._value_lock:
            # 发送gun_cmd，参数gun_cmd是一个dict
            # First, stop listening so we can talk
            self.radio.stopListening()

            # Send the final one back.
            response_payload = json.dumps(gun_cmd, separators=(',',':')).encode('utf-8')
            self.radio.write(response_payload)
            print('Sent response: {}'.format(response_payload))

            # Now, resume listening so we catch the next packets.
            self.radio.startListening()

    def wrap_gun_cmd(self, gun_name, cmd):
        tmp_gun_cmd = {"cmd": cmd, "ID": self.gun_cmd_ID, "gun": gun_name}
        return tmp_gun_cmd

    def run(self):
        while self.thread_is_running:
            if self.radio.available():
                len = self.radio.getDynamicPayloadSize()
                receive_payload = self.radio.read(len)
                receive_data = json.loads(receive_payload.decode('utf-8'))
                cmd_x = receive_data["cmd"]
                self.gun_cmd_ID = receive_data["ID"]
                print("cmd_x = {}".format(cmd_x))
                # print(type(receive_payload))
                # if ((receive_payload[0] == 0) and (receive_payload[1] == 255) and (receive_payload[2] == 255)):
                    # print("Got start code!")
                    # continue
                # if ((receive_payload[0] == 255) and (receive_payload[1] == 255) and (receive_payload[2] == 0)):
                    # print("Got end code!")
                    # continue
                # print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))
                # receive_data["cmd"] = cmd_enum.cmd_respone.value
                # self.send_cmd(receive_data)
                # 发送射击事件
                if cmd_x == cmd_enum.cmd_shoot.value:
                    evt = event(EVENT_SHOOT)
                    evt.dict["instance"] = self
                elif cmd_x == cmd_enum.cmd_confirm.value:
                    evt = event(EVENT_CONFIRM)
                    evt.dict["instance"] = self
                elif cmd_x == cmd_enum.cmd_adjust.value:
                    evt = event(EVENT_ADJUST)
                    evt.dict["instance"] = self
                self._event_engine.sent_event(evt)
                # self.send_cmd(self.wrap_gun_cmd("p", cmd_enum.cmd_respone.value))
            time.sleep(self.interval)

    def stop(self):
        self.thread_is_running = False