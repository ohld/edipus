import os
import sys, cv2 as cv
import openface
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC
from multiprocessing import Process
import numpy as np
import shutil
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QImage, QPixmap, QFileDialog

fileDir = os.path.dirname(os.path.realpath(__file__))

modelDir = os.path.join(fileDir, 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
align = openface.AlignDlib(os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))
networkModel = os.path.join(openfaceModelDir, 'nn4.small2.v1.t7')
net = openface.TorchNeuralNet(networkModel)



class Calculate_thread(QtCore.QThread):
    def __init__(self, parent = None, caller = None):
        QtCore.QThread.__init__(self, parent)
        self.caller = caller
        #==flags============================
        self.teach         = False
        self.learned       = False
        self.isnewlearning = False
        #===================================
        self.Faces      = []
        self.user_list  = []
        self.teach_list = []

        self.chosen = ""
        self.svm = None
        self.frequency = 1
        self.learningdepth = 0
        self.curlearning = 0
        self.aligned_size = 96
        self.landmark_i = ""
        self.name = "none"
        self.pars_landmarks()

        self.connect(self.caller.pushButton, QtCore.SIGNAL("clicked()"), self.add_user_list)
        self.connect(self.caller.pushButton_2, QtCore.SIGNAL("clicked()"), self.on_learning)
        self.caller.comboBox_4.currentIndexChanged.connect(self.pars_landmarks)

    def pars_landmarks(self):
        if (self.caller.comboBox_4.currentText() == "inner eyes and bottom lip"):
            self.landmark_i =  openface.AlignDlib.INNER_EYES_AND_BOTTOM_LIP
        if (self.caller.comboBox_4.currentText() == "outer eyes and nose"):
            self.landmark_i =  openface.AlignDlib.OUTER_EYES_AND_NOSE

    def add_user_list(self):
        self.user_list.append(self.caller.lineEdit.text())

    def on_learning(self):
        self.chosen = self.caller.comboBox.currentText()
        self.teach = True
        self.depth_learning()
        self.curlearning = 0
        self.image = None
        self.emit(QtCore.SIGNAL("start_learning"))
        self.emit(QtCore.SIGNAL("loader"), self.curlearning*100/self.learningdepth)


    def depth_learning(self):
        if   (self.caller.comboBox_5.currentText() == "Mininum learning ~ 15 photos"):
            self.learningdepth = 15
        elif (self.caller.comboBox_5.currentText() == "Medium learning  ~ 30 photos"):
            self.learningdepth = 30
        elif (self.caller.comboBox_5.currentText() == "Deep learning ~ 70 photos"):
            self.learningdepth = 70

    def run(self):
        cap = cv.VideoCapture(0)
        file_list = None
        i = 0
        while True:
            ok, img = cap.read()
            if (self.teach == True) and (self.caller.radioButton_2.isChecked() == True):
                if (file_list is None):
                    file_list = os.listdir(self.caller.lineEdit_2.text())
                    self.frequency = 1
                    i = 0
                img = cv.imread(os.path.join(str(self.caller.lineEdit_2.text()), file_list[i]))


            if img != None:
                bb = align.getLargestFaceBoundingBox(img)
                if bb is not None:
                    landmaks_a = align.findLandmarks(img, bb)

            if (self.teach == True):
                self.isnewlearning = True
                if (self.teach_list.count(self.chosen) == 0):
                    self.teach_list.append(self.chosen)
                if (len(self.teach_list) <= 1):
                    self.learned = False
                else:
                    self.learned = True
                if (i % self.frequency == 0):
                    if landmaks_a is not None:
                        self.image = face_aligned(img, bb, self.aligned_size, landmarks = landmaks_a, landmarks_i = self.landmark_i)
                        if self.image is not None:
                            fc = Face(self.image, list.index(self.teach_list, self.chosen))
                            self.Faces.append(fc)
                            self.curlearning+=1
                            self.emit(QtCore.SIGNAL("loader"), self.curlearning*100/self.learningdepth)
                i+=1

                if (self.curlearning == self.learningdepth):
                    self.teach = False
                    self.emit(QtCore.SIGNAL("end_learning"))


                if(self.caller.radioButton_2.isChecked() == True):
                    if (bb is not None):
                        bl = (bb.left(), bb.bottom())
                        tr = (bb.right(), bb.top())
                        cv.rectangle(img, bl, tr, color=(153, 255, 204), thickness=3)
                        for p in self.landmark_i:
                            cv.circle(img, center=landmaks_a[p], radius=3, color=(255, 100, 50), thickness=-1)
                        cv.putText(img, self.name, (bb.left(), bb.top() - 10), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75,
                                   color=(152, 255, 204), thickness=2)

                    image_out = cvimage2qimage(img)
                    self.emit(QtCore.SIGNAL("img_signal"), image_out)

            else:
                if ((self.learned == True) and (self.Faces is not None) and (self.isnewlearning == True)):
                    self.emit(QtCore.SIGNAL("st_learned"))
                    self.svm = trainSVM(self.Faces)
                    self.emit(QtCore.SIGNAL("learned"))
                    self.isnewlearning = False
                if (self.svm is not None):
                    if landmaks_a is not None:
                        self.image = face_aligned(img, bb, self.aligned_size,landmarks = landmaks_a, landmarks_i = self.landmark_i)
                    if (self.image is not None):
                        id = 0
                        rep = net.forward(self.image)
                        id = self.svm.predict(rep)[0]
                        self.emit(QtCore.SIGNAL("person_ident"), self.teach_list[id])
                        self.name = (str)(self.teach_list[id])
                else:
                    if (len(self.user_list) != 0):
                        self.emit(QtCore.SIGNAL("person_ident"), self.user_list[0])
                        self.name = (str)(self.user_list[0])

                if (bb is not None):
                    bl = (bb.left(), bb.bottom())
                    tr = (bb.right(), bb.top())
                    cv.rectangle(img, bl, tr, color=(153, 255, 204), thickness=3)
                    for p in self.landmark_i:
                        cv.circle(img, center = landmaks_a[p], radius=3, color= (255, 100, 50), thickness=-1)
                    cv.putText(img, self.name, (bb.left(), bb.top() - 10), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness = 2)

                image_out = cvimage2qimage(img)
                self.emit(QtCore.SIGNAL("img_signal"), image_out)
            if (i > 100000):
                i = 0


class Face:
    def __init__(self, cv_img, identity):
        self.cv_img = cv_img
        self.identity = identity


def trainSVM(Faces):
    rep = []
    identities = []
    for face in Faces:
        rep.append(net.forward(face.cv_img))
        identities.append(face.identity)
    rep = np.vstack(rep)
    identities = np.array(identities)

    param_grid = [
        {'C': [1, 10, 100, 1000],
         'kernel': ['linear']},
        {'C': [1, 10, 100, 1000],
         'gamma': [0.001, 0.0001],
         'kernel': ['rbf']}
    ]

    svm = GridSearchCV(SVC(C=1), param_grid, cv=5).fit(rep, identities)
    return svm




def face_aligned(img, bb, size, landmarks, landmarks_i = openface.AlignDlib.OUTER_EYES_AND_NOSE):
    if ((img is not None) and (bb is not None)):
        rgbFrame = img
        alignedFace = align.align(size, rgbFrame, bb=bb, landmarks = landmarks, landmarkIndices=landmarks_i)
        if alignedFace is not None:
            return alignedFace

class GuiWindow(QtGui.QMainWindow):
    def __init__(self):
        super(GuiWindow, self).__init__()
        uic.loadUi(os.path.join(fileDir, "newui.ui"), self)
        #self.widget.hide()
        self.mythread = Calculate_thread(caller = self)
        self.mythread.start()
        self.mywidget = LoadingWidget()

        self.radioButton.setChecked(True)
        self.radioButton_2.setChecked(False)
        self.lineEdit_2.setEnabled(False)
        self.toolButton.setEnabled(False)
        self.radioButton_2.toggled.connect(self.radioB2toggled)
        self.radioButton.toggled.connect(self.radioBtoggled)

        self.connect(self.mythread, QtCore.SIGNAL("img_signal"),     self.video_input)
        self.connect(self.mythread, QtCore.SIGNAL("start_learning"), self.start_learning)
        self.connect(self.mythread, QtCore.SIGNAL("loader"),         self.loader)
        self.connect(self.mythread, QtCore.SIGNAL("end_learning"),   self.end_learning)
        self.connect(self.mythread, QtCore.SIGNAL("learned"),        self.learned)
        self.connect(self.mythread, QtCore.SIGNAL("st_learned"),     self.st_learned)
        self.connect(self.pushButton, QtCore.SIGNAL("clicked()"),    self.add_person)
        self.connect(self.toolButton, QtCore.SIGNAL("clicked()"),    self.opendialog)

        self.show()

    def radioB2toggled(self):
        self.lineEdit_2.setEnabled(True)
        self.toolButton.setEnabled(True)

    def radioBtoggled(self):
        self.lineEdit_2.setEnabled(False)
        self.toolButton.setEnabled(False)


    def opendialog(self):
        tmp_str = QFileDialog.getExistingDirectory(self,"open dialog", "/home/ivan/PycharmProjects/face_recog")
        self.lineEdit_2.setText(tmp_str)

    def video_input(self,image):
        self.label_11.setPixmap(QPixmap.fromImage(image))

    def add_person(self):
        if(self.comboBox.findText(self.lineEdit.text()) == -1):
            self.comboBox.addItem(self.lineEdit.text())

    def start_learning(self):
        self.mywidget.label.setText("   Collecting images...   ")
        self.mywidget.progressBar.setValue(0)
        self.mywidget.show()
        self.mywidget.progressBar.show()

    def loader(self, value):
        self.mywidget.progressBar.setValue(value)

    def end_learning(self):
        self.mywidget.progressBar.setValue(100)
        self.mywidget.hide()

    def st_learned(self):
        self.mywidget.progressBar.hide()
        self.mywidget.label.setText("Wait. Network handeling images...")

    def learned(self):
        self.mywidget.label.setText("Network has successfuly learned")
        self.mywidget.hide()


class  LoadingWidget(QtGui.QWidget):
    def __init__(self):
        super(LoadingWidget, self).__init__()
        uic.loadUi(os.path.join(fileDir, "untitled.ui"), self)
        self.setGeometry(450,900, 565, 113)


def cvimage2qimage(img):
    height, width, bytesPerComponent = img.shape
    bytesPerLine = bytesPerComponent * width
    cv.cvtColor(img, cv.COLOR_BGR2RGB, img)
    q_image = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
    q_image = q_image.scaled(491, 481)
    return q_image


if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = GuiWindow()
    app.exec_()



