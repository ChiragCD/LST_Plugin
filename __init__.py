## This function is called upon import (loading) by QGIS

"""
Inputs:
    iface - qgis.gui.QgisInterface
Returns:
    unnamed - LSTplugin
"""

def classFactory(iface):
    from .mainLST import LSTplugin
    return LSTplugin(iface)
