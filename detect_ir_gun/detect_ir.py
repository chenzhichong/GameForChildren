#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import cv2
import numpy as np
import time
import RPi.GPIO as GPIO

class detect_ir():
    def __init__(self):
        self.capture = cv2.VideoCapture(0)
        # 注意VideoWriter的长宽是int型，需要强制转换一下
        self.width = int(capture.get(3))
        self.height = int(capture.get(4))
        print("cam, width=[{}], height=[{}]".format(width, height))
        # ret, frame = capture.read()
        # cv2.imwrite('cam.png', frame)
        # time.sleep(2)

    def __del__( self ):
        print("Bye!!")
        self.capture.release()

    def get_coordinate():
        # 获取一帧
        start = time.clock()
        ret, frame = self.capture.read()

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

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # cv2.circle(frame, (x, y), 2, (0, 0, 255), -1)
            print("x={0}, y={1}".format(x, y))
            # param.append(dict(x=x, y=y))
            if len(param) < 4:
                param.append([x,y])
            # cv2.imshow('image', frame)