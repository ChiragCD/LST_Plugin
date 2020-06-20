import numpy as np
from qgis.core import *


class processor(QgsTask):

    """
    Called for numpy array manipulation
    """

    def __init__(self, input_object, required, parent):

        """
        Initializes all numpy arrays
        """

        QgsTask.__init__(self, "Processing Task")
        self.setProgress(29.0)

        self.input_object = input_object
        self.required = required
        self.parent = parent

        self.r = np.array([])
        self.nir = np.array([])
        self.tir = np.array([])

        self.toa = np.array([])
        self.bt = np.array([])
        self.ndvi = np.array([])
        self.pv = np.array([])
        self.lse = np.array([])
        self.lst = np.array([])

        self.error = None
        self.results = dict()

    def calc_TOA(self):

        """
        Calculates Top Of Atmosphere Radiance
        """

        if self.toa.size:
            return
        if not (self.tir.size):
            return "Thermal-IR data missing"

        data = {
            "Landsat8": {
                "mul": 0.0003342,
                "add": -0.19,
            },  ##-0.19 = 0.1 - 0.29 (landsat 8 band 10 correction)
            "Landsat5": {"mul": 0.055375, "add": 1.18243},
        }
        self.setProgress(30)
        self.toa = (self.tir * data[self.sat_type]["mul"]) + data[self.sat_type]["add"]

    def calc_BT(self):

        """
        Calculates at-sensor Brightness Temperature
        """

        if self.bt.size:
            return

        error = self.calc_TOA()
        if error:
            return error

        data = {
            "Landsat8": {"K1": 774.8853, "K2": 1321.0789},
            "Landsat5": {"K1": 607.76, "K2": 1260.56},
        }
        self.setProgress(31)
        self.bt = (
            data[self.sat_type]["K2"]
            / np.log((data[self.sat_type]["K1"] / self.toa) + 1)
        ) - 273.15

    def calc_NDVI(self):

        """
        Calculates NDVI values (Normalized Difference Vegetation Index)
        """

        if self.ndvi.size:
            return

        if not (self.nir.size) and not (self.r.size):
            return "Red and Near-IR data missing"
        if not (self.nir.size):
            return "Near-IR data missing"
        if not (self.r.size):
            return "Red data missing"

        self.setProgress(32)
        self.ndvi = (self.nir - self.r) / (self.nir + self.r)

    def calc_PV(self):

        """
        Calculates proportion of vegetation
        """

        if self.pv.size:
            return

        error = self.calc_NDVI()
        if error:
            return error

        data = {"ndvi_soil": 0.2, "ndvi_vegetation": 0.5}

        scale = data["ndvi_vegetation"] - data["ndvi_soil"]
        offset = data["ndvi_soil"] / scale

        self.setProgress(33)
        self.pv = (self.ndvi * scale) - offset
        self.setProgress(34)
        self.pv[self.ndvi < 0.2] = 0
        self.pv[self.ndvi > 0.5] = 1
        self.setProgress(35)
        self.pv **= 2

    def calc_LSE(self):

        """
        Calculates Land Surface Emmissivity
        """

        if self.lse.size:
            return
        error = self.calc_PV()
        if error:
            return error

        data = {
            "water_emissivity": 0.991,
            "soil_emissivity": 0.996,
            "vegetation_emissivity": 0.973,
        }

        self.setProgress(36)

        self.lse = np.full(self.ndvi.shape, np.nan)
        self.lse[self.ndvi < 0] = data["water_emissivity"]
        self.lse[np.logical_and(self.ndvi >= 0, self.ndvi < 0.2)] = data[
            "soil_emissivity"
        ]
        self.setProgress(37)
        self.lse[np.logical_and(self.ndvi >= 0.2, self.ndvi < 0.5)] = data[
            "soil_emissivity"
        ] + self.pv[np.logical_and(self.ndvi >= 0.2, self.ndvi < 0.5)] * (
            data["vegetation_emissivity"] - data["soil_emissivity"]
        )
        self.setProgress(38)
        self.lse[self.ndvi >= 0.5] = data["vegetation_emissivity"]

    def calc_LST(self):

        """
        Calculates Land Surface Temperature
        """

        if self.lst.size:
            return
        error = self.calc_BT()
        if error:
            return error
        error = self.calc_LSE()
        if error:
            return error

        data = {"lambda": 0.00115, "rho": 1.4388}  ##Verify values, only ratio important
        self.setProgress(39)
        self.lst = self.bt / (
            1 + (data["lambda"] * self.bt / data["rho"]) * np.log(self.lse)
        )

    def getBand(self, bandName):

        """
        Gets individual bands for dict of bands
        Masks '0' values with numpy nan
        """

        if bandName in self.bands:
            band = self.bands[bandName]
            band[np.logical_not(self.mask)] = np.nan
            return band
        else:
            return np.array([])

    def run (self):

        """
        Only this function should be accessed from outside this file
        Inputs:
            bands - dict of numpy arrays, "Red", "Near-IR", "Thermal-IR" are the relevant keys
            sat_type - either "Landsat8" or "Landsat5"
            required - array of tuples of length 6, contains boolean and the name associated with layer in tuple
                        [toa, bt, ndvi, pv, lse, lst] in order.
            form - user interfacing element
        Returns:
            A dict of numpy arrays, with a key "Error" holding error message, if any
        """

        # self.__init__(self.input_object, self.required, self.parent)
        self.bands = self.input_object.bands
        self.sat_type = self.input_object.satType
        self.filer = self.input_object.filer
        
        shape = np.array([])

        if not (list(self.bands.values())):
            self.error = "Files missing"
            return True
        if "Shape" in self.bands:
            shape = self.bands["Shape"]
            del self.bands["Shape"]
        tempshape = list(self.bands.values())[0].shape
        self.mask = np.full(tempshape, True)
        if shape.size:
            self.mask[shape == 1] = False
        for layer in list(self.bands.values()):
            self.mask[layer == 0] = False
        if(not(np.any(self.mask))):
            self.error = "Entire image masked - please check shapefile"
            return True

        self.r = self.getBand("Red")
        self.nir = self.getBand("Near-IR")
        self.tir = self.getBand("Thermal-IR")

        toa, bt, ndvi, pv, lse, lst = [res for res in self.required]

        if (not(self.error) and toa[0]):
            self.error = self.calc_TOA()
            self.results[toa[1]] = self.toa
        if (not(self.error) and bt[0]):
            self.error = self.calc_BT()
            self.results[bt[1]] = self.bt
        if (not(self.error) and ndvi[0]):
            self.error = self.calc_NDVI()
            self.results[ndvi[1]] = self.ndvi
        if (not(self.error) and pv[0]):
            self.error = self.calc_PV()
            self.results[pv[1]] = self.pv
        if (not(self.error) and lse[0]):
            self.error = self.calc_LSE()
            self.results[lse[1]] = self.lse
        if (not(self.error) and lst[0]):
            self.error = self.calc_LST()
            self.results[lst[1]] = self.lst
        return True
    
    def finished(self, result = None):

        print("Ending proc")
        self.setProgress(100)
        if(not(result)):
            self.error = "Calculations Crash"
        if(self.error):
            self.parent.setError(self.error)
        print("Error", self.error)