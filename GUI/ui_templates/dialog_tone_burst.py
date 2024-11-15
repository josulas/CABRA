# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dialog_tone_burst.ui'
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
    QFormLayout, QLabel, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_DialogToneBurst(object):
    def setupUi(self, DialogToneBurst):
        if not DialogToneBurst.objectName():
            DialogToneBurst.setObjectName(u"DialogToneBurst")
        DialogToneBurst.resize(270, 173)
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.AudioVolumeHigh))
        DialogToneBurst.setWindowIcon(icon)
        self.verticalLayout = QVBoxLayout(DialogToneBurst)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.formCLick = QFormLayout()
        self.formCLick.setObjectName(u"formCLick")
        self.labelClickDuration = QLabel(DialogToneBurst)
        self.labelClickDuration.setObjectName(u"labelClickDuration")

        self.formCLick.setWidget(1, QFormLayout.LabelRole, self.labelClickDuration)

        self.spinClickDuration = QSpinBox(DialogToneBurst)
        self.spinClickDuration.setObjectName(u"spinClickDuration")
        self.spinClickDuration.setValue(10)

        self.formCLick.setWidget(1, QFormLayout.FieldRole, self.spinClickDuration)

        self.labelCycleDuration = QLabel(DialogToneBurst)
        self.labelCycleDuration.setObjectName(u"labelCycleDuration")

        self.formCLick.setWidget(2, QFormLayout.LabelRole, self.labelCycleDuration)

        self.spinCycleDuration = QSpinBox(DialogToneBurst)
        self.spinCycleDuration.setObjectName(u"spinCycleDuration")
        self.spinCycleDuration.setStyleSheet(u"border-color: rgb(0, 0, 0);")
        self.spinCycleDuration.setValue(30)

        self.formCLick.setWidget(2, QFormLayout.FieldRole, self.spinCycleDuration)

        self.labelNClicks = QLabel(DialogToneBurst)
        self.labelNClicks.setObjectName(u"labelNClicks")

        self.formCLick.setWidget(3, QFormLayout.LabelRole, self.labelNClicks)

        self.spinNClicks = QSpinBox(DialogToneBurst)
        self.spinNClicks.setObjectName(u"spinNClicks")
        self.spinNClicks.setMinimum(50)
        self.spinNClicks.setMaximum(3000)
        self.spinNClicks.setSingleStep(50)
        self.spinNClicks.setValue(500)

        self.formCLick.setWidget(3, QFormLayout.FieldRole, self.spinNClicks)


        self.verticalLayout.addLayout(self.formCLick)

        self.buttonBox = QDialogButtonBox(DialogToneBurst)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Apply|QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)

        self.verticalLayout.addWidget(self.buttonBox)


        self.retranslateUi(DialogToneBurst)
        self.buttonBox.accepted.connect(DialogToneBurst.accept)
        self.buttonBox.rejected.connect(DialogToneBurst.reject)

        QMetaObject.connectSlotsByName(DialogToneBurst)
    # setupUi

    def retranslateUi(self, DialogToneBurst):
        DialogToneBurst.setWindowTitle(QCoreApplication.translate("DialogToneBurst", u"Tone burst setup", None))
        self.labelClickDuration.setText(QCoreApplication.translate("DialogToneBurst", u"Click duration:", None))
        self.spinClickDuration.setSuffix(QCoreApplication.translate("DialogToneBurst", u" [ms]", None))
        self.labelCycleDuration.setText(QCoreApplication.translate("DialogToneBurst", u"Cycle duration:", None))
        self.spinCycleDuration.setSuffix(QCoreApplication.translate("DialogToneBurst", u" [ms]", None))
        self.labelNClicks.setText(QCoreApplication.translate("DialogToneBurst", u"Number of clicks:", None))
    # retranslateUi

