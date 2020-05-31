import numpy as np
from PIL import Image

def loadBands(filepaths):

    """
    Gets band data as numpy arrays, from filepaths

    Inputs:
        filepaths - dictionary of bandnames (str) to paths (str)
    Outputs:
        bands - dictionary of bandnames (str) to 2d numpy arrays (int16)
    """

    bands = dict()
    for band in filepaths:
        im = Image.open(filepaths[band])
        bands[band] = np.array(im, dtype = np.int16)
    return bands
