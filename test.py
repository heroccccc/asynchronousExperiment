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

        self.count=0
        self.next = 0

        numList = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        self.keyDic = {Qt.Key_Q:1, Qt.Key_W:2}

        li = [2, 4, 6]

        if self.count == 0 and li[self.count] == 2:
            print("aaaa")


    def keyPressEvent(self, event):
    # エスケープキーを押すと画面が閉じる
        global change

        if event.key() == Qt.Key_Escape:
            self.stop_thread.set()
            self.close()

        elif event.key() == Qt.Key_Control:
            pass

        elif event.key() in self.keyDic.keys():
            change = self.keyDic[event.key()]
            print("change:" + str(change))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = Window()
    player.show()

    sys.exit(app.exec_())
