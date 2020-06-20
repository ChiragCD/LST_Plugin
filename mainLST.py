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


def displayOnScreen(resultStates, filer):

    """
    Display generated outputs as layers on the interface
    """

    resultNames = []
    for res in resultStates:
        resultNames.append(res[1])

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
        self.parent.updateProgress(0, "0 % Starting, setting optional out folder")

        if("output" in self.filePaths):
            self.filer.prepareOutFolder(self.filePaths["output"])
            del self.filePaths["output"]
        
        self.parent.updateProgress(5, "5 % Loading files")

        if "zip" in self.filePaths:
            self.bands = self.filer.loadZip(self.filePaths)
            self.satType = self.bands["sat_type"]
            del self.bands["sat_type"]
        else:
            self.bands = self.filer.loadBands(self.filePaths)
        
        self.parent.updateProgress(15, "15% Files ready, checking for errors")

        if self.bands["Error"]:
            self.error = self.bands["Error"]
            return True
        del self.bands["Error"]
        return True
    
    def finished(self, results = None):

        if(not(results)):
            self.error = "Aborted"
        if(self.error):
            self.parent.setError(self.error)
        self.parent.updateProgress(20, "20% Starting calculations")

class postprocess(QgsTask):

    def __init__(self, proc_object, parent):

        QgsTask.__init__(self, "Outputs Processor")

        self.proc_object = proc_object
        self.parent = parent
        self.error = None
    
    def run(self):

        self.filer = self.proc_object.filer
        self.filer.saveAll(self.proc_object.results)
        self.parent.updateProgress(94, "94% Files Saved")
        return True

    def finished(self, results = None):

        if(not(results)):
            self.error = "Aborted"
        if(self.error):
            self.parent.setError(self.error)
        self.parent.done = True
        self.parent.updateProgress(95, "95% Finished, Displaying Outputs")

class CarrierTask(QgsTask):

    def __init__(self, form):
        QgsTask.__init__(self, "LST plugin base task")
        self.form = form
        self.error = None
        self.done = False
        self.notification = "If you're still seeing this, something's gone very wrong"
    
    def run(self):
        while(not(self.done) and not(self.error)):
            time.sleep(1)
        return True
    
    def finished(self, result = None):

        self.setProgress(100)
        if(not(result)):
            self.error = "Crash"
        if(self.error):
            self.form.showError(self.error)
        self.form.endRun()
    
    def updateProgress(self, num, text):

        self.notification = text
        self.setProgress(num)
    
    def setError(self, msg):

        if(self.error):
            return
        self.error = msg
        self.done = True
        self.finished(True)