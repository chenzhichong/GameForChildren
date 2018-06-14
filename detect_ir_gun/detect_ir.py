#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import cv2
import numpy as np
import time
import RPi.GPIO as GPIO
import threading
import socket
import struct

class detect_ir():
    def __init__(self):
        self.__capture = cv2.VideoCapture(0)
        if (not self.__capture.isOpened()):
            print("EEROR: Can not open cam!")
            return
        # 注意VideoWriter的长宽是int型，需要强制转换一下
        self.__width = int(self.__capture.get(3))
        self.__height = int(self.__capture.get(4))
        print("cam, width=[{}], height=[{}]".format(self.__width, self.__height))
        self.__send_pic = self.__send_pic(self.__capture)
        self.__send_pic.start()
        # ret, frame = capture.read()
        # cv2.imwrite('cam.png', frame)
        # time.sleep(2)

    def __del__(self):
        print("Bye!!")
        self.__send_pic.stop();
        if self.__capture.isOpened():
            self.__capture.release()

    def get_coordinate(self):
        if not self.__capture.isOpened():
            print("Cam is not opened, or something happen to it.")
            return None
        # 获取一帧
        start = time.clock()
        ret, frame = self.__capture.read()

        # 将这帧转换为灰度图
        elapsed = (time.clock() - start)
        print("Get pic Time used: {}".format(elapsed))
        # 转为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # 阈值操作
        ret_thresh, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        elapsed = (time.clock() - start)
        print("Do threshold Time used: {}".format(elapsed))
        # 进行透视变换
        # pts1 = np.float32(L) #左上，右上，左下，右下
        pts1 = np.float32([[129,65],[579,90],[109,323],[599,334]])
        pts2 = np.float32([[0,0],[1366,0],[0,768],[1366,768]])
        M = cv2.getPerspectiveTransform(pts1,pts2)
        elapsed = (time.clock() - start)
        print("Do getPerspectiveTransform Time used: {}".format(elapsed))
        dst = cv2.warpPerspective(thresh,M,(1366,768))
        elapsed = (time.clock() - start)
        print("Do warpPerspective Time used: {}".format(elapsed))
        # 侵蚀操作，去掉噪点
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(2, 2))
        eroded = cv2.erode(dst,kernel)
        # 膨胀操作，还原目标点
        dilated = cv2.dilate(eroded,kernel)
        cv2.imwrite("dilated.png", dilated)
        # 查找边缘
        contours, hierarchy = cv2.findContours(dilated,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            #计算质心
            cv2.drawContours(dilated,contours,-1,(0,255,0),3)
            c = max(contours, key = cv2.contourArea)
            # ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)
            center = (int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"]))
            print(center)
            return center

        # if cv2.waitKey(1) == ord('q'):
            # break
        elapsed = (time.clock() - start)
        print("Time used: {}".format(elapsed))
        return None

    ''' 内部类，用于发送从cam截取的图片到pc '''
    class __send_pic():
        def __init__(self, capture = None, remote_address = ("10.28.5.76", 7999), interval = 0.1):
            print('Get pic,gogogo!!!')
            self.__interval = interval
            self.__capture = capture
            self.__remote_address = remote_address
            self.__active = False
            self.__thread = threading.Thread(target = self.__run)

        def start(self):
            # 启动线程
            self.__active = True
            self.__thread.start()

        def stop(self):
            # 停止线程
            self.__active = False
            self.__thread.join()

        def __run(self):
            if not self.__capture.isOpened():
                print("Cam is not opened, or something happen to it.")
                return
            try :
                client_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                print("here,will block until connected...")
                # client_socket.connect(('10.28.5.76', 7999))
                client_socket.connect(self.__remote_address)
                print("ok,already connected!!!")
                connection = client_socket.makefile('wb')
            except Exception as e:
                print(e)
                return
            try :
                while self.__active == True and self.__capture.isOpened():
                    #读取图片
                    ret, frame = self.__capture.read()
                    #转换为jpg格式
                    result, imgencode = cv2.imencode('.jpg', frame)
                    img_code = np.array(imgencode)
                    img_str = img_code.tostring()
                    #获得图片长度
                    s = struct.pack('<L', len(img_str))
                    print(len(img_str))
                    #将图片长度传输到服务端
                    connection.write(s)
                    connection.flush()
                    # 传输图片流
                    connection.write(img_str)
                    connection.flush()
                if not self.__active:
                    connection.write(struct.pack('<L', 0))
                    connection.flush()
            except Exception as e:
                print(e)
            finally:
                connection.close()
                client_socket.close()

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)
            print("x={0}, y={1}".format(x, y))
            # param.append(dict(x=x, y=y))
            if len(param) < 4:
                param.append([x,y])
            # cv2.imshow('image', frame)