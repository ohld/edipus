import webbrowser
import pickle
import json
import urllib2
import os
import urlparse
import openface
import cv2 as cv
import sys
from sklearn.grid_search import GridSearchCV
from sklearn.svm import SVC
import numpy as np
from datetime import datetime, timedelta
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QImage, QPixmap, QFileDialog
import random
import shutil

fileDir = os.path.dirname(os.path.realpath(__file__))

modelDir = os.path.join(fileDir, 'models')
dlibModelDir = os.path.join(modelDir, 'dlib')
openfaceModelDir = os.path.join(modelDir, 'openface')
align = openface.AlignDlib(os.path.join(dlibModelDir, "shape_predictor_68_face_landmarks.dat"))
networkModel = os.path.join(openfaceModelDir, 'nn4.small2.v1.t7')
net = openface.TorchNeuralNet(networkModel)



APP_ID = '5712831'
IMG_FOLDER_ME = 'me'
IMG_FOLDER_NOTME = 'notme'
# file, where auth data is saved
AUTH_FILE = '.auth_data'


def get_saved_auth_params():
    access_token = None
    user_id = None
    try:
        with open(AUTH_FILE, 'rb') as pkl_file:
            token = pickle.load(pkl_file)
            expires = pickle.load(pkl_file)
            uid = pickle.load(pkl_file)
        if datetime.now() < expires:
            access_token = token
            user_id = uid
    except IOError:
        pass
    return access_token, user_id


def save_auth_params(access_token, expires_in, user_id):
    expires = datetime.now() + timedelta(seconds=int(expires_in))
    with open(AUTH_FILE, 'wb') as output:
        pickle.dump(access_token, output)
        pickle.dump(expires, output)
        pickle.dump(user_id, output)


def get_auth_params():
    auth_url = ("https://oauth.vk.com/authorize?client_id={app_id}"
        "&scope=photos&redirect_uri=http://oauth.vk.com/blank.html"
        "&display=page&response_type=token".format(app_id=APP_ID))
    webbrowser.open_new_tab(auth_url)
    redirected_url = raw_input("Paste here url you were redirected:\n")
    aup = urlparse.parse_qs(redirected_url)
    aup['access_token'] = aup.pop(
        'https://oauth.vk.com/blank.html#access_token')
    save_auth_params(aup['access_token'][0], aup['expires_in'][0],
        aup['user_id'][0])
    return aup['access_token'][0], aup['user_id'][0]


def get_imgs_metadata(access_token, user_id):
    url = ("https://api.vkontakte.ru/method/photos.getProfile.json?"
        "uid={uid}&access_token={atoken}".format(uid=user_id, atoken=access_token))
    imgs_get_page = urllib2.urlopen(url).read()
    return json.loads(imgs_get_page)['response']


def get_me(access_token, user_id):
    url = ("https://api.vkontakte.ru/method/users.get.json?"
           "uids={uids}&access_token={atoken}".format(uids=user_id, atoken=access_token))
    info = urllib2.urlopen(url).read()
    return json.loads(info)['response']


def get_my_friends_list(access_token, user_id):
    url = ("https://api.vkontakte.ru/method/friends.get.json?"
        "uid={uid}&access_token={atoken}".format(uid=user_id, atoken=access_token))
    friends_get_page = urllib2.urlopen(url).read()
    return json.loads(friends_get_page)['response']


def get_photos_urls(photos_list):
    result = []
    new_photos_list = take_n_first(photos_list, 8)
    for photo in new_photos_list:
        #Choose photo with largest resolution
        if "src_xxbig" in photo:
            url = photo["src_xxbig"]
        elif "src_xbig" in photo:
            url = photo["src_xbig"]
        else:
            url = photo["src_big"]
        result.append(url)
    return result


def take_n_first(list_l, n):
    i = 0
    out_list = []
    while ((i < n) and (i < len(list_l))):
        out_list.append(list_l[i])
        i+=1
    return out_list


class Face:
    def __init__(self, cv_img, identity):
        self.cv_img = cv_img
        self.identity = identity

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
        uic.loadUi(os.path.join(fileDir, "untitled.ui"), self)
        self.setGeometry(500,800, 565, 113)



class Calculate_thread(QtCore.QThread):
    def __init__(self, parent = None, caller = None):
        QtCore.QThread.__init__(self, parent)
        self.caller = caller
        self.Faces      = []
        self.svm = None
        self.aligned_size = 96
        self.name = ""
        self.my_name = ""

    def save_photos(self,urls, directory):
        if not os.path.exists(directory):
            os.mkdir(directory)
        for num, url in enumerate(urls):
            a = url.split("/")
            b = len(a)
            names_pattern = str(random.randrange(1000, 10001, 1)) + str(a[b - 1])
            filename = os.path.join(directory, names_pattern)
            s = "Downloading " + str(filename)
            self.emit(QtCore.SIGNAL("loading") ,s)
            #print "Downloading %s" % filename
            open(filename, "w").write(urllib2.urlopen(url).read())

    def run(self):

        access_token, user_id = get_saved_auth_params()
        if not access_token or not user_id:
            access_token, user_id = get_auth_params()

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
        dictionary = get_me(access_token,new_user_id)
        d = dictionary[0]
        self.my_name = d["first_name"] + " " + d["last_name"]
        new_user_id = int(d["uid"])

        friends = get_my_friends_list(access_token, new_user_id)
        j = random.randrange(1000, 10001, 1) % (len(friends) - num_friends)
        while i < num_friends:
            self.emit(QtCore.SIGNAL("loader_signal_f"), (i * 100 / num_friends))
            f_img = get_imgs_metadata(access_token, friends[j%len(friends)])
            f_urls = get_photos_urls(f_img)
            self.save_photos(f_urls, IMG_FOLDER_NOTME)
            i += 1
            j += 34
        self.emit(QtCore.SIGNAL("loader_my"))
        imgs = get_imgs_metadata(access_token, new_user_id)
        urls = get_photos_urls(imgs)
        self.save_photos(urls, IMG_FOLDER_ME)
        self.emit(QtCore.SIGNAL("finishloading"))



        cap = cv.VideoCapture(0)
        file_list1 = os.listdir(os.path.join(fileDir, IMG_FOLDER_NOTME))
        file_list2 = os.listdir(os.path.join(fileDir, IMG_FOLDER_ME))

        i = 0
        for file1 in file_list1:
            img1 = cv.imread(os.path.join(os.path.join(fileDir, IMG_FOLDER_NOTME), file1))
            if img1 is not None:
                bb = align.getLargestFaceBoundingBox(img1)
                if bb is not None:
                    landmarks1 = align.findLandmarks(img1, bb)
                    self.image = face_aligned(img1, bb, self.aligned_size, landmarks = landmarks1, landmarks_i = openface.AlignDlib.OUTER_EYES_AND_NOSE)
                    if self.image is not None:
                        fc = Face(self.image, 0)
                        self.Faces.append(fc)
                        image_out = cvimage2qimage(img1)
                        self.emit(QtCore.SIGNAL("img_signal"), image_out)
            i+=1
            self.emit(QtCore.SIGNAL("learinig_friends"), i*100/len(file_list1))

        self.emit(QtCore.SIGNAL("finish_learinig_friends"))
        i = 0
        for file2 in file_list2:
            img2 = cv.imread(os.path.join(os.path.join(fileDir, IMG_FOLDER_ME), file2))
            if img2 is not None:
                bb = align.getLargestFaceBoundingBox(img2)
                if bb is not None:
                    landmarks2 = align.findLandmarks(img2, bb)
                    self.image = face_aligned(img2, bb, self.aligned_size, landmarks = landmarks2, landmarks_i = openface.AlignDlib.OUTER_EYES_AND_NOSE)
                    if self.image is not None:
                        fc = Face(self.image, 1)
                        self.Faces.append(fc)
                        image_out = cvimage2qimage(img2)
                        self.emit(QtCore.SIGNAL("img_signal"), image_out)
            i+=1
            self.emit(QtCore.SIGNAL("learinig_me"), i*100/len(file_list2))
        self.emit(QtCore.SIGNAL("finish_learning_me"))


        self.svm = trainSVM(self.Faces)
        self.emit(QtCore.SIGNAL("svm_trained"))
        while True:
            ok,img = cap.read()
            if img != None:
                bb = align.getLargestFaceBoundingBox(img)
                if bb is not None:
                    landmaks_a = align.findLandmarks(img, bb)
                    if landmaks_a is not None:
                        self.image = face_aligned(img, bb, self.aligned_size, landmarks=landmaks_a, landmarks_i=openface.AlignDlib.OUTER_EYES_AND_NOSE)
            id = -1
            if (self.image is not None):
                rep = net.forward(self.image)
                id = self.svm.predict(rep)[0]
            if (id == 0):
                self.name = "not Identified"
            if (id == 1):
                self.name = self.my_name

            if bb is not None:
                bl = (bb.left(), bb.bottom())
                tr = (bb.right(), bb.top())
                cv.rectangle(img, bl, tr, color=(153, 255, 204), thickness=3)
                for p in openface.AlignDlib.OUTER_EYES_AND_NOSE:
                    cv.circle(img, center=landmaks_a[p], radius=3, color=(255, 100, 50), thickness=-1)
                cv.putText(img, self.name, (bb.left(), bb.top() - 10), cv.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(152, 255, 204), thickness=2)

            #self.emit(QtCore.SIGNAL("ident_signal"), id)
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
        self.mywidget = LoadingWidget()
        self.loggingwidget = LoggingForm()
        self.loggingwidget.lineEdit.setText("84920305")
        self.loggingwidget.show()
        self.connect(self.loggingwidget.pushButton, QtCore.SIGNAL("clicked()"), self.calc_thread_run)


    def calc_thread_run(self):
        self.mythread = Calculate_thread(caller=self)
        self.mythread.start()
        self.connect(self.mythread, QtCore.SIGNAL("img_signal"), self.video_input)
        self.connect(self.mythread, QtCore.SIGNAL("loader_signal_f"), self.loader_f)
        self.connect(self.mythread, QtCore.SIGNAL("finishloading"), self.finish)
        self.connect(self.mythread, QtCore.SIGNAL("learinig_friends"), self.learningf)
        self.connect(self.mythread, QtCore.SIGNAL("learinig_me"), self.learningme)
        self.connect(self.mythread, QtCore.SIGNAL("finish_learning_me"), self.fin_learning)
        self.connect(self.mythread, QtCore.SIGNAL("loading"), self.loading)
        self.loggingwidget.hide()

    def video_input(self,image):
        self.label.setPixmap(QPixmap.fromImage(image))
    def loader_f(self, ar):
        self.mywidget.progressBar.setValue(ar)
        self.mywidget.progressBar.show()
        self.mywidget.label.setText("start loading friends info")
        self.mywidget.show()
        self.hide()
    def finish(self):
        self.mywidget.progressBar.setValue(100)
        self.mywidget.progressBar.setValue(0)
        self.mywidget.label.setText("")
    def learningf(self, ar):
        self.show()
        self.mywidget.progressBar.setValue(ar)
        self.mywidget.label.setText("learning friends")
    def learningme(self, ar):
        self.mywidget.progressBar.setValue(ar)
        self.mywidget.label.setText("learning me")
    def fin_learning(self):
        self.mywidget.label.setText("learining finished")
        self.mywidget.hide()
    def loading(self,s):
        self.mywidget.label.setText("start loading friends info " + s)

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



if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    window = GuiWindow()
    app.exec_()
