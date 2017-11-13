import numpy as np
import cv2
import threading
import pyaudio
import wave
import time

stopTime = 0

class TestThread(threading.Thread):

    def __init__(self,i):
        threading.Thread.__init__(self)
        self.num = i

    def run(self):

        global stopTime

        stopTime = 0

        CHUNK = 1024

        FILENAME = str(self.num) + ".wav"

        wr = wave.open(FILENAME,"rb")

        p = pyaudio.PyAudio()

        stream = p.open(format=p.get_format_from_width(wr.getsampwidth()),
                        channels=wr.getnchannels(),
                        rate=wr.getframerate(),
                        output=True)

        # 1024個読み取り
        data = wr.readframes(CHUNK)

        while data != b'':
            stream.write(data)          # ストリームへの書き込み(バイナリ)
            data = wr.readframes(CHUNK) # ファイルから1024個*2個

            if stopTime == 1:
                time.sleep(1)
                stopTime = 0

        stream.stop_stream()
        stream.close()
        wr.close()

        p.terminate()


def showvideo(ptr):

    global stopTime

    for i in range(framecount_list[ptr-1]):
        is_read, frame = cap_list[ptr-1].read()
                #フレームレートのミリ秒数待つ
        k = cv2.waitKey(framerate_list[ptr-1])&0xff
        if not is_read:
            return 0
        elif k == 27:
            return 1
        elif k == 32:
            stopTime = 1
            time.sleep(1)

        cv2.imshow("player", frame)

    cap_list[ptr-1].release()
    cap_list[ptr-1] = cv2.VideoCapture(video_list[ptr-1])
    print(str(ptr) + ":finish")


if __name__ == '__main__':

    video_list = []
    cap_list = []
    framecount_list = []
    framerate_list = []
    flag = 0
    for i in range(1,9):
        name = str(i) + ".mp4"
        video_list.append(name)
        cap_list.append(cv2.VideoCapture(video_list[i-1]))
        framecount_list.append(int(cap_list[i-1].get(7)))
        framerate_list.append(int(cap_list[i-1].get(5)))
        #http://takeshid.hatenadiary.jp/entry/2016/01/10/153503
        #フレーム数を取得
        #フレームレート(1フレームの時間単位はミリ秒)の取得


    while True:

        for i in range(framecount_list[0]):

            is_read, frame = cap_list[0].read()
                #フレームレートのミリ秒数待つ
            k = cv2.waitKey(framerate_list[0])&0xff

            if k == 97 or k == 113 or k == 119 or k == 100 or k == 99 or k == 122 or not is_read:
                break
            elif k == 27:
                flag = 1
                break

            cv2.imshow("player", frame)

        cap_list[0].release()
        cap_list[0] = cv2.VideoCapture(video_list[0])
        print("1:finish")

        if k == 120:
            #x
            th2 = TestThread(2)
            th2.start()
            flag = showvideo(2)
        elif k == 122:
            #z
            th3 = TestThread(3)
            th3.start()
            flag = showvideo(3)
        elif k == 113:
            #q
            th4 = TestThread(4)
            th4.start()
            flag = showvideo(4)
        elif k == 119:
            #w
            th5 = TestThread(5)
            th5.start()
            flag = showvideo(5)
        elif k == 100:
            #d
            th6 = TestThread(6)
            th6.start()
            flag = showvideo(6)
        elif k == 97:
            #a
            th7 = TestThread(7)
            th7.start()
            flag = showvideo(7)
        elif k == 99:
            #c
            th8 = TestThread(8)
            th8.start()
            flag = showvideo(8)

        if flag == 1:
            break

cv2.destroyAllWindows()


#http://blog.livedoor.jp/aiko_tech/archives/opencv_video.html
