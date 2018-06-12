#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import threading
import time
from RF24 import *
import RPi.GPIO as GPIO

# Setup for connected IRQ pin, GPIO 24 on RPi B+; uncomment to activate
# irq_gpio_pin = RPI_BPLUS_GPIO_J8_18
# irq_gpio_pin = 24

# irq_gpio_pin = None
class receive_gun_cmd(threading.Thread):
    def __init__(self, interval):
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

    def run(self):
        while self.thread_is_running:
            if self.radio.available():
                len = self.radio.getDynamicPayloadSize()
                receive_payload = self.radio.read(len)
                # print(type(receive_payload))
                # if ((receive_payload[0] == 0) and (receive_payload[1] == 255) and (receive_payload[2] == 255)):
                    # print("Got start code!")
                    # continue
                # if ((receive_payload[0] == 255) and (receive_payload[1] == 255) and (receive_payload[2] == 0)):
                    # print("Got end code!")
                    # continue
                print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))
                # First, stop listening so we can talk
                self.radio.stopListening()

                # Send the final one back.
                self.radio.write(receive_payload)
                print('Sent response.')

                # Now, resume listening so we catch the next packets.
                self.radio.startListening()
            time.sleep(self.interval)

    def stop(self):
        self.thread_is_running = False