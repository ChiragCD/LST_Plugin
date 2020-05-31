import numpy as np


def calc_TOA_radiance(tir, sat_type):

    """
    Calculates Top Of Atmosphere Radiance
    Inputs:
        tir - numpy array
    Returns:
        toa - numpy array
    """

    data = {
        "Landsat8": {
            "mul": 0.0003342,
            "add": -0.19,
        },  ##-0.19 = 0.1 - 0.29 (landsat 8 band 10 correction)
        "Landsat5": {"mul": 0.055375, "add": 1.18243},
    }
    toa = (tir * data[sat_type]["mul"]) + data[sat_type]["add"]
    return toa


def calc_BT(toa, sat_type):

    """
    Calculates at-sensor Brightness Temperature
    Inputs:
        toa - numpy array
    Returns:
        bt - numpy array
    """

    data = {
        "Landsat8": {"K1": 1321.0789, "K2": 774.8853},
        "Landsat5": {"K1": 607.76, "K2": 1260.56},
    }
    bt = (data[sat_type]["K2"] / np.log((data[sat_type]["K1"] / toa) + 1)) - 273.15
    return bt


def calc_NDVI(nir, r):

    """
    Calculates NDVI values
    Inputs:
        nir, r - numpy arrays
    Returns:
        ndvi - numpy array
    """

    ndvi = (nir - r) / (nir + r)
    return ndvi


def calc_PV(ndvi):

    """
    Calculates proportion of vegetation
    Inputs:
        ndvi - numpy array
    Returns:
        pv - numpy array
    """

    data = {"ndvi_soil": 0.2, "ndvi_vegetation": 0.5}
    pv = np.square(
        (ndvi - data["ndvi_soil"]) / (data["ndvi_vegetation"] - data["ndvi_soil"])
    )
    return pv


def calc_LSE(ndvi, pv):

    """
    Calculates Land Surface Emmissivity
    Inputs:
        ndvi, pv - numpy array
    Returns:
        lse - numpy array
    """

    data = {
        "water_emissivity": 0.991,
        "soil_emissivity": 0.996,
        "vegetation_emissivity": 0.973,
    }
    lse = np.full(ndvi.shape, data["water_emissivity"])
    lse[ndvi > 0] = data["soil_emissivity"]
    lse[ndvi > 0.2] += pv[ndvi > 0.2] * (
        data["vegetation_emissivity"] - data["soil_emissivity"]
    )
    lse[ndvi > 0.5] = data["vegetation_emissivity"]
    return lse


def calc_LST(bt, lse):

    """
    Calculates Land Surface Temperature
    Inputs:
        bt, lse - numpy array
    Returns:
        lst - numpy array
    """

    data = {"lambda": 0.00115, "rho": 1.4388}  ##Verify values, only ratio important
    lst = bt / (1 + (data["lambda"] * bt / data["rho"]) * np.log(lse))
    return lst


def process(r, nir, tir, sat_type):

    """
    Interfacing function, follows steps and returns all subparts
    Inputs:
        r, nir, tir - numpy arrays
        sat_type - str (either "Landsat8" or "Landsat5")
    Returns:
        toa, bt, ndvi, pv, lse, lst - numpy arrays
    """

    toa = calc_TOA_radiance(tir, sat_type)
    bt = calc_BT(toa, sat_type)
    ndvi = calc_NDVI(nir, r)
    pv = calc_PV(ndvi)
    lse = calc_LSE(ndvi, pv)
    lst = calc_LST(bt, lse)
    return toa, bt, ndvi, pv, lse, lst
