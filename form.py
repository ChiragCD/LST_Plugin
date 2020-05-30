from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PIL import Image
import numpy

fileNames = set()
filePaths = set()
resultStates = []
checkboxes = []
band = [0, 0, 0]


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("App")

        layout = QVBoxLayout()

        # input file option
        label = QLabel()
        label.setText("Input file")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # input bands
        for i in (4, 5, 10):
            layout.addWidget(self.browseFile(i))

        # checkbox for various outputs

        toacheckbox = QCheckBox("TOA Spectral Radiance")
        layout.addWidget(toacheckbox)
        checkboxes.append(toacheckbox)
        ndvicheckbox = QCheckBox("NDVI")
        layout.addWidget(ndvicheckbox)
        checkboxes.append(ndvicheckbox)
        vegcheckbox = QCheckBox("Proportion of Vegetation")
        layout.addWidget(vegcheckbox)
        checkboxes.append(vegcheckbox)
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
        print(fp[0])
        pathField.setText(fp[0])
        if not fileNames.__contains__(fp[0]):
            fileNames.add(fp[0])
            filePaths.add((fp[0], num))

    def goFunc(self):
        if len(fileNames) != 3:
            print("All files not specified")
            # show an error
            return

        for box in checkboxes:
            resultStates.append(box.isChecked())

        loadBands(filePaths)
        # show a loader
        #
        #
        #
        #
        # run all the functions here

        # output the data as a file


def loadBands(fp):
    for path in fp:
        im = Image.open(path[0])
        band[path[1] % 4] = numpy.array(im)
    print(band)
