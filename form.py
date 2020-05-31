import qgis
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from PIL import Image
from zipfile import ZipFile
import numpy

from . import procedures, fileio

# import procedures
import os

class MainWindow(QMainWindow):

    def addCheckBox(self, text, defaultChecked = False):

        lstcheckbox = QCheckBox(text)
        lstcheckbox.setChecked(defaultChecked)
        self.layout.addWidget(lstcheckbox)
        self.checkboxes.append(lstcheckbox)

    def __init__(self):

        super(MainWindow, self).__init__()

        self.logfile = open("logfile.txt", "w")

        self.filePaths = dict()
        self.checkboxes = []

        self.setWindowTitle("App")

        self.layout = QVBoxLayout()

        # input file option
        label = QLabel()
        label.setText("Input bands")
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        # input bands
        for band in ("Red", "Near-IR", "Thermal-IR"):
            self.layout.addWidget(self.browseFile(band))

        # select data type
        dtwidget = QWidget()
        hlayout = QHBoxLayout()
        label = QLabel("Select Data type")
        lst5button = QRadioButton("Landsat5")
        lst8button = QRadioButton("Landsat8")
        lst8button.setChecked(True)
        hlayout.addWidget(label)
        hlayout.addWidget(lst5button)
        hlayout.addWidget(lst8button)
        self.radios = [lst5button, lst8button]
        dtwidget.setLayout(hlayout)
        self.layout.addWidget(dtwidget)

        # select output types lable
        label = QLabel()
        label.setText("Select Output types")
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        # checkbox for various outputs
        self.addCheckBox("TOA Spectral Radiance")
        self.addCheckBox("At Sensor Brightness Temperature")
        self.addCheckBox("NDVI")
        self.addCheckBox("Proportion of Vegetation")
        self.addCheckBox("Land Surface Emissivity")
        self.addCheckBox("LST", defaultChecked = True)
        # check through ischecked()

        # go button
        goButton = QPushButton("Go")
        goButton.clicked.connect(self.goFunc)
        self.layout.addWidget(goButton)

        mainWidget = QWidget()
        mainWidget.setLayout(self.layout)
        self.setCentralWidget(mainWidget)

    def browseFile(self, band):
        filesel = QWidget()
        hlayout = QHBoxLayout()

        pathField = QLineEdit()
        pathField.setText("...")
        hlayout.addWidget(pathField)

        selband = QPushButton()
        selband.setText("Select " + band + " Band file")
        selband.clicked.connect(lambda: self.getFiles(pathField, band))
        hlayout.addWidget(selband)
        filesel.setLayout(hlayout)
        return filesel

    def getFiles(self, pathField, band):
        fp = QFileDialog.getOpenFileName()
        pathField.setText(fp[0])
        self.filePaths[band] = fp[0]

    def goFunc(self):

        if len(self.filePaths) != 3:
            self.logfile.write("An error occured\n" + str(self.filePaths))
            qgis.core.QgsMessageLog.logMessage("Your plugin code has been executed correctly" + str(self.filePaths))
            self.logfile.close()
            self.close()
            return

        self.logfile.write("goFunc entered successfully\n")
        self.logfile.flush()

        resultStates = []
        for box in self.checkboxes:
            resultStates.append(box.isChecked())

        satType = self.radios[0].text() if self.radios[0].isChecked() else self.radios[1].text()

        band = fileio.loadBands(self.filePaths)

        self.logfile.write("filePaths loaded\n")
        self.logfile.flush()

        toa, bt, ndvi, pv, lse, lst = procedures.process(
            band["Red"], band["Near-IR"], band["Thermal-IR"], satType
        )

        self.logfile.write("Processing complete\n")
        self.logfile.flush()

        # os.mkdir("LSTPluginResults")
        os.makedirs("~/LSTPluginResults")

        # zipObj = ZipFile.open("results.zip", "w")

        if resultStates[0]:
            toaIm = Image.fromarray(toa)
            toaIm.save("~/LSTPluginResults/TOA.tiff")
        if resultStates[1]:
            btIm = Image.fromarray(bt)
            btIm.save("~/LSTPluginResults/BT.tiff")
        if resultStates[2]:
            ndviIm = Image.fromarray(ndvi)
            ndviIm.save("~/LSTPluginResults/NDVI.tiff")
        if resultStates[3]:
            pvIm = Image.fromarray(pv)
            pvIm.save("~/LSTPluginResults/PV.tiff")
        if resultStates[4]:
            lseIm = Image.fromarray(lse)
            lseIm.save("~/LSTPluginResults/LSE.tiff")
        if resultStates[5]:
            lstIm = Image.fromarray(lst)
            lstIm.save("~/LSTPluginResults/LST.tiff")

        self.logfile.write("All done\n")
        self.logfile.flush()

        self.logfile.close()
        self.close()
        # output the data as a file


