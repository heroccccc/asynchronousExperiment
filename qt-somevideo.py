# -*- coding:utf-8 -*-
from PyQt5.QtCore import QDir, Qt, QUrl, QTimer
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
from PyQt5.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QSlider, QStyle, QVBoxLayout, QWidget)
from PyQt5.QtWidgets import QMainWindow,QWidget, QPushButton, QAction
from PyQt5.QtGui import QIcon, QImage, QPixmap

import queue
import threading
import cv2
import sys
import numpy
import time
import pyaudio
import wave
import time

class PlayAudio(threading.Thread):

    def __init__(self,i,stop_event):
        threading.Thread.__init__(self)
        self.num = i
        self.stop_event = stop_event

    def run(self):

        self.loadAudio()

        data = self.wr.readframes(self.CHUNK)

        starttime = time.time()

        while data != b'':
            if self.stop_event.is_set():
                break

            self.stream.write(data)          # ストリームへの書き込み(バイナリ)
            data = self.wr.readframes(self.CHUNK) # ファイルから1024個*2個

        self.stream.stop_stream()
        self.stream.close()
        self.wr.close()
        self.p.terminate()

    def loadAudio(self):

        self.CHUNK = 1024

        FILENAME ="video/" + str(self.num) + ".wav"

        self.wr = wave.open(FILENAME,"rb")

        self.p = pyaudio.PyAudio()

        self.stream = self.p.open(format=self.p.get_format_from_width(self.wr.getsampwidth()),
                        channels=self.wr.getnchannels(),
                        rate=self.wr.getframerate(),
                        output=True)


class LoadVideo(threading.Thread):

    def __init__(self, queue, stop_event):
        threading.Thread.__init__(self)
        self.frameQueue = queue
        self.stop_event = stop_event

    def run(self):

        global change
        ptr = 0
        self.video_list = []
        self.cap_list = []
        global framecount_list
        framecount_list = []
        self.framerate_list = []
        for i in range(1,4):
            name = "video/" + str(i) + ".mp4"
            self.video_list.append(name)
            self.cap_list.append(cv2.VideoCapture(self.video_list[i-1]))
            framecount_list.append(int(self.cap_list[i-1].get(7)))
            self.framerate_list.append(int(self.cap_list[i-1].get(5)))
            #http://takeshid.hatenadiary.jp/entry/2016/01/10/153503
            #フレーム数を取得
            #フレームレート(1フレームの時間単位はミリ秒)の取得

        while not self.stop_event.is_set():

            for i in range(framecount_list[0]):

                while self.frameQueue.qsize() > 150:
                    if self.stop_event.is_set() or change == 1:
                        print("video break")
                        break
                    time.sleep(0.3)

                is_read, frame = self.cap_list[0].read()

                self.frameQueue.put(frame)

            self.cap_list[0].release()
            self.cap_list[0] = cv2.VideoCapture(self.video_list[0])
            print("1:finish")

            if change == 1:
                ptr = change
                change = 0
                for i in range(framecount_list[ptr]):

                    while self.frameQueue.qsize() > 150:
                        if self.stop_event.is_set():
                            break
                        time.sleep(0.3)

                    is_read, frame = self.cap_list[ptr].read()
                            #フレームレートのミリ秒数待つ
                    self.frameQueue.put(frame)

                self.cap_list[ptr].release()
                self.cap_list[ptr] = cv2.VideoCapture(self.video_list[ptr])
                print( str(ptr+1) + ":finish")


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.frameQueue = queue.Queue()
        self.imageLabel = QLabel()

        btn = QPushButton("play", self)

        layout = QVBoxLayout()
        layout.addWidget(self.imageLabel)
        layout.addWidget(btn)

        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)

        btn.clicked.connect(self.createVideoLoader)

        self.count=0
        global change
        change = 0
        self.next = 0

        self.qTimer = QTimer(self)
        self.qTimer.setTimerType(Qt.PreciseTimer)
        self.qTimer.timeout.connect(self.showImage)
        self.qTimer.start(33)

    def createVideoLoader(self):

        self.stop_thread = threading.Event()
        th = LoadVideo(self.frameQueue, self.stop_thread)
        th.start()
        self.starttime = time.time()

        tha = PlayAudio(1, self.stop_thread)
        tha.start()

    def showImage(self):

        if change == 1:
            self.next = 1
            while not self.frameQueue.empty():
                self.frameQueue.get()
        elif change == 2:
            self.next = 2
            while not self.frameQueue.empty():
                self.frameQueue.get()


        if not self.frameQueue.empty():

            if self.count >= framecount_list[0] and self.next == 0:
                tha = PlayAudio(1, self.stop_thread)
                tha.start()
                self.count=0

            elif self.count == framecount_list[1] and self.next == 1:
                self.count = 0

            elif self.count == framecount_list[2] and self.next == 2:
                self.count = 0

            if self.next == 1:
                tha = PlayAudio(2, self.stop_thread)
                tha.start()
                self.next = 0

            elif self.next == 2:
                tha = PlayAudio(3, self.stop_thread)
                tha.start()
                self.next = 0


            self.image = self.frameQueue.get()

            self.count+=1

            height, width, channel = self.image.shape
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.imageLabel.setPixmap(QPixmap.fromImage(QImage(self.image, width, height, QImage.Format_RGB888)))
        else:
            print("Nothing")


    def keyPressEvent(self, event):
    # エスケープキーを押すと画面が閉じる
        global change

        if event.key() == Qt.Key_Escape:
            self.stop_thread.set()
            self.close()

        elif event.key() == Qt.Key_Control:
            pass


        elif event.key() == Qt.Key_Q:
            change = 1
            print("change:" + str(change))

        elif event.key() == Qt.Key_W:
            change = 2
            print("change:" + str(change))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = Window()
    player.resize(1200, 760)
    player.show()

    sys.exit(app.exec_())
