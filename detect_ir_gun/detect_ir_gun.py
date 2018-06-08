#!/usr/bin/env python

from __future__ import print_function
import thread
import time
from RF24 import *
import RPi.GPIO as GPIO

irq_gpio_pin = None

radio = RF24(22, 0);


# Setup for connected IRQ pin, GPIO 24 on RPi B+; uncomment to activate
#irq_gpio_pin = RPI_BPLUS_GPIO_J8_18
#irq_gpio_pin = 24

##########################################
def try_read_data(threadName, channel=0):
    # if radio.available():
    # thread_is_running = False
    print("{} is running!!!!".format(threadName))
    while True:
        if radio.available():
            len = radio.getDynamicPayloadSize()
            receive_payload = radio.read(len)
            # print(type(receive_payload))
            # if ((receive_payload[0] == 0) and (receive_payload[1] == 255) and (receive_payload[2] == 255)):
                # print("Got start code!")
                # continue
            # if ((receive_payload[0] == 255) and (receive_payload[1] == 255) and (receive_payload[2] == 0)):
                # print("Got end code!")
                # continue
            print('Got payload size={} value="{}"'.format(len, receive_payload.decode('utf-8')))
            # First, stop listening so we can talk
            radio.stopListening()

            # Send the final one back.
            radio.write(receive_payload)
            print('Sent response.')

            # Now, resume listening so we catch the next packets.
            radio.startListening()

pipes = [0xF0F0F0F0E1, 0xF0F0F0F0D2]
millis = lambda: int(round(time.time() * 1000))

print('Gun,gogogo!!!')
radio.begin()
radio.enableDynamicPayloads()
radio.setRetries(5,15)
radio.printDetails()

print(' ************ Receive Setup *********** ')
radio.openWritingPipe(pipes[1])
radio.openReadingPipe(1,pipes[0])
radio.startListening()

# create thread to receive data
# try:
thread.start_new_thread( try_read_data, ("Thread-jieshou", 0, ) )
# except:
   # print("Error: unable to start thread")

# forever loop
while 1:
    time.sleep(1000)

