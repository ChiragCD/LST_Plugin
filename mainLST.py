from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *
from qgis.utils import iface

import os

# neccesary
from . import form, procedures, fileio

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
            icon=QIcon(":/plugins/LST_Plugin/icon.png"),
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


def processAll(filePaths, resultStates, satType):

    toa, bt, ndvi, pv, lse, lst = resultStates

    if "Thermal-IR" not in filePaths and (toa or bt or lst):
        return "Thermal-IR file missing"
    if ("Red" not in filePaths or "Near-IR" not in filePaths) and (ndvi or pv or lse or lst):
        if("Red" not in filePaths):
            return "Red file missing"
        if("Near-IR" not in filePaths):
            return "Near-IR file missing"

    band = fileio.loadBands(filePaths)

    outfolder = filePaths["Thermal-IR"]
    outfolder = outfolder[: filePaths["Thermal-IR"].rfind("/")] + "/LSTPluginResults"

    results = procedures.process(
        band["Red"], band["Near-IR"], band["Thermal-IR"], satType
    )

    while os.path.isdir(outfolder):
        if outfolder[-1].isnumeric():
            outfolder = outfolder[:-1] + str(1 + int(outfolder[-1]))
        else:
            outfolder += "1"
    os.makedirs(outfolder)

    resultName = ["TOA", "BT", "NDVI", "PV", "LSE", "LST"]

    for i in range(6):
        if resultStates[i]:
            outfilename = outfolder + "/" + resultName[i] + ".TIF"
            fileio.saveArray(results[i], outfilename)
            iface.addRasterLayer(outfilename, resultName[i])
