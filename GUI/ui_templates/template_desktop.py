# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'template_desktop.ui'
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
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QStatusBar, QVBoxLayout, QWidget)

from pyqtgraph import PlotWidget

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(864, 639)
        self.actionSave = QAction(MainWindow)
        self.actionSave.setObjectName(u"actionSave")
        self.actionNumber_of_clicks = QAction(MainWindow)
        self.actionNumber_of_clicks.setObjectName(u"actionNumber_of_clicks")
        self.actionTone_burst = QAction(MainWindow)
        self.actionTone_burst.setObjectName(u"actionTone_burst")
        self.actionCABRA_Default = QAction(MainWindow)
        self.actionCABRA_Default.setObjectName(u"actionCABRA_Default")
        self.actionSimulator = QAction(MainWindow)
        self.actionSimulator.setObjectName(u"actionSimulator")
        self.actionGoated = QAction(MainWindow)
        self.actionGoated.setObjectName(u"actionGoated")
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
"color: rgb(0, 0, 0);\n"
"border-color: rgb(0, 0, 0);\n"
"font: 9pt \"Arial\";\n"
"color: rgb(255, 255, 255);\n"
"")
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

        self.dateEdit = QDateEdit(self.frameControl)
        self.dateEdit.setObjectName(u"dateEdit")
        sizePolicy1.setHeightForWidth(self.dateEdit.sizePolicy().hasHeightForWidth())
        self.dateEdit.setSizePolicy(sizePolicy1)

        self.formPatientData.setWidget(1, QFormLayout.FieldRole, self.dateEdit)

        self.labelID = QLabel(self.frameControl)
        self.labelID.setObjectName(u"labelID")

        self.formPatientData.setWidget(2, QFormLayout.LabelRole, self.labelID)

        self.lineID = QLineEdit(self.frameControl)
        self.lineID.setObjectName(u"lineID")
        sizePolicy1.setHeightForWidth(self.lineID.sizePolicy().hasHeightForWidth())
        self.lineID.setSizePolicy(sizePolicy1)
        self.lineID.setStyleSheet(u"border-color: rgb(255, 0, 0);")

        self.formPatientData.setWidget(2, QFormLayout.FieldRole, self.lineID)


        self.horizontalLayout.addLayout(self.formPatientData)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout.addItem(self.verticalSpacer_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalLayout_3.setContentsMargins(-1, -1, 0, -1)
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.labelFreq = QLabel(self.frameControl)
        self.labelFreq.setObjectName(u"labelFreq")

        self.horizontalLayout_3.addWidget(self.labelFreq)

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

        self.horizontalLayout_3.addWidget(self.comboBoxFreq)


        self.verticalLayout_3.addLayout(self.horizontalLayout_3)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.radioLeftEAR = QRadioButton(self.frameControl)
        self.radioLeftEAR.setObjectName(u"radioLeftEAR")
        self.radioLeftEAR.setChecked(True)

        self.horizontalLayout_2.addWidget(self.radioLeftEAR)

        self.radioRightEAR = QRadioButton(self.frameControl)
        self.radioRightEAR.setObjectName(u"radioRightEAR")

        self.horizontalLayout_2.addWidget(self.radioRightEAR)


        self.verticalLayout_3.addLayout(self.horizontalLayout_2)


        self.horizontalLayout.addLayout(self.verticalLayout_3)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.horizontalLayout.addItem(self.verticalSpacer)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(15, -1, 15, -1)
        self.checkBone = QCheckBox(self.frameControl)
        self.checkBone.setObjectName(u"checkBone")

        self.verticalLayout_2.addWidget(self.checkBone)

        self.pushCABRASweep = QPushButton(self.frameControl)
        self.pushCABRASweep.setObjectName(u"pushCABRASweep")
        sizePolicy1.setHeightForWidth(self.pushCABRASweep.sizePolicy().hasHeightForWidth())
        self.pushCABRASweep.setSizePolicy(sizePolicy1)
        self.pushCABRASweep.setMinimumSize(QSize(0, 20))
        font = QFont()
        font.setFamilies([u"Arial Bold"])
        font.setPointSize(11)
        font.setBold(True)
        font.setItalic(True)
        font.setUnderline(False)
        font.setStrikeOut(False)
        self.pushCABRASweep.setFont(font)
        self.pushCABRASweep.setAutoFillBackground(False)
        self.pushCABRASweep.setStyleSheet(u"background-color: rgb(230, 97, 0);\n"
"color: rgb(0, 0, 0);\n"
"font: Bold Italic 11pt \"Arial Bold\";")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ZoomFitBest))
        self.pushCABRASweep.setIcon(icon)
        self.pushCABRASweep.setIconSize(QSize(20, 20))

        self.verticalLayout_2.addWidget(self.pushCABRASweep)


        self.horizontalLayout.addLayout(self.verticalLayout_2)

        self.pushRUN = QPushButton(self.frameControl)
        self.pushRUN.setObjectName(u"pushRUN")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.pushRUN.sizePolicy().hasHeightForWidth())
        self.pushRUN.setSizePolicy(sizePolicy2)
        self.pushRUN.setMinimumSize(QSize(80, 0))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(11)
        font1.setBold(True)
        font1.setItalic(False)
        font1.setKerning(True)
        self.pushRUN.setFont(font1)
        self.pushRUN.setStyleSheet(u"background-color: rgb(246, 211, 45);\n"
"color: rgb(0,0,0);\n"
"font: 700 11pt \"Arial\";")
        icon1 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.AudioInputMicrophone))
        self.pushRUN.setIcon(icon1)
        self.pushRUN.setIconSize(QSize(20, 20))

        self.horizontalLayout.addWidget(self.pushRUN)

        self.pushEVOKED = QPushButton(self.frameControl)
        self.pushEVOKED.setObjectName(u"pushEVOKED")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.pushEVOKED.sizePolicy().hasHeightForWidth())
        self.pushEVOKED.setSizePolicy(sizePolicy3)
        self.pushEVOKED.setStyleSheet(u"background-color: rgb(131, 153, 105);\n"
"alternate-background-color: rgb(36, 31, 49);\n"
"color: rgb(0, 0, 0);\n"
"font: 700 10pt \"Arial\";")
        icon2 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.AudioVolumeHigh))
        self.pushEVOKED.setIcon(icon2)

        self.horizontalLayout.addWidget(self.pushEVOKED)

        self.pushNOISE = QPushButton(self.frameControl)
        self.pushNOISE.setObjectName(u"pushNOISE")
        sizePolicy3.setHeightForWidth(self.pushNOISE.sizePolicy().hasHeightForWidth())
        self.pushNOISE.setSizePolicy(sizePolicy3)
        self.pushNOISE.setStyleSheet(u"alternate-background-color: rgb(36, 31, 49);\n"
"background-color: rgb(199, 122, 108);\n"
"color:rgb(0,0,0);\n"
"font: 700 10pt \"Arial\";")
        icon3 = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.AudioVolumeMuted))
        self.pushNOISE.setIcon(icon3)
        self.pushNOISE.setCheckable(False)

        self.horizontalLayout.addWidget(self.pushNOISE)


        self.verticalLayout.addWidget(self.frameControl)

        self.plotWidget = PlotWidget(self.centralwidget)
        self.plotWidget.setObjectName(u"plotWidget")

        self.verticalLayout.addWidget(self.plotWidget)

        self.labelStatus = QLabel(self.centralwidget)
        self.labelStatus.setObjectName(u"labelStatus")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.labelStatus.sizePolicy().hasHeightForWidth())
        self.labelStatus.setSizePolicy(sizePolicy4)

        self.verticalLayout.addWidget(self.labelStatus)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 864, 23))
        self.menuFile = QMenu(self.menubar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuOption = QMenu(self.menubar)
        self.menuOption.setObjectName(u"menuOption")
        self.menuMode = QMenu(self.menuOption)
        self.menuMode.setObjectName(u"menuMode")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuOption.menuAction())
        self.menuFile.addAction(self.actionSave)
        self.menuOption.addAction(self.actionTone_burst)
        self.menuOption.addAction(self.menuMode.menuAction())
        self.menuMode.addAction(self.actionCABRA_Default)
        self.menuMode.addAction(self.actionSimulator)
        self.menuMode.addAction(self.actionGoated)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"CABRA", None))
        self.actionSave.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.actionNumber_of_clicks.setText(QCoreApplication.translate("MainWindow", u"Number of clicks", None))
        self.actionTone_burst.setText(QCoreApplication.translate("MainWindow", u"Tone burst setup", None))
        self.actionCABRA_Default.setText(QCoreApplication.translate("MainWindow", u"CABRA [Default]", None))
        self.actionSimulator.setText(QCoreApplication.translate("MainWindow", u"Simulator", None))
        self.actionGoated.setText(QCoreApplication.translate("MainWindow", u"Goated", None))
        self.labelName.setText(QCoreApplication.translate("MainWindow", u"Name:", None))
        self.labelDOB.setText(QCoreApplication.translate("MainWindow", u"DOB:", None))
        self.labelID.setText(QCoreApplication.translate("MainWindow", u"ID:", None))
        self.labelFreq.setText(QCoreApplication.translate("MainWindow", u"Frequency [Hz]:", None))
        self.comboBoxFreq.setItemText(0, QCoreApplication.translate("MainWindow", u"250", None))
        self.comboBoxFreq.setItemText(1, QCoreApplication.translate("MainWindow", u"500", None))
        self.comboBoxFreq.setItemText(2, QCoreApplication.translate("MainWindow", u"1000", None))
        self.comboBoxFreq.setItemText(3, QCoreApplication.translate("MainWindow", u"2000", None))
        self.comboBoxFreq.setItemText(4, QCoreApplication.translate("MainWindow", u"4000", None))
        self.comboBoxFreq.setItemText(5, QCoreApplication.translate("MainWindow", u"8000", None))

        self.radioLeftEAR.setText(QCoreApplication.translate("MainWindow", u"Left ear", None))
        self.radioRightEAR.setText(QCoreApplication.translate("MainWindow", u"Right ear", None))
        self.checkBone.setText(QCoreApplication.translate("MainWindow", u"Bone conduction", None))
        self.pushCABRASweep.setText(QCoreApplication.translate("MainWindow", u" CABRA Sweep", None))
        self.pushRUN.setText(QCoreApplication.translate("MainWindow", u"REC", None))
        self.pushEVOKED.setText(QCoreApplication.translate("MainWindow", u"HEARD", None))
        self.pushNOISE.setText(QCoreApplication.translate("MainWindow", u"  NOT\n"
"HEARD", None))
        self.labelStatus.setText(QCoreApplication.translate("MainWindow", u"Set the parameters for the experiment, and hit RUN", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuOption.setTitle(QCoreApplication.translate("MainWindow", u"Options", None))
        self.menuMode.setTitle(QCoreApplication.translate("MainWindow", u"Mode...", None))
    # retranslateUi

