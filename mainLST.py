from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.utils import iface
from qgis.core import *

import time

from . import resources, form, procedures, fileio

## Main class: LSTplugin


class LandSurfaceTemperature(object):

    """Main plugin object"""

    def __init__(self, iface):

        """
        Initialiser
        """

        self.iface = iface

    def initGui(self):

        """
        Called when loaded
        Adds plugin option to menus
        """

        self.action = QAction(
            icon=QIcon(":plugins/LandSurfaceTemperature/icon.png"),
            text="Land Surface Temperature",
            parent=self.iface.mainWindow(),
        )
        self.action.triggered.connect(self.run)

        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("Land Surface Temperature", self.action)

    def unload(self):

        """
        Called when plugin is unloaded
        Removes option from interface
        """

        self.iface.removePluginMenu("Land Surface Temperature", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):

        """
        Called when plugin asked to run
        Starts a UI instance, defined in form.py
        """

        window = form.MainWindow(self.iface)
        window.show()


def displayOnScreen(resultStates, resultNames, filer):

    """
    Display generated outputs as layers on the interface
    """

    for i in range(6):
        if resultStates[i][0]:
            iface.addRasterLayer(
                filer.generateFileName(resultNames[i], "TIF"), resultNames[i]
            )

class preprocess(QgsTask):

    def __init__(self, filePaths, resultStates, satType, parent):

        QgsTask.__init__(self, "Inputs Processor")

        self.filePaths = filePaths
        self.resultStates = resultStates
        self.satType = satType
        self.parent = parent

        self.bands = dict()
        self.filer = None
        self.error = None

    def run(self):

        """
        Main processing element, called every time Go is pressed
        """

        self.filer = fileio.fileHandler()
        # processor = procedures.processor()

        self.setProgress(10)

        if("output" in self.filePaths):
            self.filer.prepareOutFolder(self.filePaths["output"])
            del self.filePaths["output"]

        if "zip" in self.filePaths:
            self.setProgress(12)
            self.bands = self.filer.loadZip(self.filePaths)
            self.satType = self.bands["sat_type"]
            del self.bands["sat_type"]
        else:
            self.bands = self.filer.loadBands(self.filePaths)
        if self.bands["Error"]:
            self.error = self.bands["Error"]
            return True
        del self.bands["Error"]
        return True
    
    def cancel(self):

        super().cancel()
    
    def finished(self, results = None):

        if(not(results)):
            self.error = "Pre-Processing Crashed"
        if(self.error):
            self.parent.setError(self.error)

class postprocess(QgsTask):

    def __init__(self, proc_object, parent):

        QgsTask.__init__(self, "Outputs Processor")

        self.proc_object = proc_object
        self.parent = parent
        self.error = None
    
    def run(self):

        self.filer = self.proc_object.filer

        self.filer.saveAll(self.proc_object.results)
        self.setProgress(90)
        return True

        resultNames = []
        for res in resultStates:
            resultNames.append(res[1])

        if displayResults:
            displayOnScreen(resultStates, resultNames, filer)

        form.showStatus("Finished")
        self.setProgress(99)
    
    def cancel(self):

        super().cancel()

    def finished(self, results = None):
        if(not(results)):
            self.error = "Post-Processing Crashed"
        if(self.error):
            self.parent.setError(self.error)
        self.parent.done = True

class CarrierTask(QgsTask):

    def __init__(self, form):
        QgsTask.__init__(self, "Carrier for other plugin tasks")
        self.form = form
        self.error = None
        self.done = False
    
    def run(self):
        while(not(self.done)):
            if(self.error):
                return True
            time.sleep(0.1)
        return True
    
    def cancel(self):

        super().cancel()
    
    def finished(self, result = None):

        if(not(result)):
            self.error = "Crash"        
        # print("Finishing", self.error)
        if(self.error):
            self.form.showError(self.error)
        self.form.endRun()
    
    def setError(self, msg):

        if(self.error):
            return
        self.error = msg