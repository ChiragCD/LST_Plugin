## Main class: mainLST

class mainLST(object):

"""
Initialiser
Inputs:
    iface - qgis.gui.QgisInterface
Outputs:
    mainLST object (implicitly)
"""

    def __init__(self, iface):

        self.iface = iface

"""
Called when loaded
"""

    def initGui(self):

        self.action = QAction(
                icon=QIcon(":/plugins/LST_Plugin/icon.png"),
                text = "LST plugin",
                parent = self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        ## Add to interface
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("LST plugin", self.action)

"""
Called when unloaded
"""

    def unload(self):

        self.iface.removePluginMenu("LST plugin", self.action)
        self.iface.removeToolBarIcon(self.action)

"""
Called when plugin asked to run
"""

    def run(self):

        print("Running")
