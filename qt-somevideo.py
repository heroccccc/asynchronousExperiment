# -*- coding:utf-8 -*-
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget, QLabel, QMainWindow,QWidget, QPushButton, QAction
from PyQt5.QtGui import QImage, QPixmap

import queue
import threading
import cv2
import sys
import numpy
import time
import pyaudio
import wave

#指定されたビデオの音声を再生
class PlayAudio(threading.Thread):

    global change


    def __init__(self,i,stop_event):
        threading.Thread.__init__(self)
        self.num = i
        self.stop_event = stop_event

    def run(self):

        self.loadAudio()

        data = self.wr.readframes(self.CHUNK)

        while data != b'':
            #最初の基本ビデオの音声が終了した時、基本ビデオの音声も終了させる
            if change > 0:
                break

            if self.stop_event.is_set():
                break


            self.stream.write(data)
            data = self.wr.readframes(self.CHUNK)

        self.stream.stop_stream()
        self.stream.close()
        self.wr.close()
        self.p.terminate()

    def loadAudio(self):

        self.CHUNK = 1024
        #ファイル名を変更してください(これは、1.wavなど)
        FILENAME = "video/" + str(self.num) + ".wav"

        self.wr = wave.open(FILENAME,"rb")

        self.p = pyaudio.PyAudio()

        self.stream = self.p.open(format=self.p.get_format_from_width(self.wr.getsampwidth()),
                        channels=self.wr.getnchannels(),
                        rate=self.wr.getframerate(),
                        output=True)

#ビデオの読み込み
class LoadVideo(threading.Thread):

    def __init__(self, queue, stop_event):
        threading.Thread.__init__(self)
        self.frameQueue = queue
        self.stop_event = stop_event

    def run(self):
        #切り替わった後のビデオのindex番号変数
        global change
        #nextと同じ意味の変数、ビデオのindex番号を保持する変数
        ptr = 0

        #読みこむビデオのための用意する変数
        #表示させるビデオのリスト
        self.video_list = []
        self.cap_list = []
        #表示させるビデオのフレームの合計値のリスト
        global framecount_list
        framecount_list = []

        #ここで表示させるビデオを全て変数として準備する、今回は3つのビデオなのでrange(1,4)にした
        for i in range(1,4):
            #ファイル名を変更してください(これは、1.mp4など)
            name = "video/" + str(i) + ".mp4"
            self.video_list.append(name)
            self.cap_list.append(cv2.VideoCapture(self.video_list[i-1]))
            framecount_list.append(int(self.cap_list[i-1].get(7)))

        #ストップされるまで
        while not self.stop_event.is_set():
            #最初に再生されるビデオの読み込み
            for i in range(framecount_list[0]):

                #2秒分キューに入れる buffer
                #こうすることで、メモリの圧迫を解決できる
                while self.frameQueue.qsize() > 60:
                    if self.stop_event.is_set():
                        break
                    #300msまつ,この間にキューの中身を消費する
                    time.sleep(0.3)

                #最初の基本ビデオが再生されていた時に、ビデオの切り替えが行われた時
                if change > 0:
                    print("main video break")
                    break

                #キューに最初の基本のビデオのフレームを読み込み、入れる
                is_read, frame = self.cap_list[0].read()
                self.frameQueue.put(frame)

            #普通に終了した場合 or 切り替えで終了した場合、最初のビデオを準備する
            self.cap_list[0].release()
            self.cap_list[0] = cv2.VideoCapture(self.video_list[0])

            #最初の基本ビデオが再生されていた時に、ビデオの切り替えが行われた時
            if change > 0:
                #切り替わるビデオのindex番号を保持
                ptr = change
                change = 0

                print( str(ptr+1) + ":start")
                #切り替わるビデオの読み込み
                for i in range(framecount_list[ptr]):

                    #2秒分キューに入れる buffer
                    #こうすることで、メモリの圧迫を解決できる
                    while self.frameQueue.qsize() > 60:
                        if self.stop_event.is_set():
                            break
                        time.sleep(0.3)

                    #ビデオの読み込み
                    is_read, frame = self.cap_list[ptr].read()
                    self.frameQueue.put(frame)

                #終了した時、次の切り替わりのため、そのビデオの準備する
                self.cap_list[ptr].release()
                self.cap_list[ptr] = cv2.VideoCapture(self.video_list[ptr])
                print( str(ptr+1) + ":finish")


class Window(QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.frameQueue = queue.Queue()
        self.imageLabel = QLabel()

        btn = QPushButton("play", self)
        btn2 = QPushButton("end", self)

        layout = QVBoxLayout()
        layout.addWidget(self.imageLabel)
        layout.addWidget(btn)
        layout.addWidget(btn2)

        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)

        #playボタンを押されたら
        btn.clicked.connect(self.createVideoLoader)
        btn2.clicked.connect(self.endApp)

        #表示される動画のフレーム数をカウント変数
        self.count=0

        #ビデオが変更された後の、そのビデオのindex番号をその切り替えられたビデオのindex番号を保持する変数
        self.next = 0

        #ビデオの切り替えが行われた時に、その切り買われた後のビデオのindex番号を入れる変数
        global change
        change = 0

        #ビデオを切り替える際に、音声も切り替えるための変数
        self.changeSound = 0

        #キー操作で動画の切り替えを行うための、キーリスト(切り替わるビデオを3つ用意)
        self.keyList = [Qt.Key_1,Qt.Key_2]

        #33msごとにshowimageが呼ばれる(30fpsのビデオから1枚を表示する33msとした)
        self.qTimer = QTimer(self)
        self.qTimer.setTimerType(Qt.PreciseTimer)
        self.qTimer.timeout.connect(self.showImage)
        self.qTimer.start(33)

    #ビデオの読み込み開始関数
    def createVideoLoader(self):
        #33msでshowimageを行い、スレッドでビデオの読み込みを行う、最初の再生するビデオは指定
        self.stop_thread = threading.Event()
        th = LoadVideo(self.frameQueue, self.stop_thread)
        th.start()

        #指定したビデオの音声をスレッドで呼び出し、再生する(pyaudioを使用)
        tha = PlayAudio(1, self.stop_thread)
        tha.start()

    def showImage(self):

        #ビデオが変更された時
        if change > 0:
            self.changeSound = change
            #その時まで入っていたキューを空にする、バッファの中を0にする
            #その時切り替わったビデオのindex番号を保持
            self.next = change
            #キュー、バッファを空にする
            while not self.frameQueue.empty():
                self.frameQueue.get()

        #キュー、バッファを空ではない時
        if not self.frameQueue.empty():

            #表示される動画のフレーム数を計算
            self.count+=1

            #最初に指定したビデオの再生が切り替えを行われずに、ビデオが終了した場合、もう一度基本ビデオを再生する
            if self.count == framecount_list[0] and self.next == 0:
                tha = PlayAudio(1, self.stop_thread)
                tha.start()
                self.count=0


            #切り替わった後のビデオが終了した場合、そのカウントを0にする
            #self.next in [i for i,v in enumerate(framecount_list) if v == self.count]は、切り替わった後のビデオのindex番号と等しいかどうかみている
            #右側をself.next == framecount_list.index(self.count):でもいいが、これだと切り替わるビデオの中に同じフレーム数が存在するとバグが起きてしまう
            elif self.count in framecount_list and self.next in [i for i,v in enumerate(framecount_list) if v == self.count]:
                [i for i,v in enumerate(framecount_list) if v == self.count]
                tha = PlayAudio(1, self.stop_thread)
                tha.start()
                self.count = 0
                self.next = 0

            '''
            キーの切り替わりが行われ、次のビデオが再生される前に、すぐにバッファーにその次のビデオのフレームがキューに保存され、
            その保存されたビデオの音声をnextのビデオindex番号から再生させる
            self.changeSound > 0でビデオが切り替わり、その切り替わった後の音声を一度だけ再生させることができる
            '''
            if self.next > 0 and self.changeSound > 0:
                #音声再生
                tha = PlayAudio(self.next+1, self.stop_thread)
                tha.start()
                self.count=0
                self.changeSound = 0


            #LoadVideoで保存されたフレームを取得し、画面上に表示させる
            self.image = self.frameQueue.get()
            height, width, channel = self.image.shape
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
            self.imageLabel.setPixmap(QPixmap.fromImage(QImage(self.image, width, height, QImage.Format_RGB888)))

    #キー操作関数
    def keyPressEvent(self, event):
        global change

        if event.key() == Qt.Key_Escape:
            # エスケープキーを押すと画面が閉じる
            self.stop_thread.set()
            self.close()

        #押されたキーがキーリストに入っていた場合、ビデオの切り替えを行う
        elif event.key() in self.keyList:
            #ビデオの切り替え
            change = self.keyList.index(event.key())+1
            print("change:" + str(change))

    #×ボタンで終了イベント
    def closeEvent(self,event):

        self.stop_thread.set()

        event.accept()

    #endボタンで終了イベント
    def endApp(self):

        self.stop_thread.set()

        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = Window()

    #ディスプレイの大きさを取得
    screen = app.desktop()
    height = screen.height()
    width = screen.width()

    #スクリーンいっぱいに表示
    #調節してください　
    player.resize(700,600)
    player.show()

    sys.exit(app.exec_())
