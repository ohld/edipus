from PyQt4 import QtCore
from PyQt4.QtGui import QImage
from PyQt4.QtGui import QMessageBox
import vk_requests
import os
import random
import urllib2
import aligning
import shutil
import cv2 as cv
import numpy as np
from sklearn.grid_search import GridSearchCV
from sklearn.linear_model import LogisticRegression as LR
import face
import pickle
import torch_net

fileDir = os.path.dirname(os.path.realpath(__file__))

IMG_FOLDER_ME = 'me'
IMG_FOLDER_NOTME = 'notme'

modelDir = os.path.join(fileDir, 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
align = aligning.AlignDlib(os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))
networkModel = os.path.join(openfaceModelDir, 'nn4.small2.v1.t7')
net = torch_net.TorchNeuralNet(networkModel)


PROBABILITY_THRESHOLD = 0.8

def cvimage2qimage(img):
    height, width, bytesPerComponent = img.shape
    bytesPerLine = bytesPerComponent * width
    cv.cvtColor(img, cv.COLOR_BGR2RGB, img)
    q_image = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
    q_image = q_image.scaled(491, 481)
    return q_image



class Calculate_thread(QtCore.QThread):
    def __init__(self, parent = None, caller = None):
        QtCore.QThread.__init__(self, parent)
        self.caller = caller
        self.probth = 0.8
        self.Faces = []
        self.lr = None
        self.scaling = 0
        self.aligned_size = 96
        self.landmarks_type = aligning.AlignDlib.OUTER_EYES_AND_NOSE

        #flags
        self.first_flag     = False
        self.logging_next   = False
        self.end_learning   = False

        self.learning = 0  # 0 - not learning
                           # 1 - video learning
                           # 2 - photo learning
                           # 3 - social networks
        self.loading_flag = False
        self.owner= 0
        self.others = 0
        self.iters = 30
        self.name = ""
        self.my_name = "Owner"
        self.image = None
        self.connect(self.caller.pushButton,               QtCore.SIGNAL("clicked()"), self.start_learning)
        self.connect(self.caller.loggingwidget.pushButton, QtCore.SIGNAL("clicked()"), self.logg_next)
        self.connect(self.caller.pushButton_2,             QtCore.SIGNAL("clicked()"), self.checking)
        self.connect(self.caller.settingswigdet.pushButton,QtCore.SIGNAL("clicked()"), self.load_settings)

    def load_settings(self):
        self.probth = float(self.caller.settingswigdet.lineEdit.text())
        self.aligned_size = int(self.caller.settingswigdet.lineEdit_2.text())
        self.iters = int(self.caller.settingswigdet.lineEdit_3.text())
        self.scaling = int(self.caller.settingswigdet.spinBox.value())
        self.set_landmarks(self.caller.settingswigdet.comboBox.currentText())

    def set_landmarks(self, landmarks_type):
        if landmarks_type == "outer eyes and nose":
            self.landmarks_type = aligning.AlignDlib.OUTER_EYES_AND_NOSE
        if landmarks_type == "inner eyes and bottom lip":
            self.landmarks_type = aligning.AlignDlib.INNER_EYES_AND_BOTTOM_LIP

    def checking(self):
        self.loading_flag = True


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
                bb = align.getLargestFaceBoundingBox(img1, skipMulti=True, scaling=self.scaling)
                if bb is not None:
                    landmarks1 = align.findLandmarks(img1, bb)
                    self.image = face_aligned(img1, bb, self.aligned_size, landmarks=landmarks1,
                                              landmarks_i=self.landmarks_type, scaling=self.scaling)
                    if self.image is not None:
                        fc = face.Face(self.image, 0)
                        self.Faces.append(fc)
                        self.others += 1
                        self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                        bl = (bb.left(), bb.bottom())
                        tr = (bb.right(), bb.top())
                        cv.rectangle(img1, bl, tr, color=(153, 255, 204), thickness=3)
                        for p in self.landmarks_type:
                            cv.circle(img1, center=landmarks1[p], radius=3, color=(255, 100, 50), thickness=-1)
                        cv.putText(img1, "your friend", (bb.left(), bb.bottom() + 20), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness=2)
                        image_out = cvimage2qimage(img1)
                        self.emit(QtCore.SIGNAL("img_signal"), image_out)
            i += 1
            self.emit(QtCore.SIGNAL("loading"), True, i * 100 / len(file_list1),"learning friend" + str(file1))

        self.emit(QtCore.SIGNAL("loading"), False)
        i = 0
        for file2 in file_list2:
            img2 = cv.imread(os.path.join(os.path.join(fileDir, IMG_FOLDER_ME), file2))
            if img2 is not None:
                bb = align.getLargestFaceBoundingBox(img2, skipMulti=True,scaling=self.scaling)
                if bb is not None:
                    landmarks2 = align.findLandmarks(img2, bb)
                    self.image = face_aligned(img2, bb, self.aligned_size, landmarks=landmarks2,
                                              landmarks_i=self.landmarks_type, scaling=self.scaling)
                    if self.image is not None:
                        fc = face.Face(self.image, 1)
                        self.owner += 1
                        self.emit(QtCore.SIGNAL("ownoth"), self.owner, self.others)
                        self.Faces.append(fc)
                        bl = (bb.left(), bb.bottom())
                        tr = (bb.right(), bb.top())
                        cv.rectangle(img2, bl, tr, color=(153, 255, 204), thickness=3)
                        for p in self.landmarks_type:
                            cv.circle(img2, center=landmarks2[p], radius=3, color=(255, 100, 50), thickness=-1)
                        cv.putText(img2, self.my_name, (bb.left(), bb.bottom() + 20), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness=2)
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
            if ok is not True:
                msg  = "video device is busy"
                self.emit(QtCore.SIGNAL("error"), msg)
                break

            if img != None:
                bb = align.getLargestFaceBoundingBox(img, skipMulti = True,scaling=self.scaling)
                if bb is not None:
                    landmaks_a = align.findLandmarks(img, bb)
                    if landmaks_a is not None:
                        self.image = face_aligned(img, bb, self.aligned_size, landmarks=landmaks_a, landmarks_i=self.landmarks_type, scaling=self.scaling)
            id = 0
            if (self.learning == 0):
                if (self.image is not None):
                    if (self.lr is not None):
                        rep = net.forward(self.image)
                        id = self.lr.predict_proba(rep)[0][1]
                    else:
                        id = 0

                    self.emit(QtCore.SIGNAL("probabil"), id)
                if self.loading_flag is True:
                    if os.path.exists(os.path.join(fileDir,"classifier.pkl")):
                        os.remove(os.path.join(fileDir,"classifier.pkl"))
                    fname = os.path.join(fileDir, "classifier.pkl")
                    with open(fname, 'w') as f:
                        pickle.dump(self.lr, f)
                        self.emit(QtCore.SIGNAL("p_control"), " NETWORK HAS BEEN SAVED ", "black")
                        self.loading_flag = False
                                                  # now id -> probability of id == 1.
                                                  # ^ - prob of 1. If there was 0, that would be prob of 0
                                                  # http://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
                if (id > self.probth):
                    self.name = self.my_name
                else:
                    self.name = "Others"

                if bb is not None:
                    bl = (bb.left(), bb.bottom())
                    tr = (bb.right(), bb.top())
                    cv.rectangle(img, bl, tr, color=(153, 255, 204), thickness=3)
                    for p in self.landmarks_type:
                        cv.circle(img, center=landmaks_a[p], radius=3, color=(255, 100, 50), thickness=-1)
                    cv.putText(img, self.name, (bb.left(), bb.bottom() + 20), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness=2)

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
                        bb = align.getLargestFaceBoundingBox(img_l, skipMulti=True,scaling=self.scaling)
                        if bb is not None:
                            landmaks_a = align.findLandmarks(img_l, bb)
                            if landmaks_a is not None:
                                self.image = face_aligned(img_l, bb, self.aligned_size, landmarks=landmaks_a, landmarks_i=self.landmarks_type, scaling=self.scaling)
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
                                        for p in self.landmarks_type:
                                            cv.circle(img_l, center=landmaks_a[p], radius=3, color=(255, 100, 50),
                                                      thickness=-1)
                                        cv.putText(img_l, "Others", (bb.left(), bb.bottom() + 20), cv.FONT_HERSHEY_SIMPLEX,
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

def face_aligned(img, bb, size, landmarks, landmarks_i = aligning.AlignDlib.OUTER_EYES_AND_NOSE, scaling = 0):
    if ((img is not None) and (bb is not None)):
        rgbFrame = img
        alignedFace = align.align(size, rgbFrame, bb=bb, landmarks = landmarks, landmarkIndices=landmarks_i, scaling = scaling)
        if alignedFace is not None:
            return alignedFace