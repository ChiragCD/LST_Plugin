import numpy as np
import gdal, os, tarfile
from zipfile import ZipFile
import processing
from qgis.core import QgsVectorLayer, QgsRasterLayer, QgsCoordinateTransform, QgsProject

gdal.UseExceptions()

class fileHandler(object):

    """
    Class to handle all file input output operations
    """

    def __init__(self):

        self.folder = ""            ## Folder in which all operations are ongoing
        self.outfolder = ""         ## Folder in which to place outputs

        ## Tif writing data, copied from input
        self.rows = 0
        self.cols = 0
        self.driver = None
        self.geoTransform = None
        self.projection = None

    def readBand(self, filepath):

        """
        Given a filepath, read a numpy array from its data
        Save tif data for future use, if the class has not already done so
        """

        im = gdal.Open(filepath)
        array = im.ReadAsArray().astype(np.float32)
        if(not(self.folder)):
            self.folder = filepath[:filepath.rfind('/')]
        if(not(self.driver)):
            self.rows = im.RasterYSize
            self.cols = im.RasterXSize
            self.driver = im.GetDriver()
            self.geoTransform = im.GetGeoTransform()
            self.projection = im.GetProjection()
            layer = QgsRasterLayer(filepath, "Temp")
            self.extent = layer.extent()
            self.crs = layer.crs()
        del im
        return array

    def loadZip(self, filePaths):

        """
        Compatible with zip, tar and gz extensions
        Read only Red, Near IR and Thermal IR bands
        Get satellite type by looking at the name of the metadata file.
        """

        filepath = filePaths["zip"]
        recognised = False
        bands = {"Error" : None}
        for ext in [".tar.gz", ".tar", ".zip", ".gz"]:
            if(filepath.lower().endswith(ext)):
                recognised = True
        if(not(recognised)):
            bands["Error"] = "Unknown compressed file format"
            return bands
        self.folder = filepath[:filepath.rfind("/")]

        if(filepath.lower().endswith(".zip")):
            compressed = ZipFile(filepath, 'r')
            extract = compressed.extract
            listoffiles = compressed.namelist()
        elif(filepath.lower().endswith(".gz")):
            compressed = tarfile.open(filepath, "r:gz")
            extract = compressed.extract
            listoffiles = [member.name for member in compressed.getmembers()]
        else:
            compressed = tarfile.open(filepath, 'r')
            extract = compressed.extract
            listoffiles = compressed.getmembers()

        for filename in listoffiles:
            if(filename.upper().endswith("MTL.TXT")):
                if(filename[:4] == "LC08"):
                    bands["sat_type"] = "Landsat8"
                    sat_type = "Landsat8"
                if(filename[:4] == "LT05"):
                    bands["sat_type"] = "Landsat5"
                    sat_type = "Landsat5"
        if("sat_type" not in bands):
            bands["Error"] = "Unknown satellite - Please verify that files have not been renamed"
            compressed.close()
            return bands

        sat_bands = {"Landsat5" : {"Red" : "B3", "Near-IR" : "B4", "Thermal-IR" : "B6"},
                "Landsat8" : {"Red" : "B4", "Near-IR" : "B5", "Thermal-IR" : "B10"} }
        filepaths = dict()
        for band in ("Red", "Near-IR", "Thermal-IR"):
            bands[band] = np.array([])
            for filename in listoffiles:
                if(filename.upper().endswith(sat_bands[sat_type][band] + ".TIF")):
                    extract(filename)
                    filepaths[band] = filename
        compressed.close()
        for band in ("Red", "Near-IR", "Thermal-IR"):
            bands[band] = self.readBand(filepaths[band])

        if("Shape" in filepaths):
            bands["Shape"] = self.readShapeFile(filepaths["Shape"])
            if(type(bands["Shape"]) == str):
                bands["Error"] = bands["Shape"]
                return bands
        return bands

    def loadBands(self, filepaths):

        """
        Gets band data as numpy arrays, from a dict of filepaths
        """

        bands = {"Error" : None}
        for band in filepaths:
            if(band == "Shape"):
                continue
            if(not(filepaths[band].lower().endswith(".tif"))):
                bands["Error"] = "Bands must be TIFs"
                return bands
            bands[band] = self.readBand(filepaths[band])
        if("Shape" in filepaths):
            bands["Shape"] = self.readShapeFile(filepaths["Shape"])
            if(type(bands["Shape"]) == str):
                bands["Error"] = bands["Shape"]
                return bands
        return bands
    
    def readShapeFile(self, vectorfname):

        """
        Get a rasterized numpy array from the features of a shapefile
        """
        
        if(not(vectorfname.lower().endswith(".shp"))):
            return "Shapes must be SHPs"
        vlayer = self.loadVectorLayer(vectorfname)
        shapefile = self.generateFileName("Shape", "TIF")
        self.rasterize(vlayer, shapefile)
        return self.readBand(shapefile)

    def saveArray(self, array, fname):

        """
        Saves array as tiff file named fname
        Use TIF info saved by the class on input
        Should not be used directly, use saveAll instead
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
    
    def loadVectorLayer(self, fname):

        """
        Load a vector layer, using qgis core functionality
        """

        layer = QgsVectorLayer(fname, "Shape", "ogr")
        return layer
    
    def rasterize(self, vlayer, fname, res = 30):

        """
        Convert a vector layer to a raster layer, handle CRS differences
        """

        rfile = self.driver.Create(fname, self.cols, self.rows, bands=1, eType = gdal.GDT_Float32)
        rfile.SetProjection(self.projection)
        rfile.SetGeoTransform(self.geoTransform)
        rfile = None

        transformer = QgsCoordinateTransform(self.crs, vlayer.crs(), QgsProject.instance())
        extent = transformer.transformBoundingBox(self.extent)
        xmin = extent.xMinimum()
        xmax = extent.xMaximum()
        ymin = extent.yMinimum()
        ymax = extent.yMaximum()

        resdrop = (self.extent.xMaximum() - self.extent.xMinimum()) / (xmax - xmin)

        parameters = {
            "INPUT" : vlayer,
            "FIELD" : "id",
            "HEIGHT": res / resdrop,
            "WIDTH" : res / resdrop,
            "BURN"  : 0,
            "UNITS" : 1,
            "EXTENT":"%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),
            "DATA_TYPE" : 5,
            "NODATA" : 1,
            "OUTPUT": fname
        }
        processing.run("gdal:rasterize", parameters) 

    def prepareOutFolder(self):

        """
        Make a new directory under the operating folder, for outputs
        """

        outfolder = self.folder + "/LandSurfaceTemperature"
        while os.path.isdir(outfolder):
            if outfolder[-1].isnumeric():
                outfolder = outfolder[:-1] + str(1 + int(outfolder[-1]))
            else:
                outfolder += "1"
        os.makedirs(outfolder)
        self.outfolder = outfolder

    def generateFileName(self, topic, ftype):

        """
        Generate a filepath for topic
        """
        
        if(not(self.outfolder)):
            self.prepareOutFolder()
        return self.outfolder + "/" + topic + "." + ftype

    def saveAll(self, arrays):

        """
        Write each of a dict of arrays as TIF outputs
        """

        if(not(self.outfolder)):
            self.prepareOutFolder()

        for resultName in arrays:
            filepath = self.generateFileName(resultName, "TIF")
            self.saveArray(arrays[resultName], filepath)
