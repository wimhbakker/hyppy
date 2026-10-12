# pip install h5py

import h5py
import os
import sys
import numpy as np

import envi2
import envi2.constants

def message(s):
    print(s)

def read_prisma(fname, message=message, progress=None):
    if "L2A" in fname:
        message("Level 2A")
        read_prisma_L2A(fname, message=message, progress=progress)
    elif "L2B" in fname:
        message("Level 2B")
        read_prisma_L2B(fname, message=message, progress=progress)
    elif "L2C" in fname:
        message("Level 2C")
        read_prisma_L2C(fname, message=message, progress=progress)
    elif "L2D" in fname:
        message("Level 2D")
        read_prisma_L2D(fname, message=message, progress=progress)
    elif "L1" in fname:
        message("Level 1")
        read_prisma_L1(fname, message=message, progress=progress)
    else:
        raise IOError("File name not recognized")

# L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1 L1
def read_prisma_L1(fname, message=message, progress=None):
    f = h5py.File(fname, "r")

    # ATTR
    Processing_Level = f.attrs["Processing_Level"].decode()
    message(f"Processing Level {Processing_Level}")

    cw_swir = f.attrs["List_Cw_Swir"]
    message(cw_swir)
    cw_swir_bbl = f.attrs["List_Cw_Swir_Flags"]
    cw_swir_fwhm = f.attrs["List_Fwhm_Swir"]

    cw_vnir = f.attrs["List_Cw_Vnir"]
    message(cw_vnir)
    cw_vnir_bbl = f.attrs["List_Cw_Vnir_Flags"]
    cw_vnir_fwhm = f.attrs["List_Fwhm_Vnir"]

    # HRC dataset co-registered VNIR and SWIR
    swir = f["/HDFEOS/SWATHS/PRS_L1_HRC/Data Fields/SWIR_Cube"]
    message(f"SWIR: {swir.shape}")
    message(f"SWIR: {swir.dtype}")

    swir_err = f["/HDFEOS/SWATHS/PRS_L1_HRC/Data Fields/SWIR_PIXEL_SAT_ERR_MATRIX"]

    lines, bands, samples = swir.shape

    vnir = f["/HDFEOS/SWATHS/PRS_L1_HRC/Data Fields/VNIR_Cube"]
    message(f"VNIR: {vnir.shape}")
    message(f"VNIR: {vnir.dtype}")

    vnir_err = f["/HDFEOS/SWATHS/PRS_L1_HRC/Data Fields/VNIR_PIXEL_SAT_ERR_MATRIX"]

    latitude = f["/HDFEOS/SWATHS/PRS_L1_HRC/Geolocation Fields/Latitude_SWIR"]
    message(f"LAT: {latitude.shape}")
    message(f"LAT: {latitude.dtype}")

    longitude = f["/HDFEOS/SWATHS/PRS_L1_HRC/Geolocation Fields/Longitude_SWIR"]
    message(f"LON: {longitude.shape}")
    message(f"LON: {longitude.dtype}")

    # PRC, PAN data co-registered with SWIR and VNIR
    pan = f["/HDFEOS/SWATHS/PRS_L1_PRC/Data Fields/Cube"]
    message(f"PAN: {pan.shape}")
    message(f"PAN: {pan.dtype}")

    pan_err = f["/HDFEOS/SWATHS/PRS_L1_PRC/Data Fields/PIXEL_SAT_ERR_MATRIX"]

    pan_latitude = f["/HDFEOS/SWATHS/PRS_L1_PRC/Geolocation Fields/Latitude"]
    message(f"PAN_LAT: {pan_latitude.shape}")
    message(f"PAN_LAT: {pan_latitude.dtype}")

    pan_longitude = f["/HDFEOS/SWATHS/PRS_L1_PRC/Geolocation Fields/Longitude"]
    message(f"PAN_LON: {pan_longitude.shape}")
    message(f"PAN_LON: {pan_longitude.dtype}")

    # ENVI VNIR+SWIR
    bname, ext = os.path.splitext(fname)
    description = ['PRISMA VNIR+SWIR data']
    file_type = envi2.constants.ENVI_Standard
    interleave = envi2.constants.ENVI_BIP
    data_type = 'f' # swir.dtype
    byte_order = 0 if sys.byteorder=='little' else 1

    lines, swir_bands, samples = swir.shape
    _, vnir_bands, _ = vnir.shape
    bands = vnir_bands + swir_bands

    wavelength = np.hstack((cw_vnir[::-1], cw_swir[::-1]))
    fwhm = np.hstack((cw_vnir_fwhm[::-1], cw_swir_fwhm[::-1]))
    bbl = np.hstack((cw_vnir_bbl[::-1], cw_swir_bbl[::-1]))

    # GEO_POINTS from the latitude longitude data

    ULcorner_lat = latitude[0,0]
    ULcorner_long = longitude[0,0]
    message(f"UL: {ULcorner_lat} {ULcorner_long}")

    URcorner_lat = latitude[0,-1]
    URcorner_long = longitude[0,-1]
    message(f"UR: {URcorner_lat} {URcorner_long}")

    LLcorner_lat = latitude[-1,0]
    LLcorner_long = longitude[-1,0]
    message(f"LL: {LLcorner_lat} {LLcorner_long}")

    LRcorner_lat = latitude[-1,-1]
    LRcorner_long = longitude[-1,-1]
    message(f"LR: {LRcorner_lat} {LRcorner_long}")

    # GEO_POINTS order should be UL, UR, LL, LR and x, y, lat, long (!!)
    geo_points = [1      , 1    , float(ULcorner_lat), float(ULcorner_long),
                  samples, 1    , float(URcorner_lat), float(URcorner_long),
                  1      , lines, float(LLcorner_lat), float(LLcorner_long),
                  samples, lines, float(LRcorner_lat), float(LRcorner_long)]

    message(f"geo points {geo_points}")

    # Setting up output ENVI image
    envi_im = envi2.New(bname+'_VNIR+SWIR', value=float('nan'), description=description, file_type=file_type,
                          interleave=interleave, data_type=data_type,
                          byte_order=byte_order, samples=samples,
                          lines=lines, bands=bands, wavelength=wavelength,
                          fwhm=fwhm, bbl=bbl, geo_points=geo_points)

    if progress:
        progress(0.0)

    message("Writing VNIR data")
    b = 0
    for i in range(vnir_bands):
        envi_im[:, :, b] = (vnir[:, vnir_bands-i-1, :] * (1 - vnir_err[:, vnir_bands-i-1, :]))
        b = b + 1
        if progress:
            progress(b / bands)

    message("Writing SWIR data")
    for i in range(swir_bands):
        envi_im[:, :, b] = (swir[:, swir_bands-i-1, :] * (1 - swir_err[:, swir_bands-i-1, :]))
        b = b + 1
        if progress:
            progress(b / bands)

    if progress:
        progress(1.0)
        
    del envi_im

    # ENVI PAN
    bname, ext = os.path.splitext(fname)
    description = ['PRISMA PAN data']
    file_type = envi2.constants.ENVI_Standard
    interleave = envi2.constants.ENVI_BIP
    data_type = 'f' # swir.dtype
    byte_order = 0 if sys.byteorder=='little' else 1

    lines, samples = pan.shape
    bands = 1

    # GEO_POINTS from the latitude longitude data

    ULcorner_lat = latitude[0,0]
    ULcorner_long = longitude[0,0]
    message(f"UL: {ULcorner_lat} {ULcorner_long}")

    URcorner_lat = latitude[0,-1]
    URcorner_long = longitude[0,-1]
    message(f"UR: {URcorner_lat} {URcorner_long}")

    LLcorner_lat = latitude[-1,0]
    LLcorner_long = longitude[-1,0]
    message(f"LL: {LLcorner_lat} {LLcorner_long}")

    LRcorner_lat = latitude[-1,-1]
    LRcorner_long = longitude[-1,-1]
    message(f"LR: {LRcorner_lat} {LRcorner_long}")

    # GEO_POINTS order should be UL, UR, LL, LR and x, y, lat, long (!!)
    geo_points = [1      , 1    , float(ULcorner_lat), float(ULcorner_long),
                  samples, 1    , float(URcorner_lat), float(URcorner_long),
                  1      , lines, float(LLcorner_lat), float(LLcorner_long),
                  samples, lines, float(LRcorner_lat), float(LRcorner_long)]

    message(f"geo points {geo_points}")

    # Setting up output ENVI image
    envi_im = envi2.New(bname+'_PAN', value=float('nan'), description=description, file_type=file_type,
                          interleave=interleave, data_type=data_type,
                          byte_order=byte_order, samples=samples,
                          lines=lines, bands=bands, geo_points=geo_points)

    message("Writing PAN data")
    envi_im[:, :, 0] = (pan[:, :] * (1 - pan_err[:, :]))
        
    del envi_im

## L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A L2A

def read_prisma_L2A(fname, message=message, progress=None):
    raise ValueError("Level 2A not supported")

## L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B L2B

def read_prisma_L2B(fname, message=message, progress=None):
    raise ValueError("Level 2B not supported")

## L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C L2C

def read_prisma_L2C(fname, message=message, progress=None):
    raise ValueError("Level 2C not supported")

## L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D L2D

def read_prisma_L2D(fname, message=message, progress=None):
    f = h5py.File(fname, "r")

    # ATTR
    Processing_Level = f.attrs["Processing_Level"].decode()
    message(f"Processing Level {Processing_Level}")

    cw_swir_max = f.attrs["L2ScaleSwirMax"]
    message(cw_swir_max)

    cw_swir = f.attrs["List_Cw_Swir"]
    message(cw_swir)
    cw_swir_bbl = f.attrs["List_Cw_Swir_Flags"]
    cw_swir_fwhm = f.attrs["List_Fwhm_Swir"]

    cw_vnir = f.attrs["List_Cw_Vnir"]
    message(cw_vnir)
    cw_vnir_bbl = f.attrs["List_Cw_Vnir_Flags"]
    cw_vnir_fwhm = f.attrs["List_Fwhm_Vnir"]

    # HSI
    swir = f["/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_Cube"]
    message(f"SWIR: {swir.shape}")
    message(f"SWIR: {swir.dtype}")

    swir_err = f["/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/SWIR_PIXEL_L2_ERR_MATRIX"]

    vnir = f["/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_Cube"]
    message(f"VNIR: {vnir.shape}")
    message(f"VNIR: {vnir.dtype}")

    vnir_err = f["/HDFEOS/SWATHS/PRS_L2D_HCO/Data Fields/VNIR_PIXEL_L2_ERR_MATRIX"]

    latitude = f["/HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation Fields/Latitude"]
    message(f"LAT: {latitude.shape}")
    message(f"LAT: {latitude.dtype}")

    longitude = f["/HDFEOS/SWATHS/PRS_L2D_HCO/Geolocation Fields/Longitude"]
    message(f"LON: {longitude.shape}")
    message(f"LON: {longitude.dtype}")

    # PAN
    pan = f["/HDFEOS/SWATHS/PRS_L2D_PCO/Data Fields/Cube"]
    message(f"PAN: {pan.shape}")
    message(f"PAN: {pan.dtype}")

    pan_err = f["/HDFEOS/SWATHS/PRS_L2D_PCO/Data Fields/PIXEL_L2_ERR_MATRIX"]

    pan_latitude = f["/HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation Fields/Latitude"]
    message(f"PAN_LAT: {pan_latitude.shape}")
    message(f"PAN_LAT: {pan_latitude.dtype}")

    pan_longitude = f["/HDFEOS/SWATHS/PRS_L2D_PCO/Geolocation Fields/Longitude"]
    message(f"PAN_LON: {pan_longitude.shape}")
    message(f"PAN_LON: {pan_longitude.dtype}")

    # ENVI VNIR+SWIR
    bname, ext = os.path.splitext(fname)
    description = ['PRISMA VNIR+SWIR data']
    file_type = envi2.constants.ENVI_Standard
    interleave = envi2.constants.ENVI_BIP
    data_type = 'f' # swir.dtype
    byte_order = 0 if sys.byteorder=='little' else 1

    lines, swir_bands, samples = swir.shape
    _, vnir_bands, _ = vnir.shape
    bands = vnir_bands + swir_bands

    wavelength = np.hstack((cw_vnir[::-1], cw_swir[::-1]))
    fwhm = np.hstack((cw_vnir_fwhm[::-1], cw_swir_fwhm[::-1]))
    bbl = np.hstack((cw_vnir_bbl[::-1], cw_swir_bbl[::-1]))

    # MAP_INFO
    Projection_Name = f.attrs["Projection_Name"].decode()
    message(Projection_Name)

    ULcorner_easting = f.attrs["Product_ULcorner_easting"]
    ULcorner_northing = f.attrs["Product_ULcorner_northing"]
    message(f"{ULcorner_easting}, {ULcorner_northing}")

    LRcorner_easting = f.attrs["Product_LRcorner_easting"]
    LRcorner_northing = f.attrs["Product_LRcorner_northing"]

    delta_x = (LRcorner_easting - ULcorner_easting) / (samples - 1)
    delta_y = (ULcorner_northing - LRcorner_northing) / (lines - 1)
    message(f"{delta_x}, {delta_y}")

    Projection_Id = f.attrs["Projection_Id"].decode()
    message(Projection_Id)

    Epsg_Code = f.attrs["Epsg_Code"]
    message(Epsg_Code)
    Hemisphere = 'North' if str(Epsg_Code)[2]=='6' else 'South'
    message(Hemisphere)

    Reference_Ellipsoid = f.attrs["Reference_Ellipsoid"].decode()
    message(Reference_Ellipsoid)

    map_info = [Projection_Name,
                1.0, 1.0, float(ULcorner_easting), float(ULcorner_northing),
                float(delta_x), float(delta_y),
                Projection_Id, Hemisphere, Reference_Ellipsoid]

    message(f"map_info: {map_info}")

    # Setting up output ENVI image
    envi_im = envi2.New(bname+'_VNIR+SWIR', value=float('nan'), description=description, file_type=file_type,
                          interleave=interleave, data_type=data_type,
                          byte_order=byte_order, samples=samples,
                          lines=lines, bands=bands, wavelength=wavelength,
                          fwhm=fwhm, bbl=bbl, map_info=map_info)

    if progress:
        progress(0.0)

    message("Writing VNIR data")
    b = 0
    for i in range(vnir_bands):
        envi_im[:, :, b] = (vnir[:, vnir_bands-i-1, :] * (1 - vnir_err[:, vnir_bands-i-1, :])) / 65535.0
        b = b + 1
        if progress:
            progress(b / bands)

    message("Writing SWIR data")
    for i in range(swir_bands):
        envi_im[:, :, b] = (swir[:, swir_bands-i-1, :] * (1 - swir_err[:, swir_bands-i-1, :])) / 65535.0
        b = b + 1

        if progress:
            progress(b / bands)
        
    if progress:
        progress(1.0)

    del envi_im

    # ENVI PAN
    bname, ext = os.path.splitext(fname)
    description = ['PRISMA PAN data']
    file_type = envi2.constants.ENVI_Standard
    interleave = envi2.constants.ENVI_BIP
    data_type = 'f' # swir.dtype
    byte_order = 0 if sys.byteorder=='little' else 1

    lines, samples = pan.shape
    bands = 1

    # MAP_INFO
    Projection_Name = f.attrs["Projection_Name"].decode()
    message(Projection_Name)

    ULcorner_easting = f.attrs["Product_ULcorner_easting"]
    ULcorner_northing = f.attrs["Product_ULcorner_northing"]
    message(f"{ULcorner_easting}, {ULcorner_northing}")

    LRcorner_easting = f.attrs["Product_LRcorner_easting"]
    LRcorner_northing = f.attrs["Product_LRcorner_northing"]

    delta_x = (LRcorner_easting - ULcorner_easting) / (samples - 1)
    delta_y = (ULcorner_northing - LRcorner_northing) / (lines - 1)
    message(f"{delta_x}, {delta_y}")

    Projection_Id = f.attrs["Projection_Id"].decode()
    message(Projection_Id)

    Epsg_Code = f.attrs["Epsg_Code"]
    message(Epsg_Code)
    Hemisphere = 'North' if str(Epsg_Code)[2]=='6' else 'South'
    message(Hemisphere)

    Reference_Ellipsoid = f.attrs["Reference_Ellipsoid"].decode()
    message(Reference_Ellipsoid)

    map_info = [Projection_Name,
                1.0, 1.0, float(ULcorner_easting), float(ULcorner_northing),
                float(delta_x), float(delta_y),
                Projection_Id, Hemisphere, Reference_Ellipsoid]

    message(f"PAN map_info: {map_info}")

    # Setting up output ENVI image
    envi_im = envi2.New(bname+'_PAN', value=float('nan'), description=description, file_type=file_type,
                          interleave=interleave, data_type=data_type,
                          byte_order=byte_order, samples=samples,
                          lines=lines, bands=bands, map_info=map_info)

    message("Writing PAN data")
    envi_im[:, :, 0] = (pan[:, :] * (1 - pan_err[:, :])) / 65535.0
        
    del envi_im

# for testing...
#read_prisma("PRS_L2D_STD_20260724080229_20260724080234_0001.he5")
#read_prisma("PRS_L1_STD_OFFL_20260724080229_20260724080234_0001.he5")

# MAIN
if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='convprisma.py',
        description='Convert PRISMA image to ENVI format.')

    parser.add_argument('-i', dest='input', help='input file name', required=True)

    options = parser.parse_args()

    read_prisma(options.input)

