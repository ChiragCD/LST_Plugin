from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *
from qgis.PyQt.QtCore import *

# neccesary
from . import form

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

        print("Running")

        window = form.MainWindow()
        window.show()
