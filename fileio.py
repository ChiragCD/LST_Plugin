import numpy as np
import gdal

sampleDS = None

def loadBands(filepaths):

    """
    Gets band data as numpy arrays, from filepaths

    Inputs:
        filepaths - dictionary of bandnames (str) to paths (str)
    Outputs:
        bands - dictionary of bandnames (str) to 2d numpy arrays (int16)
    """

    global sampleDS

    bands = dict()
    for band in filepaths:
        im = gdal.Open(filepaths[band])
        bands[band] = im.ReadAsArray().astype('int16')
    sampleDS = im
    return bands

def saveArray(array, fname):

    """
    Saves array as tiff file fname

    Inputs:
        array - numpy array
        fname - str
    Outputs:
        None
    """

    global sampleDS
    rows = sampleDS.RasterYSize
    cols = sampleDS.RasterXSize
    driver = sampleDS.GetDriver()

    outDS = driver.Create(fname, cols, rows, bands=1, eType = gdal.GDT_Float32)
    outBand = outDS.GetRasterBand(1)
    outBand.WriteArray(array)
    outBand.FlushCache()
    outDS.SetGeoTransform(sampleDS.GetGeoTransform())
    outDS.SetProjection(sampleDS.GetProjection())

    del outDS
    del array

    """
    DavidF's answer at
    https://gis.stackexchange.com/questions/37238/writing-numpy-array-to-raster-file
    was incredibly useful.
    """
