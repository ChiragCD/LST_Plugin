from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from PIL import Image
from zipfile import ZipFile
import numpy

from . import procedures

# import procedures
import os

fileNames = set()
filePaths = set()
resultStates = []
checkboxes = []
band = [0, 0, 0]
radios = []


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("App")

        layout = QVBoxLayout()

        # input file option
        label = QLabel()
        label.setText("Input bands")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # input bands
        for i in (4, 5, 10):
            layout.addWidget(self.browseFile(i))

        # select data type
        dtwidget = QWidget()
        hlayout = QHBoxLayout()

        label = QLabel("Select Data type")
        hlayout.addWidget(label)

        lst5button = QRadioButton("Landsat5")
        radios.append(lst5button)
        hlayout.addWidget(lst5button)

        lst8button = QRadioButton("Landsat8")
        lst8button.setChecked(True)
        radios.append(lst8button)
        hlayout.addWidget(lst8button)

        dtwidget.setLayout(hlayout)
        layout.addWidget(dtwidget)

        # select output types lable
        label = QLabel()
        label.setText("Select Output types")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # checkbox for various outputs
        toacheckbox = QCheckBox("TOA Spectral Radiance")
        layout.addWidget(toacheckbox)
        checkboxes.append(toacheckbox)

        btcheckbox = QCheckBox("At Sensor Brightness Temperature")
        layout.addWidget(btcheckbox)
        checkboxes.append(btcheckbox)

        ndvicheckbox = QCheckBox("NDVI")
        layout.addWidget(ndvicheckbox)
        checkboxes.append(ndvicheckbox)

        pvcheckbox = QCheckBox("Proportion of Vegetation")
        layout.addWidget(pvcheckbox)
        checkboxes.append(pvcheckbox)

        lsecheckbox = QCheckBox("Land Surface Emissivity")
        layout.addWidget(lsecheckbox)
        checkboxes.append(lsecheckbox)

        lstcheckbox = QCheckBox("LST")
        lstcheckbox.setChecked(True)
        layout.addWidget(lstcheckbox)
        checkboxes.append(lstcheckbox)
        # check through ischecked()

        # go button
        goButton = QPushButton("Go")
        goButton.clicked.connect(self.goFunc)
        layout.addWidget(goButton)

        mainWidget = QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

    def browseFile(self, num):
        filesel = QWidget()
        hlayout = QHBoxLayout()

        pathField = QLineEdit()
        pathField.setText("...")
        hlayout.addWidget(pathField)

        selband = QPushButton()
        selband.setText("Select Band " + str(num))
        selband.clicked.connect(lambda: self.getFiles(pathField, num))
        hlayout.addWidget(selband)
        filesel.setLayout(hlayout)
        return filesel

    def getFiles(self, pathField, num):
        fp = QFileDialog.getOpenFileName()
        # print(fp[0])
        pathField.setText(fp[0])
        if not fileNames.__contains__(fp[0]):
            fileNames.add(fp[0])
            filePaths.add((fp[0], num))

    def goFunc(self):

        if len(fileNames) != 3:
            print("An error occured")
            return

        for box in checkboxes:
            resultStates.append(box.isChecked())

        satType = radios[0].text() if radios[0].isChecked() else radios[1].text()

        loadBands(filePaths)

        toa, bt, ndvi, pv, lse, lst = procedures.process(
            band[0], band[1], band[2], satType
        )

        # os.mkdir("LSTPluginResults")
        os.makedirs("~/LSTPluginResults")
        print(resultStates[5])

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
        print("All done")

        self.close()
        # output the data as a file


def loadBands(fp):
    for path in fp:
        im = Image.open(path[0])
        band[path[1] % 4] = numpy.array(im, dtype = numpy.int16)
