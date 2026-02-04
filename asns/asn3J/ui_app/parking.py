# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'parking.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QTextEdit,
    QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(573, 450)
        self.checkbox_spot1 = QCheckBox(Dialog)
        self.checkbox_spot1.setObjectName(u"checkbox_spot1")
        self.checkbox_spot1.setEnabled(False)
        self.checkbox_spot1.setGeometry(QRect(80, 70, 101, 41))
        self.checkbox_spot2 = QCheckBox(Dialog)
        self.checkbox_spot2.setObjectName(u"checkbox_spot2")
        self.checkbox_spot2.setEnabled(False)
        self.checkbox_spot2.setGeometry(QRect(80, 110, 101, 41))
        self.checkbox_spot3 = QCheckBox(Dialog)
        self.checkbox_spot3.setObjectName(u"checkbox_spot3")
        self.checkbox_spot3.setEnabled(False)
        self.checkbox_spot3.setGeometry(QRect(80, 150, 101, 41))
        self.checkbox_spot4 = QCheckBox(Dialog)
        self.checkbox_spot4.setObjectName(u"checkbox_spot4")
        self.checkbox_spot4.setEnabled(False)
        self.checkbox_spot4.setGeometry(QRect(80, 190, 101, 41))
        self.checkbox_spot5 = QCheckBox(Dialog)
        self.checkbox_spot5.setObjectName(u"checkbox_spot5")
        self.checkbox_spot5.setEnabled(False)
        self.checkbox_spot5.setGeometry(QRect(80, 230, 101, 41))
        self.button_warn_on = QPushButton(Dialog)
        self.button_warn_on.setObjectName(u"button_warn_on")
        self.button_warn_on.setGeometry(QRect(190, 180, 71, 51))
        self.button_warn_off = QPushButton(Dialog)
        self.button_warn_off.setObjectName(u"button_warn_off")
        self.button_warn_off.setGeometry(QRect(190, 120, 71, 51))
        self.label_sensor_data = QLabel(Dialog)
        self.label_sensor_data.setObjectName(u"label_sensor_data")
        self.label_sensor_data.setGeometry(QRect(310, 110, 141, 131))
        self.input_message = QLineEdit(Dialog)
        self.input_message.setObjectName(u"input_message")
        self.input_message.setGeometry(QRect(30, 280, 331, 41))
        self.button_send_msg = QPushButton(Dialog)
        self.button_send_msg.setObjectName(u"button_send_msg")
        self.button_send_msg.setGeometry(QRect(360, 280, 101, 41))
        self.textEdit = QTextEdit(Dialog)
        self.textEdit.setObjectName(u"textEdit")
        self.textEdit.setGeometry(QRect(30, 20, 431, 41))
        self.textEdit_2 = QTextEdit(Dialog)
        self.textEdit_2.setObjectName(u"textEdit_2")
        self.textEdit_2.setGeometry(QRect(40, 70, 31, 41))
        self.textEdit_3 = QTextEdit(Dialog)
        self.textEdit_3.setObjectName(u"textEdit_3")
        self.textEdit_3.setGeometry(QRect(40, 110, 31, 41))
        self.textEdit_4 = QTextEdit(Dialog)
        self.textEdit_4.setObjectName(u"textEdit_4")
        self.textEdit_4.setGeometry(QRect(40, 150, 31, 41))
        self.textEdit_5 = QTextEdit(Dialog)
        self.textEdit_5.setObjectName(u"textEdit_5")
        self.textEdit_5.setGeometry(QRect(40, 190, 31, 41))
        self.textEdit_6 = QTextEdit(Dialog)
        self.textEdit_6.setObjectName(u"textEdit_6")
        self.textEdit_6.setGeometry(QRect(40, 230, 31, 41))

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.checkbox_spot1.setText(QCoreApplication.translate("Dialog", u"Spot 1", None))
        self.checkbox_spot2.setText(QCoreApplication.translate("Dialog", u"Spot 2", None))
        self.checkbox_spot3.setText(QCoreApplication.translate("Dialog", u"Spot 3", None))
        self.checkbox_spot4.setText(QCoreApplication.translate("Dialog", u"Spot 4", None))
        self.checkbox_spot5.setText(QCoreApplication.translate("Dialog", u"Spot 5", None))
        self.button_warn_on.setText(QCoreApplication.translate("Dialog", u"Warn ON", None))
        self.button_warn_off.setText(QCoreApplication.translate("Dialog", u"Warn OFF", None))
        self.label_sensor_data.setText("")
        self.button_send_msg.setText(QCoreApplication.translate("Dialog", u"Send", None))
        self.textEdit.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:18pt; color:#ffffff;\">Smart Parking System</span></p></body></html>", None))
        self.textEdit_2.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">1</span></p></body></html>", None))
        self.textEdit_3.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">2</span></p></body></html>", None))
        self.textEdit_4.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">3</span></p></body></html>", None))
        self.textEdit_5.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">4</span></p></body></html>", None))
        self.textEdit_6.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"hr { height: 1px; border-width: 0; }\n"
"li.unchecked::marker { content: \"\\2610\"; }\n"
"li.checked::marker { content: \"\\2612\"; }\n"
"</style></head><body style=\" font-family:'Segoe UI'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
"<p style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:14pt;\">5</span></p></body></html>", None))
    # retranslateUi

