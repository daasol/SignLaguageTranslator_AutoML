import os
import cv2
import sys
import numpy as np
import urllib.request
import json
import argparse

from PIL import ImageFont, Image, ImageDraw
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtGui

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import pyqtSlot

total_trans_array = []
is_stop = True
show_cnt = 1


def predict(
        project_id, compute_region, model_id, file_path, score_threshold=""
):
    from google.cloud import automl_v1beta1 as automl

    automl_client = automl.AutoMlClient()

    model_full_id = automl_client.model_path(
        project_id, compute_region, model_id
    )

    prediction_client = automl.PredictionServiceClient()

    with open(file_path, "rb") as image_file:
        content = image_file.read()
    payload = {"image": {"image_bytes": content}}

    params = {}
    if score_threshold:
        params = {"score_threshold": score_threshold}

    response = prediction_client.predict(model_full_id, payload, params)
    print("Prediction results:")

    if len(response.payload) == 0:
        return ""

    else:
        for result in response.payload:
            print("Predicted class name: {}".format(result.display_name))
            print("Predicted class score: {}".format(result.classification.score))
        return result.display_name



# 영상을 출력, 저장, 변환, 추론하는 핵심 class
class ShowVideo(QtCore.QObject):
    num = 1  # 이미지의 개수를 파악하기 위한 변수
    flag = 0
    is_run = True  # 수화번역을 시작했는지 파악하기 위한 변수

    camera = cv2.VideoCapture(0)  # USB로 연결된 카메라를 변수에 저장
    # camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    # camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

    text = ""  # 타이머를 표시하기 위한 변수
    is_trans = False  # 추론 및 번역이 끝났는지를 확인하기 위한 변수
    trans_text = ""  # 번역된 텍스트를 받아오기 위한 변수

    ret, image = camera.read()  # 카메라로 부터 입력을 받아와 이미지로 저장
    height, width = image.shape[:2]  # 이미지의 가로, 세로 값을 저장
    VideoSignal1 = QtCore.pyqtSignal(QtGui.QImage)  # QImage 객체를 전달 할 Signal 생성



    def __init__(self, parent=None):  # ShowVideo 객체 초기화 함수
        super(ShowVideo, self).__init__(parent)



    @QtCore.pyqtSlot()  # PyQt 내에서 사용할 함수 선언
    def startVideo(self):  # 영상을 출력하는 함수 (어플리케이션 실행과 동시에 시작됨)
        global image  # 출력할 이미지 변수
        global text  # 타이머 변수
        global color_swapped_image  # 화면에 출력하기 위한 이미지
        global is_trans  # 추론 및 번역이 끝났는지를 확인하기 위한 변수
        global trans_text  # 번역된 텍스트를 받아오기 위한 변수
        global is_stop

        is_trans = False  # 초기값 설정
        text = ""

        while True:
            ret, image = self.camera.read()  # 카메라로 부터 입력을 받아와 이미지로 저장
            color_swapped_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # 화면에 출력하기 위하여 BGR 패턴의 이미지를 RGB 패턴으로 변환

            if is_trans:  # 번역이 완료됐다면
                font = ImageFont.truetype("C:\\Windows\\Fonts\\NanumSquareB.ttf", 32)
                img_pil = Image.fromarray(color_swapped_image)  # color_swapped_image에
                draw = ImageDraw.Draw(img_pil)  # draw를 한다.
                draw.text((20, 430), trans_text, font=font,
                          fill=(255, 255, 255, 0))  # 50, 400의 위치에 trans_text(번역된 텍스트)를 빨간색으로 뿌려준다.
                color_swapped_image = np.array(img_pil)  # 글씨가 그려진 이미지를 다시 기존 이미지에 저장

            qt_image1 = QtGui.QImage(color_swapped_image.data,  # 전달할 QImage 객체를 생성
                                     self.width,
                                     self.height,
                                     color_swapped_image.strides[0],
                                     QtGui.QImage.Format_RGB888)
            self.VideoSignal1.emit(qt_image1)  # 기존에 만들었던 시그널을 통해 QImage 객체를 전송.

            loop = QtCore.QEventLoop()  # 1ms 마다 반복
            QtCore.QTimer.singleShot(1, loop.quit)  # 25 ms
            loop.exec_()

    @QtCore.pyqtSlot()
    def save(self):  # 수화 촬영을 시작하는 함수

        global image  # 출력할 이미지 변수
        global is_run  # 수화번역을 시작했는지 파악하기 위한 변수
        global num  # 이미지의 개수를 파악하기 위한 변수
        global text  # 타이머를 표시하기 위한 변수
        global is_trans  # 추론 및 번역이 끝났는지를 확인하기 위한 변수

        # is_trans = False  # 수화 촬영 중이기 때문에 번역 중인 변수를 False로 초기화
        #버튼 회색

        #push_button1.setEnabled(False)
        icon1_on = icon1 = QtGui.QIcon()
        icon1_on.addPixmap(QtGui.QPixmap("icon/cut-on2.png"), QtGui.QIcon.Selected, QtGui.QIcon.On)
        push_button1.setIcon(icon1_on)
        push_button1.setToolTip('촬영중입니다.')

        is_run = True  # 수화 촬영변수를 True로 변경
        num = 1  # 촬영된 이미지 수를 1로 초기화
        # timer = 3 # 타이머를 5초로 초기화

        if not os.path.isdir("image"):  # 초기 이미지를 저장할 image 폴더가 없다면 폴더 생성
            os.mkdir("image")

        while is_run:  # 수화를 촬영하는 동안
            # text = str(timer)  # text에 타이머를 저장
            # timer = timer - 1  # 1초에 한번씩 감소

            # if timer == 0:  # 타이머가 0이 되면
            path = "image/1.jpg"
            cv2.imwrite(path, image)  # image를 저장한다.
            timer = 3  # 사진을 3장 찍고 나면 타이머를 다시 5초로 초기화
            self.Api_trans()

            loop = QtCore.QEventLoop()  # 1초마다 한번씩 반복
            QtCore.QTimer.singleShot(1000, loop.quit)  # 25 ms
            loop.exec_()

    @QtCore.pyqtSlot()
    def Api_trans(self):  # 이미지 추론 및 번역 함수
        global num  # 이미지의 개수를 파악하기 위한 변수
        global is_trans  # 추론 및 번역이 끝났는지를 확인하기 위한 변수
        global trans_text  # 번역된 텍스트를 저장하기 위한 변수
        global is_run
        global total_trans_array

        trans_text = ""

        res_array = []  # 최종적으로 Papago에 전달 할 배열

        client_id = "vIj2xvkAVXo8ArNz48NH"  # 개발자센터에서 발급받은 Client ID 값
        client_secret = "xZAQ6OTeHy"  # 개발자센터에서 발급받은 Client Secret 값

        # 요청할 주소
        url = "https://openapi.naver.com/v1/papago/n2mt"

        # 이미지 평가 코드
        m_parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        project_id = "synthetic-diode-255613"
        compute_region = "us-central1"
        model_id = "ICN6793930726539526144"
        score_threshold = "0.85"

        args = m_parser.parse_args()

        img_path = "./image/1.jpg"

        result = predict(
            project_id,
            compute_region,
            model_id,
            img_path,
            score_threshold,
        )

        if result == "question":
            result = "?"
        elif result == "":
            return
        elif result == "cant":
            result = "can't"
        elif result == "cancle":
            result = "cancel"
        else:
            result = result.replace("_", " ")

        res_array.append(result)
        if result != "stop" and result != "cancel":
            if result not in total_trans_array:
                total_trans_array.append(result)

        print(res_array)
        if not res_array:  # res_array가 비었다면 오류메시지 출력
            print("인식된 동작이 없습니다.")
            self.reset()
        else:
            if result == "stop":
                if len(total_trans_array) > 0:
                    text = " ".join(total_trans_array)
                    total_trans_array.clear()
                    push_button1.setEnabled(True)
                    is_run = False
                else:
                    text = "please shoot the motion picture."
                    push_button1.setEnabled(True)
                    is_run = False
            elif result == "cancel":
                text = "Action is initialized."
                total_trans_array.clear()
            else:
                text = " ".join(res_array)  # 배열로 된 결과를 String으로 변경

            encText = urllib.parse.quote(text)  # 한글 텍스트를 퍼센트 인코딩
            srcLang = 'en'  # 원본 언어
            tarLang = 'ko'  # 번역을 요청할 언어
            rq_data = "honorific=true&" + "source={}&target={}&text=".format(srcLang,
                                                                             tarLang) + encText  # 번역을 요청할 data 생성
            # 웹 요청
            request = urllib.request.Request(url)  # 번역을 요청할 request 생성
            request.add_header("X-Naver-Client-Id", client_id)  # ID, 비밀번호를 header값에 저장
            request.add_header("X-Naver-Client-Secret", client_secret)

            # 결과 받아오는 부분
            response = urllib.request.urlopen(request, data=rq_data.encode("utf-8"))  # 번역 요청 후 json 타입으로 결과를 받아옴

            # 응답 성공적일 때
            rescode = response.getcode()  # request에 대한 결과코드를 저장
            if rescode == 200:  # 성공
                response_body = response.read()  # response를 읽어서
                rs_data = response_body.decode('utf-8')  # decode를 한 뒤
                rs_data = json.loads(rs_data)  # 딕셔너리화
                trans_text = rs_data['message']['result']['translatedText']  # 번역된 텍스트를 변수에 저장
                print("번역된 내용: ", trans_text)
                self.reset()  # 리셋함수 호출
                is_trans = 1  # 번역이 완료됨을 알림
                return trans_text  # 번역 결과를 return
            else:  # 실패
                print("Error Code:" + rescode)  # 실패 시 에러코드 출력

    @QtCore.pyqtSlot()
    def reset(self):
        global num
        for i in range(1, num):
            path = "image/" + str(i) + ".jpg"
            if os.path.isfile(path):
                os.remove(path)

    @QtCore.pyqtSlot()
    def spinBoxChanged(self):
        global show_cnt
        show_cnt = spinBox.value()
        print(show_cnt)

    @QtCore.pyqtSlot()
    def show(self):
        global show_cnt
        scenario = cv2.imread("scenario/" + str(show_cnt) + ".jpg")
        cv2.imshow('Scenario', scenario)


class ImageViewer(QtWidgets.QWidget):  # 카메라로 부터 받은 이미지를 출력하기 위한 class
    def __init__(self, parent=None):  # 초기화 함수
        super(ImageViewer, self).__init__(parent)
        self.image = QtGui.QImage()  # QImage 객체 생성
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)  # 전체 영역을 불투명한 색상으로 칠한다고 선언

    def paintEvent(self, event):  # 이미지를 실제로 그리는 함수
        painter = QtGui.QPainter(self)  # QPainter 객체 선언
        painter.drawImage(0, 0, self.image)  # 0,0 부터 image를 그림
        self.image = QtGui.QImage()  # image를 다 그리면 다시 초기화

    def initUI(self):
        self.setWindowTitle('Test')

    @QtCore.pyqtSlot(QtGui.QImage)
    def setImage(self, image):  # image를 받아와서 사이즈를 변경하는 함수
        if image.isNull():
            print("Viewer Dropped frame!")

        self.image = image
        if image.size() != self.size():
            self.setFixedSize(image.size())
        self.update()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    thread = QtCore.QThread()  # Thread 생성 및 시작
    thread.start()
    vid = ShowVideo()
    vid.moveToThread(thread)  # ShowVideo 객체를 Thread로 이동

    image_viewer1 = ImageViewer()

    vid.VideoSignal1.connect(image_viewer1.setImage)  # ImageViewer의 setImage 함수와 ShowVideo 객체의 VideoSignal1을 연결

    push_button1 = QtWidgets.QPushButton('Start')  # 버튼 생성
    push_button2 = QtWidgets.QPushButton('Stop')
    push_button1.clicked.connect(vid.save)  # 버튼과 함수 연결
    push_button2.clicked.connect(vid.show)

    # 레이아웃 생성 및 버튼 추가
    vertical_layout = QtWidgets.QVBoxLayout()
    horizontal_layout = QtWidgets.QHBoxLayout()
    vertical_layout2 = QtWidgets.QVBoxLayout()
    horizontal_layout.addWidget(image_viewer1)
    vertical_layout.addLayout(horizontal_layout)
    horizontal_layout.addLayout(vertical_layout2)
    vertical_layout2.addWidget(push_button1)
    vertical_layout2.addWidget(push_button2)

    layout_widget = QtWidgets.QWidget()
    layout_widget.setLayout(vertical_layout)
    main_window = QtWidgets.QMainWindow()
    main_window.setCentralWidget(layout_widget)

    main_window.setObjectName("Form")
    main_window.resize(861, 636)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap("icon/main.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)

    main_window.setWindowIcon(icon)
    main_window.setStyleSheet("background-color: rgb(30, 38, 53);")

    push_button1.setGeometry(QtCore.QRect(690, 110, 160, 89))
    push_button1.setText("")
    icon1 = QtGui.QIcon()
    icon1.addPixmap(QtGui.QPixmap("icon/cut-start.png"), QtGui.QIcon.Selected, QtGui.QIcon.Off)
    push_button1.setIcon(icon1)
    push_button1.setToolTip('시작합니다.')
    push_button1.setIconSize(QtCore.QSize(160, 89))
    push_button1.setObjectName("pushButton")
    push_button1.setStyleSheet("border:0px solid #ffffff")


    push_button2.setGeometry(QtCore.QRect(690, 390, 131, 141))
    push_button2.setText("")
    icon2 = QtGui.QIcon()

    icon2.addPixmap(QtGui.QPixmap("icon/stop.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
    push_button2.setIcon(icon2)
    push_button2.setIconSize(QtCore.QSize(160, 160))
    push_button2.setObjectName("pushButton_2")
    push_button2.setToolTip('종료합니다.')
    push_button2.setStyleSheet("border:0px solid #ffffff")


    spinBox = QtWidgets.QSpinBox(main_window)
    spinBox.setGeometry(QtCore.QRect(710, 510, 91, 41))
    spinBox.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
    spinBox.setMouseTracking(False)
    spinBox.setAlignment(QtCore.Qt.AlignCenter)
    spinBox.setButtonSymbols(QtWidgets.QAbstractSpinBox.UpDownArrows)
    spinBox.setMinimum(1)
    spinBox.setMaximum(8)
    spinBox.setObjectName("spinBox")
    spinBox.valueChanged.connect(vid.spinBoxChanged)

    _translate = QtCore.QCoreApplication.translate
    main_window.setWindowTitle(_translate("Form", " SignLanguage Translator"))
    main_window.show()
    vid.startVideo()

    sys.exit(app.exec_())