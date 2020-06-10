import numpy as np

class processor(object):

    """
    Called for numpy array manipulation
    """

    def __init__(self):

        """
        Initializes all numpy arrays
        """

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

        self.form = None

    def calc_TOA(self):

        """
        Calculates Top Of Atmosphere Radiance
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
            "Landsat5": {"mul": 0.055375, "add": 1.18243}
        }
        self.report("Calculating TOA")
        self.toa = (self.tir * data[self.sat_type]["mul"]) + data[self.sat_type]["add"]


    def calc_BT(self):

        """
        Calculates at-sensor Brightness Temperature
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
        self.report("Calculating BT")
        self.bt = (data[self.sat_type]["K2"] / np.log((data[self.sat_type]["K1"] / self.toa) + 1)) - 273.15


    def calc_NDVI(self):

        """
        Calculates NDVI values (Normalized Difference Vegetation Index)
        """

        if(self.ndvi.size):
            return

        if(not(self.nir.size) and not(self.r.size)):
            return "Red and Near-IR data missing"
        if(not(self.nir.size)):
            return "Near-IR data missing"
        if(not(self.r.size)):
            return "Red data missing"

        self.report("Calculating NDVI")
        self.ndvi = (self.nir - self.r) / (self.nir + self.r)


    def calc_PV(self):

        """
        Calculates proportion of vegetation
        """

        if(self.pv.size):
            return

        error = self.calc_NDVI()
        if(error):
            return error

        data = {"ndvi_soil": 0.2, "ndvi_vegetation": 0.5}

        scale = data["ndvi_vegetation"] - data["ndvi_soil"]
        offset = data["ndvi_soil"] / scale

        self.report("Calculating PV")
        self.pv = (self.ndvi * scale) - offset
        self.pv[self.ndvi < 0.2] = 0
        self.pv[self.ndvi > 0.5] = 1
        self.pv **= 2


    def calc_LSE(self):

        """
        Calculates Land Surface Emmissivity
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

        self.report("Calculating LSE")

        self.lse = np.full(self.ndvi.shape, np.nan)
        self.lse[self.ndvi < 0] = data["water_emissivity"]
        self.lse[np.logical_and(self.ndvi >= 0, self.ndvi < 0.2)] = data["soil_emissivity"]
        self.lse[np.logical_and(self.ndvi >= 0.2, self.ndvi < 0.5)] = (
                data["soil_emissivity"] + \
                self.pv[np.logical_and(self.ndvi >= 0.2, self.ndvi < 0.5)] * \
                (data["vegetation_emissivity"] - data["soil_emissivity"])
                )
        self.lse[self.ndvi >= 0.5] = data["vegetation_emissivity"]


    def calc_LST(self):

        """
        Calculates Land Surface Temperature
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
        self.report("Calculating LST")
        self.lst = self.bt / (1 + (data["lambda"] * self.bt / data["rho"]) * np.log(self.lse))

    @staticmethod
    def getBand(bandName, bands, mask):

        """
        Gets individual bands for dict of bands
        Masks '0' values with numpy nan
        """

        if(bandName in bands):
            band = bands[bandName]
            band[np.logical_not(mask)] = np.nan
            return band
        else:
            return np.array([])

    def report(self, text):

        """
        Asks the UI to show a message on the status bar
        """

        self.form.showStatus(text)

    def process(self, bands, sat_type, required, form):

        """
        Only this function should be accessed from outside this file
        Inputs:
            bands - dict of numpy arrays, "Red", "Near-IR", "Thermal-IR" are the relevant keys
            sat_type - either "Landsat8" or "Landsat5"
            required - boolean array of size 6, constitutes a request for some or all of
                        [toa, bt, ndvi, pv, lse, lst] in order.
            form - user interfacing element
        Returns:
            A dict of numpy arrays, with a key "Error" holding error message, if any
        """

        error = None
        results = dict()
        self.form = form

        if(not(list(bands.values()))):
            results["Error"] = "Files missing"
            return results
        temp = list(bands.values())[0]
        mask = np.full(temp.shape, True)
        del temp
        for layer in list(bands.values()):
            mask[layer == 0] = False
        if("Shape" in layer):
            pass

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
