import numpy as np
import gdal, os

class fileHandler(object):

    def __init__(self):

        self.folder = ""
        self.outfolder = ""
        self.rows = 0
        self.cols = 0
        self.driver = None
        self.geoTransform = None
        self.projection = None

    def readBand(self, filepath):

        im = gdal.Open(filepath)
        array = im.ReadAsArray().astype(np.float16)
        if(not(self.folder)):
            self.folder = filepath[:filepath.rfind('/')]
        if(not(self.driver)):
            self.rows = im.RasterYSize
            self.cols = im.RasterXSize
            self.driver = im.GetDriver()
            self.geoTransform = im.GetGeoTransform()
            self.projection = im.GetProjection()
        del im
        return array

    def loadBands(self, filepaths):

        """
        Gets band data as numpy arrays, from filepaths

        Inputs:
            filepaths - dictionary of bandnames (str) to paths (str)
        Outputs:
            bands - dictionary of bandnames (str) to 2d numpy arrays (int16)
        """

        bands = dict()
        for band in filepaths:
            bands[band] = self.readBand(filepaths[band])
        return bands

    def saveArray(self, array, fname):

        """
        Saves array as tiff file fname

        Inputs:
            array - numpy array
            fname - str
        Outputs:
            None
        """

        outDS = self.driver.Create(fname, self.cols, self.rows, bands=1, eType = gdal.GDT_Float32)
        outBand = outDS.GetRasterBand(1)
        outBand.WriteArray(array)
        outBand.FlushCache()
        outDS.SetGeoTransform(self.geoTransform)
        outDS.SetProjection(self.projection)

        del outDS
        del array

        """
        DavidF's answer at
        https://gis.stackexchange.com/questions/37238/writing-numpy-array-to-raster-file
        was incredibly useful.
        """

    def prepareOutFolder(self):

        outfolder = self.folder + "/LSTPluginResults"
        while os.path.isdir(outfolder):
            if outfolder[-1].isnumeric():
                outfolder = outfolder[:-1] + str(1 + int(outfolder[-1]))
            else:
                outfolder += "1"
        os.makedirs(outfolder)
        self.outfolder = outfolder

    def generateFileName(self, topic, ftype):
        return self.outfolder + "/" + topic + "." + ftype

    def saveAll(self, arrays):

        if(not(self.outfolder)):
            self.prepareOutFolder()

        for resultName in arrays:
            filepath = self.generateFileName(resultName, "TIF")
            self.saveArray(arrays[resultName], filepath)

        print("Saved at " + self.outfolder)
