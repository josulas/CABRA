# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'template.ui'
##
## Created by: Qt User Interface Compiler version 6.8.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit,
    QFormLayout, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QMenu, QMenuBar,
    QPushButton, QRadioButton, QSizePolicy, QSpinBox,
    QStatusBar, QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(782, 639)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionNumber_of_clicks = QAction(MainWindow)
        self.actionNumber_of_clicks.setObjectName(u"actionNumber_of_clicks")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.frameControl = QFrame(self.centralwidget)
        self.frameControl.setObjectName(u"frameControl")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.frameControl.sizePolicy().hasHeightForWidth())
        self.frameControl.setSizePolicy(sizePolicy)
        self.frameControl.setMinimumSize(QSize(0, 100))
        self.frameControl.setStyleSheet(u"background-color: rgb(55, 50, 50);\n"
"gridline-color: rgb(0, 0, 0);\n"
"border-color: rgb(0, 0, 0);\n"
"font: 9pt \"Arialt\";\n"
"color: rgb(255, 255, 255);")
        self.frameControl.setFrameShape(QFrame.Shape.StyledPanel)
        self.frameControl.setFrameShadow(QFrame.Shadow.Raised)
        self.horizontalLayout = QHBoxLayout(self.frameControl)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.formPatientData = QFormLayout()
        self.formPatientData.setObjectName(u"formPatientData")
        self.labelName = QLabel(self.frameControl)
        self.labelName.setObjectName(u"labelName")

        self.formPatientData.setWidget(0, QFormLayout.LabelRole, self.labelName)

        self.nameEdit = QLineEdit(self.frameControl)
        self.nameEdit.setObjectName(u"nameEdit")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.nameEdit.sizePolicy().hasHeightForWidth())
        self.nameEdit.setSizePolicy(sizePolicy1)
        self.nameEdit.setStyleSheet(u"border-color: rgb(6, 6, 6);")

        self.formPatientData.setWidget(0, QFormLayout.FieldRole, self.nameEdit)

        self.labelDOB = QLabel(self.frameControl)
        self.labelDOB.setObjectName(u"labelDOB")

        self.formPatientData.setWidget(1, QFormLayout.LabelRole, self.labelDOB)

        self.labelID = QLabel(self.frameControl)
        self.labelID.setObjectName(u"labelID")

        self.formPatientData.setWidget(2, QFormLayout.LabelRole, self.labelID)

        self.dateEdit = QDateEdit(self.frameControl)
        self.dateEdit.setObjectName(u"dateEdit")
        sizePolicy1.setHeightForWidth(self.dateEdit.sizePolicy().hasHeightForWidth())
        self.dateEdit.setSizePolicy(sizePolicy1)

        self.formPatientData.setWidget(1, QFormLayout.FieldRole, self.dateEdit)

        self.lineID = QLineEdit(self.frameControl)
        self.lineID.setObjectName(u"lineID")
        sizePolicy1.setHeightForWidth(self.lineID.sizePolicy().hasHeightForWidth())
        self.lineID.setSizePolicy(sizePolicy1)
        self.lineID.setStyleSheet(u"border-color: rgb(255, 0, 0);")

        self.formPatientData.setWidget(2, QFormLayout.FieldRole, self.lineID)


        self.horizontalLayout.addLayout(self.formPatientData)

        self.VLayoutEAR = QVBoxLayout()
        self.VLayoutEAR.setObjectName(u"VLayoutEAR")
        self.VLayoutEAR.setContentsMargins(20, -1, -1, -1)
        self.HLayoutEar = QHBoxLayout()
        self.HLayoutEar.setObjectName(u"HLayoutEar")
        self.radioLeftEAR = QRadioButton(self.frameControl)
        self.radioLeftEAR.setObjectName(u"radioLeftEAR")
        self.radioLeftEAR.setChecked(True)

        self.HLayoutEar.addWidget(self.radioLeftEAR)

        self.radioRightEAR = QRadioButton(self.frameControl)
        self.radioRightEAR.setObjectName(u"radioRightEAR")

        self.HLayoutEar.addWidget(self.radioRightEAR)


        self.VLayoutEAR.addLayout(self.HLayoutEar)

        self.checkBone = QCheckBox(self.frameControl)
        self.checkBone.setObjectName(u"checkBone")

        self.VLayoutEAR.addWidget(self.checkBone)


        self.horizontalLayout.addLayout(self.VLayoutEAR)

        self.formCLick = QFormLayout()
        self.formCLick.setObjectName(u"formCLick")
        self.labelFreq = QLabel(self.frameControl)
        self.labelFreq.setObjectName(u"labelFreq")

        self.formCLick.setWidget(0, QFormLayout.LabelRole, self.labelFreq)

        self.comboBoxFreq = QComboBox(self.frameControl)
        self.comboBoxFreq.addItem("")
        self.comboBoxFreq.addItem("")
        self.comboBoxFreq.addItem("")
        self.comboBoxFreq.addItem("")
        self.comboBoxFreq.addItem("")
        self.comboBoxFreq.addItem("")
        self.comboBoxFreq.setObjectName(u"comboBoxFreq")
        sizePolicy1.setHeightForWidth(self.comboBoxFreq.sizePolicy().hasHeightForWidth())
        self.comboBoxFreq.setSizePolicy(sizePolicy1)

        self.formCLick.setWidget(0, QFormLayout.FieldRole, self.comboBoxFreq)

        self.labelClickDuration = QLabel(self.frameControl)
        self.labelClickDuration.setObjectName(u"labelClickDuration")

        self.formCLick.setWidget(1, QFormLayout.LabelRole, self.labelClickDuration)

        self.spinClickDuration = QSpinBox(self.frameControl)
        self.spinClickDuration.setObjectName(u"spinClickDuration")

        self.formCLick.setWidget(1, QFormLayout.FieldRole, self.spinClickDuration)

        self.labelCycleDuration = QLabel(self.frameControl)
        self.labelCycleDuration.setObjectName(u"labelCycleDuration")

        self.formCLick.setWidget(2, QFormLayout.LabelRole, self.labelCycleDuration)

        self.spinCycleDuration = QSpinBox(self.frameControl)
        self.spinCycleDuration.setObjectName(u"spinCycleDuration")

        self.formCLick.setWidget(2, QFormLayout.FieldRole, self.spinCycleDuration)


        self.horizontalLayout.addLayout(self.formCLick)

        self.pushRUN = QPushButton(self.frameControl)
        self.pushRUN.setObjectName(u"pushRUN")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushRUN.sizePolicy().hasHeightForWidth())
        self.pushRUN.setSizePolicy(sizePolicy2)
        self.pushRUN.setMinimumSize(QSize(100, 0))
        font = QFont()
        font.setFamilies([u"Arialt"])
        font.setPointSize(9)
        font.setBold(False)
        font.setItalic(False)
        font.setKerning(True)
        self.pushRUN.setFont(font)
        icon = QIcon(QIcon.fromTheme(u"media-playback-start"))
        self.pushRUN.setIcon(icon)
        self.pushRUN.setIconSize(QSize(20, 20))

        self.horizontalLayout.addWidget(self.pushRUN)


        self.verticalLayout.addWidget(self.frameControl)

        self.plotWidget = PlotWidget(self.centralwidget)
        self.plotWidget.setObjectName(u"plotWidget")

        self.verticalLayout.addWidget(self.plotWidget)

        self.labelStatus = QLabel(self.centralwidget)
        self.labelStatus.setObjectName(u"labelStatus")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.labelStatus.sizePolicy().hasHeightForWidth())
        self.labelStatus.setSizePolicy(sizePolicy3)

        self.verticalLayout.addWidget(self.labelStatus)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 782, 22))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuOption = QMenu(self.menubar)
        self.menuOption.setObjectName(u"menuOption")
        self.menuSet = QMenu(self.menuOption)
        self.menuSet.setObjectName(u"menuSet")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuOption.menuAction())
        self.menuFile.addAction(self.actionSave)
        self.menuOption.addAction(self.menuSet.menuAction())
        self.menuSet.addAction(self.actionNumber_of_clicks)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"CABRA", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionNumber_of_clicks.setText(QCoreApplication.translate("MainWindow", u"Number of clicks", None))
        self.labelName.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.labelDOB.setText(QCoreApplication.translate("MainWindow", u"DOB:", None))
        self.labelID.setText(QCoreApplication.translate("MainWindow", u"ID:", None))
        self.radioLeftEAR.setText(QCoreApplication.translate("MainWindow", u"Left ear", None))
        self.radioRightEAR.setText(QCoreApplication.translate("MainWindow", u"Right ear", None))
        self.checkBone.setText(QCoreApplication.translate("MainWindow", u"Bone conduction headset", None))
        self.labelFreq.setText(QCoreApplication.translate("MainWindow", u"Frequency [Hz]:", None))
        self.comboBoxFreq.setItemText(0, QCoreApplication.translate("MainWindow", u"250", None))
        self.comboBoxFreq.setItemText(1, QCoreApplication.translate("MainWindow", u"500", None))
        self.comboBoxFreq.setItemText(2, QCoreApplication.translate("MainWindow", u"1000", None))
        self.comboBoxFreq.setItemText(3, QCoreApplication.translate("MainWindow", u"2000", None))
        self.comboBoxFreq.setItemText(4, QCoreApplication.translate("MainWindow", u"4000", None))
        self.comboBoxFreq.setItemText(5, QCoreApplication.translate("MainWindow", u"8000", None))

        self.labelClickDuration.setText(QCoreApplication.translate("MainWindow", u"Click duration:", None))
        self.spinClickDuration.setSuffix(QCoreApplication.translate("MainWindow", u" [ms]", None))
        self.labelCycleDuration.setText(QCoreApplication.translate("MainWindow", u"Cycle duration:", None))
        self.spinCycleDuration.setSuffix(QCoreApplication.translate("MainWindow", u" [ms]", None))
        self.pushRUN.setText(QCoreApplication.translate("MainWindow", u"RUN", None))
        self.labelStatus.setText(QCoreApplication.translate("MainWindow", u"Set the parameters for the experiment, and hit RUN", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuOption.setTitle(QCoreApplication.translate("MainWindow", u"Options", None))
        self.menuSet.setTitle(QCoreApplication.translate("MainWindow", u"Set...", None))
    # retranslateUi

