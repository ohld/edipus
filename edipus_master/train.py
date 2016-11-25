#!/usr/bin/python2
import os
import sys
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QPixmap, QFileDialog, QMessageBox
import exec_thread

fileDir = os.path.dirname(os.path.realpath(__file__))



class  LoadingWidget(QtGui.QWidget):
    def __init__(self):
        super(LoadingWidget, self).__init__()
        uic.loadUi(os.path.join(fileDir, "ui_forms/loading.ui"), self)
        self.setGeometry(500,800, 565, 113)

class PermissionWidget(QtGui.QWidget):
    def __init__(self):
        super(PermissionWidget, self).__init__()
        uic.loadUi(os.path.join(fileDir, "ui_forms/permission.ui"), self)
        self.setGeometry(500, 800, 400, 114)


class  LoggingForm(QtGui.QWidget):
    def __init__(self):
        super(LoggingForm, self).__init__()
        uic.loadUi(os.path.join(fileDir, "ui_forms/log_form.ui"), self)
        self.setGeometry(500,800, 401, 170)

class GuiWindow(QtGui.QMainWindow):
    def __init__(self):
        super(GuiWindow, self).__init__()
        uic.loadUi(os.path.join(fileDir, "ui_forms/mwinvk.ui"), self)
        self.loadingwidget    = LoadingWidget()
        self.loggingwidget    = LoggingForm()
        self.permissionwidget = PermissionWidget()

        self.radioButton.setChecked(True)
        self.radioButton_2.setChecked(False)
        self.lineEdit_2.setEnabled(False)
        self.toolButton.setEnabled(False)
        self.radioButton_2.toggled.connect(self.radioB2toggled)
        self.radioButton.toggled.connect(self.radioBtoggled)
        self.radioButton_3.toggled.connect(self.radioB3toggled)
        self.calc_thread_run()
        self.show()

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

    def close_p_c(self):
        self.permissionwidget.hide()


    def error(self, message):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setText(message)
        msg.exec_()

    def calc_thread_run(self):
        self.mythread = exec_thread.Calculate_thread(caller=self)
        self.mythread.start()
        self.connect(self.mythread,                    QtCore.SIGNAL("img_signal"),  self.video_input)
        self.connect(self.mythread,                    QtCore.SIGNAL("probabil"),    self.setprob)
        self.connect(self.toolButton,                  QtCore.SIGNAL("clicked()"),   self.opendialog)
        self.connect(self.mythread,                    QtCore.SIGNAL("loading"),     self.loading)
        self.connect(self.mythread,                    QtCore.SIGNAL("logging"),     self.logging)
        self.connect(self.mythread,                    QtCore.SIGNAL("ownoth"),      self.OwnerOthers)
        self.connect(self.mythread,                    QtCore.SIGNAL("p_control"),   self.permission_control)
        self.connect(self.permissionwidget.pushButton, QtCore.SIGNAL(("clicked()")), self.close_p_c)
        self.connect(self.mythread,                    QtCore.SIGNAL("error"),       self.error)

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

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = GuiWindow()
    app.exec_()
