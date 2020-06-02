import numpy as np

class processor(object):

    def __init__(self):

        self.sat_type = None

        self.r = np.array([])
        self.nir = np.array([])
        self.tir = np.array([])

        self.toa = np.array([])
        self.bt = np.array([])
        self.ndvi = np.array([])
        self.pv = np.array([])
        self.lse = np.array([])
        self.lst = np.array([])

    def calc_TOA(self):

        """
        Calculates Top Of Atmosphere Radiance
        Inputs:
            tir - numpy array
        Returns:
            toa - numpy array
        """

        if(self.toa.size):
            return
        if(not(self.tir.size)):
            return "Thermal-IR data missing"

        data = {
            "Landsat8": {
                "mul": 0.0003342,
                "add": -0.19,
            },  ##-0.19 = 0.1 - 0.29 (landsat 8 band 10 correction)
            "Landsat5": {"mul": 0.055375, "add": 1.18243},
        }
        self.toa = (self.tir * data[self.sat_type]["mul"]) + data[self.sat_type]["add"]
        print("Calculated TOA")


    def calc_BT(self):

        """
        Calculates at-sensor Brightness Temperature
        Inputs:
            toa - numpy array
        Returns:
            bt - numpy array
        """

        if(self.bt.size):
            return

        error = self.calc_TOA()
        if(error):
            return error

        data = {
            "Landsat8": {"K1": 774.8853, "K2" :1321.0789},
            "Landsat5": {"K1": 607.76, "K2": 1260.56},
        }
        self.bt = (data[self.sat_type]["K2"] / np.log((data[self.sat_type]["K1"] / self.toa) + 1)) - 273.15
        print("Calculated BT")


    def calc_NDVI(self):

        """
        Calculates NDVI values
        Inputs:
            nir, r - numpy arrays
        Returns:
            ndvi - numpy array
        """

        if(self.ndvi.size):
            return

        if(not(self.nir.size) and not(self.r.size)):
            return "Red and Near-IR data missing"
        if(not(self.nir.size)):
            return "Near-IR data missing"
        if(not(self.r.size)):
            return "Red data missing"

        self.ndvi = (self.nir - self.r) / (self.nir + self.r)
        print("Calculated NDVI")


    def calc_PV(self):

        """
        Calculates proportion of vegetation
        Inputs:
            ndvi - numpy array
        Returns:
            pv - numpy array
        """

        if(self.pv.size):
            return

        error = self.calc_NDVI()
        if(error):
            return error

        data = {"ndvi_soil": 0.2, "ndvi_vegetation": 0.5}
        self.pv = np.square(
            (self.ndvi - data["ndvi_soil"]) / (data["ndvi_vegetation"] - data["ndvi_soil"])
        )
        print("Calculated PV")


    def calc_LSE(self):

        """
        Calculates Land Surface Emmissivity
        Inputs:
            ndvi, pv - numpy array
        Returns:
            lse - numpy array
        """

        if(self.lse.size):
            return
        error = self.calc_PV()
        if(error):
            return error

        data = {
            "water_emissivity": 0.991,
            "soil_emissivity": 0.996,
            "vegetation_emissivity": 0.973,
        }
        self.lse = np.full(self.ndvi.shape, np.nan)
        self.lse[self.ndvi < 0] = data["water_emissivity"]
        self.lse[np.logical_and(self.ndvi >= 0, self.ndvi < 0.2)] = data["soil_emissivity"]
        self.lse[np.logical_and(self.ndvi >= 0.2, self.ndvi < 0.5)] = (
                data["soil_emissivity"] + \
                self.pv[np.logical_and(self.ndvi >= 0.2, self.ndvi < 0.5)] * \
                (data["vegetation_emissivity"] - data["soil_emissivity"])
                )
        self.lse[self.ndvi >= 0.5] = data["vegetation_emissivity"]
        print("Calculated LSE")


    def calc_LST(self):

        """
        Calculates Land Surface Temperature
        Inputs:
            bt, lse - numpy array
        Returns:
            lst - numpy array
        """

        if(self.lst.size):
            return
        error = self.calc_BT()
        if(error):
            return error
        error = self.calc_LSE()
        if(error):
            return error

        data = {"lambda": 0.00115, "rho": 1.4388}  ##Verify values, only ratio important
        self.lst = self.bt / (1 + (data["lambda"] * self.bt / data["rho"]) * np.log(self.lse))
        print("Calculated LST")

    @staticmethod
    def getBand(bandName, bands, mask):
        if(bandName in bands):
            band = bands[bandName]
            band[np.logical_not(mask)] = np.nan
            return band
        else:
            return np.array([])

    def process(self, bands, sat_type, required):

        """
        Interfacing function, follows steps and returns all subparts
        Inputs:
            r, nir, tir - numpy arrays
            sat_type - str (either "Landsat8" or "Landsat5")
        Returns:
            toa, bt, ndvi, pv, lse, lst - numpy arrays
        """

        error = None
        results = dict()

        if(not(list(bands.values()))):
            results["Error"] = "Files missing"
            return results
        temp = list(bands.values())[0]
        mask = np.full(temp.shape, True)
        del temp
        for layer in list(bands.values()):
            mask[layer == 0] = False

        self.sat_type = sat_type
        self.r = processor.getBand("Red", bands, mask)
        self.nir = processor.getBand("Near-IR", bands, mask)
        self.tir = processor.getBand("Thermal-IR", bands, mask)

        toa, bt, ndvi, pv, lse, lst = required

        if(toa):
            error = self.calc_TOA()
            results["TOA"] = self.toa
        if(bt):
            error = self.calc_BT()
            results["BT"] = self.bt
        if(ndvi):
            error = self.calc_NDVI()
            results["NDVI"] = self.ndvi
        if(pv):
            error = self.calc_PV()
            results["PV"] = self.pv
        if(lse):
            error = self.calc_LSE()
            results["LSE"] = self.lse
        if(lst):
            error = self.calc_LST()
            results["LST"] = self.lst
        results["Error"] = error
        return results
