# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_reconnect.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QLabel, QSizePolicy, QVBoxLayout, QWidget)

class Ui_DialogReconnect(object):
    def setupUi(self, DialogReconnect):
        if not DialogReconnect.objectName():
            DialogReconnect.setObjectName(u"DialogReconnect")
        DialogReconnect.resize(218, 147)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ApplicationExit))
        DialogReconnect.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(DialogReconnect)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(DialogReconnect)
        self.label.setObjectName(u"label")
        self.label.setWordWrap(True)

        self.verticalLayout.addWidget(self.label)

        self.buttonBox = QDialogButtonBox(DialogReconnect)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(DialogReconnect)
        self.buttonBox.accepted.connect(DialogReconnect.accept)
        self.buttonBox.rejected.connect(DialogReconnect.reject)

        QMetaObject.connectSlotsByName(DialogReconnect)
    # setupUi

    def retranslateUi(self, DialogReconnect):
        DialogReconnect.setWindowTitle(QCoreApplication.translate("DialogReconnect", u"Error", None))
        self.label.setText(QCoreApplication.translate("DialogReconnect", u"Connection failed. Please reconnect the CABRA.", None))
    # retranslateUi

