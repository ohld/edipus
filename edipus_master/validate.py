#!/usr/bin/python2
import os
import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QPixmap, QFileDialog
import pickle
import cv2 as cv
import exec_thread
fileDir = os.path.dirname(os.path.realpath(__file__))

os.system("export PATH=/home/ivan/torch/install/bin:$PATH")

PROBABILITY_THRESHOLD = 0.8

fifo1 = "/home/common/edipusisthebest1120161"
fifo2 = "/home/common/edipusisthebest1120162"


def permission_control (check):
    if check is True:
        os.mkfifo(fifo2, get_flags())
        os.mkfifo(fifo1, get_flags())

        fifo_id1 = os.open(fifo1, os.O_WRONLY)
        fifo_id2 = os.open(fifo2, os.O_RDONLY)

        if ((fifo_id1 is not -1) and (fifo_id2 is not -1)):
            buf = os.getenv("USER")
            if (len(buf) is 0):
                return
            else:
                os.write(fifo_id1, buf)
                sym = os.read(fifo_id2, 1)
                os.system("sg secret -c \"subl /home/secret_docs/*\"")
                os.write(fifo_id1, sym)
                os.close(fifo_id1)
                os.close(fifo_id2)


def get_flags():
    i = 0
    flags = 0
    while i < 9:
        flags |= 1 << (8 - i)
        i += 1
    return flags


class Calculate_thread(QtCore.QThread):
    def __init__(self, parent = None, caller = None):
        QtCore.QThread.__init__(self, parent)
        self.caller = caller
        self.Faces = []
        with open(os.path.join(fileDir, "classifier.pkl"), 'r') as f:
            self.lr = pickle.load(f)

        self.aligned_size = 96
        self.image = None
        self.c_permision = 0
        self.c_all = 0
        self.p_control_flag = False
        self.connect(self.caller.pushButton_2, QtCore.SIGNAL("clicked()"), self.checking)

    def checking(self):
        self.c_permision = 0
        self.c_all = 0
        self.p_control_flag = True
        self.emit(QtCore.SIGNAL("p_control"), " Please, look in the camera...", "black")

    def permission_control(self, check):
        if check is True:
            os.mkfifo(fifo2, self.get_flags())
            os.mkfifo(fifo1, self.get_flags())

            fifo_id1 = os.open(fifo1, os.O_WRONLY)
            fifo_id2 = os.open(fifo2, os.O_RDONLY)

            if ((fifo_id1 is not -1) and (fifo_id2 is not -1)):
                buf = os.getenv("USER")
                if (len(buf) is 0):
                    return
                else:
                    os.write(fifo_id1, buf)
                    sym = os.read(fifo_id2, 1)
                    os.system("sg secret -c \"subl /home/secret_docs/*\"")
                    os.write(fifo_id1, sym)
                    os.close(fifo_id1)
                    os.close(fifo_id2)

    def get_flags(self):
        i = 0
        flags = 0
        while i < 9:
            flags |= 1 << (8 - i)
            i += 1
        return flags

    def run(self):
        cap = cv.VideoCapture(0)
        while True:
            ok, img = cap.read()
            if img != None:
                bb = exec_thread.align.getLargestFaceBoundingBox(img, skipMulti=True)
                if bb is not None:
                    landmaks_a = exec_thread.align.findLandmarks(img, bb)
                    if landmaks_a is not None:
                        self.image = exec_thread.face_aligned(img, bb, self.aligned_size, landmarks=landmaks_a, landmarks_i=exec_thread.aligning.AlignDlib.OUTER_EYES_AND_NOSE)

            id = 0
            if (self.image is not None):
                if (self.lr is not None):
                    rep = exec_thread.net.forward(self.image)
                    id = self.lr.predict_proba(rep)[0][1]
                else:
                    id = 0
            if (self.p_control_flag is True):
                self.c_all += 1
                if (id > 0.8):
                    self.c_permision += 1
                if self.c_all is 40:
                    if self.c_permision >= 25:
                        self.emit(QtCore.SIGNAL("p_control"), " ACCESS HAS BEEN GRANTED ", "green")
                        self.permission_control(True)
                        #self.emit(QtCore.SIGNAL("open_d"), "/home/secret_docs")
                    else:
                        self.emit(QtCore.SIGNAL("p_control"), " ACCESS  DENIDED ", "red")
                    self.p_control_flag = False

            if bb is not None:
                bl = (bb.left(), bb.bottom())
                tr = (bb.right(), bb.top())
                cv.rectangle(img, bl, tr, color=(153, 255, 204), thickness=3)

            image_out = exec_thread.cvimage2qimage(img)
            self.emit(QtCore.SIGNAL("img_signal"), image_out)


class PermissionWidget(QtGui.QWidget):
    def __init__(self):
        super(PermissionWidget, self).__init__()
        uic.loadUi(os.path.join(fileDir, "ui_forms/permission.ui"), self)
        self.setGeometry(500, 800, 400, 114)
        self.setWindowTitle("Permission")


class GuiWindow(QtGui.QMainWindow):
    def __init__(self):
        super(GuiWindow, self).__init__()
        uic.loadUi(os.path.join(fileDir, "ui_forms/classif.ui"), self)
        self.setWindowTitle("Edipus validator")
        self.permissionwidget = PermissionWidget()
        self.calc_thread_run()
        self.show()

    def calc_thread_run(self):
        self.mythread = Calculate_thread(caller=self)
        self.mythread.start()
        self.connect(self.mythread,                    QtCore.SIGNAL("img_signal"),  self.video_input)
        self.connect(self.mythread,                    QtCore.SIGNAL("p_control"),   self.permission_control)
        self.connect(self.permissionwidget.pushButton, QtCore.SIGNAL(("clicked()")), self.close_p_c)
        self.connect(self.mythread,                    QtCore.SIGNAL("open_d"),      self.open_d)

    def video_input(self,image):
        self.label.setPixmap(QPixmap.fromImage(image))

    def open_d(self, s):
        QFileDialog.getExistingDirectory(self, "open dialog", s)

    def permission_control(self, message, color):
        palette = QtGui.QPalette()
        self.permissionwidget.label.setText(str(message))
        if (color is "green"):
            palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.green)
            self.permissionwidget.label.setPalette(palette)
        if (color is "red"):
            palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.red)
            self.permissionwidget.label.setPalette(palette)
        if (color is "black"):
            palette.setColor(QtGui.QPalette.Foreground, QtCore.Qt.black)
            self.permissionwidget.label.setPalette(palette)
        self.permissionwidget.pushButton.show()
        self.permissionwidget.show()

    def close_p_c(self):
        self.permissionwidget.hide()



if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = GuiWindow()
    app.exec_()