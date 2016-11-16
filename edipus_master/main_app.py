import urllib2
import os
import openface
import cv2 as cv
import sys
from sklearn.grid_search import GridSearchCV
from sklearn.linear_model import LogisticRegression as LR
import numpy as np
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QImage, QPixmap, QFileDialog
import random
import shutil
import vk_requests
import face

fileDir = os.path.dirname(os.path.realpath(__file__))

IMG_FOLDER_ME = 'me'
IMG_FOLDER_NOTME = 'notme'

modelDir = os.path.join(fileDir, 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
align = openface.AlignDlib(os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))
networkModel = os.path.join(openfaceModelDir, 'nn4.small2.v1.t7')
net = openface.TorchNeuralNet(networkModel)

PROBABILITY_THRESHOLD = 0.8

def cvimage2qimage(img):
    height, width, bytesPerComponent = img.shape
    bytesPerLine = bytesPerComponent * width
    cv.cvtColor(img, cv.COLOR_BGR2RGB, img)
    q_image = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
    q_image = q_image.scaled(491, 481)
    return q_image




class  LoadingWidget(QtGui.QWidget):
    def __init__(self):
        super(LoadingWidget, self).__init__()
        uic.loadUi(os.path.join(fileDir, "loading.ui"), self)
        self.setGeometry(500,800, 565, 113)



class Calculate_thread(QtCore.QThread):
    def __init__(self, parent = None, caller = None):
        QtCore.QThread.__init__(self, parent)
        self.caller = caller
        self.Faces = []
        self.lr = None
        self.aligned_size = 96

        #flags
        self.first_flag   = False
        self.logging_next = False
        self.end_learning = False

        self.learning = 0  # 0 - not learning
                           # 1 - video learning
                           # 2 - photo learning
                           # 3 - social networks

        self.owner= 0
        self.others = 0
        self.iters = 12
        self.name = ""
        self.my_name = "Owner"
        self.image = None
        self.connect(self.caller.pushButton,               QtCore.SIGNAL("clicked()"), self.start_learning)
        self.connect(self.caller.loggingwidget.pushButton, QtCore.SIGNAL("clicked()"), self.logg_next)

    def logg_next(self):
        self.learning = 3
        self.caller.loggingwidget.hide()

    def start_learning(self):
        if (self.caller.radioButton.isChecked()   is True):
            self.learning = 1
        if (self.caller.radioButton_2.isChecked() is True):
            self.learning = 2
        if (self.caller.radioButton_3.isChecked() is True):
            self.caller.loggingwidget.show()


    def save_photos(self,urls, directory):
        if not os.path.exists(directory):
            os.mkdir(directory)
        for num, url in enumerate(urls):
            a = url.split("/")
            b = len(a)
            names_pattern = str(random.randrange(1000, 10001, 1)) + str(a[b - 1])
            filename = os.path.join(directory, names_pattern)
            s = "Downloading " + str(filename)
            self.emit(QtCore.SIGNAL("loading") , True, 0, s)
            #print "Downloading %s" % filename
            open(filename, "w").write(urllib2.urlopen(url).read())

    def vk_learning(self):
        access_token, user_id = vk_requests.get_saved_auth_params()
        if not access_token or not user_id:
            access_token, user_id = vk_requests.get_auth_params()

        if os.path.exists(IMG_FOLDER_NOTME):
            shutil.rmtree(IMG_FOLDER_NOTME)
        if os.path.exists(IMG_FOLDER_ME):
            shutil.rmtree(IMG_FOLDER_ME)

        if IMG_FOLDER_NOTME and not os.path.exists(IMG_FOLDER_NOTME):
            os.makedirs(IMG_FOLDER_NOTME)
        if IMG_FOLDER_ME and not os.path.exists(IMG_FOLDER_ME):
            os.makedirs(IMG_FOLDER_ME)

        num_friends = int(self.caller.loggingwidget.lineEdit_2.text())

        i = 0
        new_user_id = self.caller.loggingwidget.lineEdit.text()
        dictionary = vk_requests.get_me(access_token, new_user_id)
        d = dictionary[0]
        self.my_name = d["first_name"] + " " + d["last_name"]
        new_user_id = int(d["uid"])

        friends = vk_requests.get_my_friends_list(access_token, new_user_id)
        j = random.randrange(1000, 10001, 1) % (len(friends) - num_friends)
        while i < num_friends:
            self.emit(QtCore.SIGNAL("loading"), True, (i * 100 / num_friends), "loading friends...")
            f_img = vk_requests.get_imgs_metadata(access_token, friends[j % len(friends)])
            f_urls = vk_requests.get_photos_urls(f_img)
            self.save_photos(f_urls, IMG_FOLDER_NOTME)
            i += 1
            j += 34
        self.emit(QtCore.SIGNAL("loading"), False)
        self.emit(QtCore.SIGNAL("loading"), True, 0, "loading me...")
        imgs = vk_requests.get_imgs_metadata(access_token, new_user_id)
        urls = vk_requests.get_photos_urls(imgs)
        self.save_photos(urls, IMG_FOLDER_ME)
        self.emit(QtCore.SIGNAL("finishloading"))

        file_list1 = os.listdir(os.path.join(fileDir, IMG_FOLDER_NOTME))
        file_list2 = os.listdir(os.path.join(fileDir, IMG_FOLDER_ME))

        i = 0
        for file1 in file_list1:
            img1 = cv.imread(os.path.join(os.path.join(fileDir, IMG_FOLDER_NOTME), file1))
            if img1 is not None:
                bb = align.getLargestFaceBoundingBox(img1, skipMulti=True)
                if bb is not None:
                    landmarks1 = align.findLandmarks(img1, bb)
                    self.image = face_aligned(img1, bb, self.aligned_size, landmarks=landmarks1,
                                              landmarks_i=openface.AlignDlib.OUTER_EYES_AND_NOSE)
                    if self.image is not None:
                        fc = face.Face(self.image, 0)
                        self.Faces.append(fc)
                        self.others += 1
                        self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                        bl = (bb.left(), bb.bottom())
                        tr = (bb.right(), bb.top())
                        cv.rectangle(img1, bl, tr, color=(153, 255, 204), thickness=3)
                        for p in openface.AlignDlib.OUTER_EYES_AND_NOSE:
                            cv.circle(img1, center=landmarks1[p], radius=3, color=(255, 100, 50), thickness=-1)
                        cv.putText(img1, "your friend", (bb.left(), bb.top() - 10), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness=2)
                        image_out = cvimage2qimage(img1)
                        self.emit(QtCore.SIGNAL("img_signal"), image_out)
            i += 1
            self.emit(QtCore.SIGNAL("loading"), True, i * 100 / len(file_list1),"learning friend" + str(file1))

        self.emit(QtCore.SIGNAL("loading"), False)
        i = 0
        for file2 in file_list2:
            img2 = cv.imread(os.path.join(os.path.join(fileDir, IMG_FOLDER_ME), file2))
            if img2 is not None:
                bb = align.getLargestFaceBoundingBox(img2, skipMulti=True)
                if bb is not None:
                    landmarks2 = align.findLandmarks(img2, bb)
                    self.image = face_aligned(img2, bb, self.aligned_size, landmarks=landmarks2,
                                              landmarks_i=openface.AlignDlib.OUTER_EYES_AND_NOSE)
                    if self.image is not None:
                        fc = face.Face(self.image, 1)
                        self.owner += 1
                        self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                        self.Faces.append(fc)
                        bl = (bb.left(), bb.bottom())
                        tr = (bb.right(), bb.top())
                        cv.rectangle(img2, bl, tr, color=(153, 255, 204), thickness=3)
                        for p in openface.AlignDlib.OUTER_EYES_AND_NOSE:
                            cv.circle(img2, center=landmarks2[p], radius=3, color=(255, 100, 50), thickness=-1)
                        cv.putText(img2, self.my_name, (bb.left(), bb.top() - 10), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness=2)
                        image_out = cvimage2qimage(img2)
                        self.emit(QtCore.SIGNAL("img_signal"), image_out)
            i += 1
            self.emit(QtCore.SIGNAL("loading"),True, i * 100 / len(file_list2), "learning me" + str(file2))
        self.emit(QtCore.SIGNAL("loading"), False)


    def run(self):
        cap = cv.VideoCapture(0)
        i = 0
        while True:
            if (self.end_learning is True):
                if (self.first_flag is True):
                    if (face.checking_one_face(self.Faces) == False):
                        self.lr = trainLR(self.Faces)
                else:
                    self.first_flag = True
                self.end_learning = False

            ok,img = cap.read()
            if img != None:
                bb = align.getLargestFaceBoundingBox(img, skipMulti = True)
                if bb is not None:
                    landmaks_a = align.findLandmarks(img, bb)
                    if landmaks_a is not None:
                        self.image = face_aligned(img, bb, self.aligned_size, landmarks=landmaks_a, landmarks_i=openface.AlignDlib.OUTER_EYES_AND_NOSE)
            id = 0
            if (self.learning == 0):
                if (self.image is not None):
                    if (self.lr is not None):
                        rep = net.forward(self.image)
                        id = self.lr.predict_proba(rep)[0][1]
                    else:
                        id = 0
                    self.emit(QtCore.SIGNAL("probabil"), id)
                                                    # now id -> probability of id == 1.
                                                  # ^ - prob of 1. If there was 0, that would be prob of 0
                                                  # http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
                if (id > PROBABILITY_THRESHOLD):
                    self.name = self.my_name
                else:
                    self.name = "Others"

                if bb is not None:
                    bl = (bb.left(), bb.bottom())
                    tr = (bb.right(), bb.top())
                    cv.rectangle(img, bl, tr, color=(153, 255, 204), thickness=3)
                    for p in openface.AlignDlib.OUTER_EYES_AND_NOSE:
                        cv.circle(img, center=landmaks_a[p], radius=3, color=(255, 100, 50), thickness=-1)
                    cv.putText(img, self.name, (bb.left(), bb.top() - 10), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness=2)

            if (self.learning == 1):
                if(i < self.iters):
                    if self.image is not None:
                        if(self.caller.comboBox.currentText() == "Owner"):
                            fc = face.Face(self.image, 1)
                            self.owner += 1
                            self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                        if(self.caller.comboBox.currentText() == "Others"):
                            fc = face.Face(self.image, 0)
                            self.others += 1
                            self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                        self.Faces.append(fc)
                        self.emit(QtCore.SIGNAL("loading"), True, i*100/self.iters, "teaching from cameras")
                        i+=1
                        if ( i >= self.iters):
                            self.emit(QtCore.SIGNAL("loading"), False)
                            self.learning = 0
                            self.end_learning = True
                            i = 0

            j = 0
            if(self.learning == 2):
                file_list = os.listdir(self.caller.lineEdit_2.text())
                for filem in file_list:
                    img_l = cv.imread(os.path.join(str(self.caller.lineEdit_2.text()),filem))
                    if img_l is not None:
                        bb = align.getLargestFaceBoundingBox(img_l, skipMulti=True)
                        if bb is not None:
                            landmaks_a = align.findLandmarks(img_l, bb)
                            if landmaks_a is not None:
                                self.image = face_aligned(img_l, bb, self.aligned_size, landmarks=landmaks_a, landmarks_i=openface.AlignDlib.OUTER_EYES_AND_NOSE)
                                if self.image is not None:
                                    if (self.caller.comboBox.currentText() == "Owner"):
                                        fc = face.Face(self.image, 1)
                                        self.owner+=1
                                        self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                                    if (self.caller.comboBox.currentText() == "Others"):
                                        fc = face.Face(self.image, 0)
                                        self.others+=1
                                        self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                                    if bb is not None:
                                        bl = (bb.left(), bb.bottom())
                                        tr = (bb.right(), bb.top())
                                        cv.rectangle(img_l, bl, tr, color=(153, 255, 204), thickness=3)
                                        for p in openface.AlignDlib.OUTER_EYES_AND_NOSE:
                                            cv.circle(img_l, center=landmaks_a[p], radius=3, color=(255, 100, 50),
                                                      thickness=-1)
                                        cv.putText(img_l, "Others", (bb.left(), bb.top() - 10), cv.FONT_HERSHEY_SIMPLEX,
                                                   fontScale=0.75, color=(153, 255, 204), thickness=2)

                                    image_out = cvimage2qimage(img_l)
                                    self.emit(QtCore.SIGNAL("img_signal"), image_out)
                                    self.Faces.append(fc)
                                    self.emit(QtCore.SIGNAL("loading"), True, j * 100 / len(file_list), "teaching from folder " + str(filem))
                    if (j >= (len(file_list)-1)):
                        self.emit(QtCore.SIGNAL("loading"), False)
                        self.end_learning = True
                        self.learning = 0
                    j+=1

            if(self.learning == 3):
                self.vk_learning()
                self.end_learning = True
                self.learning = 0

            image_out = cvimage2qimage(img)
            self.emit(QtCore.SIGNAL("img_signal"), image_out)


class  LoggingForm(QtGui.QWidget):
    def __init__(self):
        super(LoggingForm, self).__init__()
        uic.loadUi(os.path.join(fileDir, "log_form.ui"), self)
        self.setGeometry(500,800, 401, 170)

class GuiWindow(QtGui.QMainWindow):
    def __init__(self):
        super(GuiWindow, self).__init__()
        uic.loadUi(os.path.join(fileDir, "mwinvk.ui"), self)
        self.loadingwidget = LoadingWidget()
        self.loggingwidget = LoggingForm()

        self.radioButton.setChecked(True)
        self.radioButton_2.setChecked(False)
        self.lineEdit_2.setEnabled(False)
        self.toolButton.setEnabled(False)
        self.radioButton_2.toggled.connect(self.radioB2toggled)
        self.radioButton.toggled.connect(self.radioBtoggled)
        self.radioButton_3.toggled.connect(self.radioB3toggled)
        self.calc_thread_run()
        self.show()

    def OwnerOthers(self, owner, others):
        self.label_6.setText(str(owner))
        self.label_4.setText(str(others))

    def radioB3toggled(self):
        self.lineEdit_2.setEnabled(False)
        self.toolButton.setEnabled(False)

    def radioB2toggled(self):
        self.lineEdit_2.setEnabled(True)
        self.toolButton.setEnabled(True)

    def radioBtoggled(self):
        self.lineEdit_2.setEnabled(False)
        self.toolButton.setEnabled(False)

    def opendialog(self):
        tmp_str = QFileDialog.getExistingDirectory(self,"open dialog", "/home/ivan/PycharmProjects")
        self.lineEdit_2.setText(tmp_str)


    def calc_thread_run(self):
        self.mythread = Calculate_thread(caller=self)
        self.mythread.start()
        self.connect(self.mythread,   QtCore.SIGNAL("img_signal"),  self.video_input)
        self.connect(self.mythread,   QtCore.SIGNAL("probabil"),    self.setprob)
        self.connect(self.toolButton, QtCore.SIGNAL("clicked()"),   self.opendialog)
        self.connect(self.mythread,   QtCore.SIGNAL("loading"),     self.loading)
        self.connect(self.mythread,   QtCore.SIGNAL("logging"),     self.logging)
        self.connect(self.mythread,   QtCore.SIGNAL("ownoth"),      self.OwnerOthers)

    def loading(self,start, var = 100, s = ""):
        self.loadingwidget.label.setText(str(s))
        self.loadingwidget.progressBar.setValue(var)
        if start is True:
            self.loadingwidget.show()
        else:
            self.loadingwidget.hide()

    def logging(self, start):
        if start is True:
            self.loggingwidget.show()
        else:
            self.loggingwidget.hide()


    def video_input(self,image):
        self.label.setPixmap(QPixmap.fromImage(image))

    def setprob(self, prob):
        self.label_2.setText(str(prob))

def trainLR(Faces):
    rep = []
    identities = []
    for face in Faces:
        rep.append(net.forward(face.cv_img))
        identities.append(face.identity)
    rep = np.vstack(rep)
    identities = np.array(identities)

    param_grid = [
        {'C': [0.001, 0.01, 0.1, 1, 10],
         'penalty': ['l1', 'l2']}
    ]

    # http://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html
    lr = GridSearchCV(LR(C=1), param_grid, cv=5, n_jobs=4).fit(rep, identities) # n_jobs param is for parallel computation, try differen values
    return lr

def face_aligned(img, bb, size, landmarks, landmarks_i = openface.AlignDlib.OUTER_EYES_AND_NOSE):
    if ((img is not None) and (bb is not None)):
        rgbFrame = img
        alignedFace = align.align(size, rgbFrame, bb=bb, landmarks = landmarks, landmarkIndices=landmarks_i)
        if alignedFace is not None:
            return alignedFace

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = GuiWindow()
    app.exec_()
