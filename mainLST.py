from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.utils import iface

import os

# neccesary
from . import resources, form, procedures, fileio

## Main class: LSTplugin


class LSTplugin(object):

    """Main plugin object"""

    def __init__(self, iface):

        """
        Initialiser
        Inputs:
            iface - qgis.gui.QgisInterface
        Outputs:
            mainLST object (implicitly)
        """

        self.iface = iface

    def initGui(self):

        """
        Called when loaded
        """

        self.action = QAction(
                icon=QIcon(":plugins/LST_Plugin/icon.png"),
            text="LST plugin",
            parent=self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.run)

        ## Add to interface
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("LST plugin", self.action)

    def unload(self):

        """
        Called when unloaded
        """

        self.iface.removePluginMenu("LST plugin", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):

        """
        Called when plugin asked to run
        """

        window = form.MainWindow(self.iface)
        window.show()

def displayOnScreen(resultStates, resultNames, filer):

    for i in range(6):
        if resultStates[i]:
            iface.addRasterLayer(filer.generateFileName(resultNames[i], "TIF"), resultNames[i])

def processAll(form, filePaths, resultStates, satType, displayResults = True):

    form.showStatus("Loading Files")

    filer = fileio.fileHandler()
    processor = procedures.processor()

    if("zip" in filePaths):
        bands = filer.loadZip(filePaths)
        satType = bands["sat_type"]
        del bands["sat_type"]
    else:
        bands = filer.loadBands(filePaths)
    if(bands["Error"]):
        form.showError(bands["Error"])
        return
    del bands["Error"]

    form.showStatus("Processing")

    results = processor.process(bands, satType, resultStates, form)
    if(results["Error"]):
        form.showError(results["Error"])
        return
    del results["Error"]

    form.showStatus("Saving Outputs")

    filer.saveAll(results)

    form.showStatus("Displaying Outputs")

    resultNames = ["TOA", "BT", "NDVI", "PV", "LSE", "LST"]
    if(displayResults):
        displayOnScreen(resultStates, resultNames, filer)

    form.showStatus("Finished")
