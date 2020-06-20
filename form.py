from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *

from qgis.core import *

import time

from . import mainLST, procedures


class MainWindow(QMainWindow):

    """
    Class in charge of all user interfacing
    """

    def __init__(self, iface):

        """
        Generate the pyqt5 user interface
        """

        self.iface = iface
        super(MainWindow, self).__init__()

        self.filePaths = dict()
        self.running = False
        self.error = None
        self.checkboxes = []
        self.layerInfor = dict()
        layers = iface.mapCanvas().layers()
        for layer in layers:
            self.layerInfor[layer.name()] = layer.dataProvider().dataSourceUri()

        self.setWindowTitle("Land Surface Temperature")

        self.layout = QVBoxLayout()

        # input file option
        label = QLabel()
        label.setText("Input Bands")
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        # input bands
        for band in ("Red", "Near-IR", "Thermal-IR"):
            self.layout.addWidget(self.browseFile(band))

        # select satellite type
        dtwidget = QWidget()
        hlayout = QHBoxLayout()
        label = QLabel("Select Satellite Type")
        lst5button = QRadioButton("Landsat5")
        lst8button = QRadioButton("Landsat8")
        lst8button.setChecked(True)
        hlayout.addWidget(label)
        hlayout.addWidget(lst5button)
        hlayout.addWidget(lst8button)
        self.radios = [lst5button, lst8button]
        dtwidget.setLayout(hlayout)
        self.layout.addWidget(dtwidget)

        label = QLabel("OR")
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        # select a compressed file
        zipLayout = QHBoxLayout()
        pathField = QLineEdit()
        pathField.setText("Compressed File")
        zipLayout.addWidget(pathField)
        selband = QPushButton()
        selband.setText("Select Compressed File")
        selband.clicked.connect(lambda: self.getFiles(pathField, "zip"))
        zipLayout.addWidget(selband)
        filesel = QWidget()
        filesel.setLayout(zipLayout)
        self.layout.addWidget(filesel)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(h_line)

        # select shapefile, optional

        label = QLabel("Optional - Limit calculations to shapefile")
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        self.layout.addWidget(self.browseFile("Shape"))

        h_line = QFrame()
        h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(h_line)

        # select output types lable
        label = QLabel()
        label.setText("Select Outputs")
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        # checkbox for various outputs
        self.addCheckBox("TOA Spectral Radiance")
        self.addCheckBox("At Sensor Brightness Temperature")
        self.addCheckBox("NDVI")
        self.addCheckBox("Proportion of Vegetation")
        self.addCheckBox("Land Surface Emissivity")
        self.addCheckBox("Land Surface Temperature", defaultChecked=True)

        # horizontal line seperator
        h_line = QFrame()
        h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(h_line)

        # add option to specify file output destination
        label = QLabel("Optional - Set Destination Folder for Outputs")
        label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(label)

        sfoldlayout = QHBoxLayout()
        pathFold = QLineEdit()
        pathFold.setText("Output Folder Destination")
        sfoldlayout.addWidget(pathFold)
        selfold = QPushButton()
        selfold.setText("Select Output Destination")
        selfold.clicked.connect(lambda: self.getFolder(pathFold, "output"))
        sfoldlayout.addWidget(selfold)
        filesel = QWidget()
        filesel.setLayout(sfoldlayout)
        self.layout.addWidget(filesel)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(h_line)

        # go button
        goButton = QPushButton("Go")
        goButton.clicked.connect(self.goFunc)
        self.layout.addWidget(goButton)

        h_line = QFrame()
        h_line.setFrameShape(QFrame.HLine)
        self.layout.addWidget(h_line)

        mainWidget = QWidget()
        mainWidget.setLayout(self.layout)
        self.setCentralWidget(mainWidget)

        # status bar for status updates
        self.status = QStatusBar()
        self.setStatusBar(self.status)

    def browseFile(self, band):

        """
        Select a file for a particular band
        """

        filesel = QWidget()
        hlayout = QHBoxLayout()

        pathField = QLineEdit()
        pathField.setText(band)
        hlayout.addWidget(pathField)

        selLayer = QComboBox()
        selLayer.addItem("Select a Layer")
        self.layerInfor["Select a Layer"] = "Select a layer"

        for name in self.layerInfor:
            selLayer.addItem(name)
        selLayer.activated.connect(
            lambda: self.getLayers(
                pathField, self.layerInfor[selLayer.currentText()], band
            )
        )
        hlayout.addWidget(selLayer)
        hlayout.addWidget(QLabel("Or"))

        selband = QPushButton()
        selband.setText("Select a File")
        selband.clicked.connect(lambda: self.getFiles(pathField, band))
        hlayout.addWidget(selband)
        filesel.setLayout(hlayout)
        return filesel

    def getLayers(self, pathField, addr, band):

        """
        Get filepath of layer selected
        """

        if addr == "Select a layer":
            return
        if not (addr.lower().endswith(".tif")) and not (addr.lower().endswith(".shp")):
            lastmatch = addr.lower().rfind(".tif")
            if lastmatch == -1:
                lastmatch = addr.lower().rfind(".shp")
            addr = addr[: lastmatch + 4]
        pathField.setText(addr)
        self.filePaths[band] = addr

    def getFiles(self, pathField, band):

        """
        Get filepath of file selected
        """

        fp = QFileDialog.getOpenFileName()
        if not (fp[0]):
            return
        pathField.setText(fp[0])
        self.filePaths[band] = fp[0]

    def getFolder(self, pathField, name):
        """
        Get path of foleder selected
        """

        fp = QFileDialog.getExistingDirectory()
        if not fp:
            return
        pathField.setText(fp)
        self.filePaths[name] = fp

    def goFunc(self):

        """
        Called when the go button is pressed
        Begins the processing
        """

        if(self.running):
            self.showError("Busy, please wait till end of execution")
            return
        self.running = True

        self.resultStates = []
        for box in self.checkboxes:
            self.resultStates.append((box[0].isChecked(), box[1].text() or box[0].text()))

        satType = (
            self.radios[0].text()
            if self.radios[0].isChecked()
            else self.radios[1].text()
        )

        self.start_time = time.time()

        self.virtualTask = mainLST.CarrierTask(self)
        self.virtualTask.progressChanged.connect(self.update_progress)
        self.preproc = mainLST.preprocess(self.filePaths, self.resultStates, satType, self.virtualTask)
        self.proc = procedures.processor(self.preproc, self.resultStates, self.virtualTask)
        self.postproc = mainLST.postprocess(self.proc, self.virtualTask)
        self.virtualTask.addSubTask(self.preproc)
        self.virtualTask.addSubTask(self.proc, [self.preproc])
        self.virtualTask.addSubTask(self.postproc, [self.proc])
        QgsApplication.taskManager().addTask(self.virtualTask)

        return
    
    def update_progress(self):
        
        self.showStatus(self.virtualTask.notification)
    
    def endRun(self):

        if(self.virtualTask.progress() != 100):
            self.virtualTask.cancel()
        else:
            mainLST.displayOnScreen(self.resultStates, self.postproc.filer)
        time_taken = int(time.time() - self.start_time)
        self.showStatus("Finished, process time - " + str(time_taken) + " seconds")
        self.running = False

    def addCheckBox(self, text, defaultChecked=False):

        """
        Add a checkbox (specifically for listing output types needed)
        and a line edit to specify file name for output
        """

        widget = QWidget()
        localLayout = QHBoxLayout()

        lstcheckbox = QCheckBox(text)
        lstcheckbox.setChecked(defaultChecked)
        lstcheckbox.setMinimumWidth(250)
        localLayout.addWidget(lstcheckbox)

        fname = QLineEdit()
        fname.setFixedWidth(200)
        fname.setPlaceholderText("File Name (Optional)")
        localLayout.addWidget(fname)

        widget.setLayout(localLayout)

        self.layout.addWidget(widget)
        self.checkboxes.append((lstcheckbox, fname))

    def showStatus(self, text):

        """
        Show a message on the status bar
        """

        text = str(text)
        self.status.showMessage(text, 60000)

    def showError(self, err):

        """
        Raise an error as a message box
        """

        self.showStatus(err)
        messageBox = QMessageBox()
        messageBox.critical(None, "", err)

    def closeEvent(self, event):

        if(self.running):
            self.endRun()