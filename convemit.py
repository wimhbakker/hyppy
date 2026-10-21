#!/usr/bin/python3
## convemit.py
##
## Copyright (C) 2024 Wim Bakker
##
##        Created: 20241206
## 
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by the
## Free Software Foundation, version 3 of the License.
## 
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
## See the GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License along
## with this program. If not, see <http://www.gnu.org/licenses/>.
## 
## Contact:
##     Wim Bakker, <bakker@itc.nl>
##     University of Twente, Faculty ITC
##     Netherlands
##

## The EMIT L2A MASK_001 file contains quality and atmospheric-screening
## layers—not eight spectral reflectance bands. In the common mask_bands
## dimension, the eight layers are:
##
##    Cloud flag — identifies pixels flagged as cloudy.
##    Cirrus flag — identifies dense cirrus.
##    Water flag — identifies water bodies.
##    Spacecraft flag — identifies spacecraft or space-station components in the instrument’s view.
##    Dilated Cloud Flag — cloud mask expanded with a buffer around cloud pixels.
##    AOD550 — estimated aerosol optical depth at 550 nm.
##    H2O (g cm-2) — estimated atmospheric water-vapor amount.
##    Aggregate Flag — combines the cloud, cirrus, water, spacecraft, and dilated-cloud flags. nasa.github.io
##
## The first five and the aggregate layer are masks/flags; AOD550 and H2O are
## retrieval estimates that can be used for additional screening.

## The 11 layers in the EMIT MASK_002 product are, in order:
###	Layer	What it represents
##1	Cloud Flag	Cloud coverage
##2	Cirrus Flag	Dense cirrus clouds
##3	Water Flag	Water bodies
##4	Spacecraft Flag	Spacecraft or space-station components in EMIT’s field of view
##5	Dilated Cloud Flag	Cloud coverage plus a buffer
##6	AOD550	Estimated aerosol optical depth at 550 nm
##7	H2O (g cm-2)	Estimated atmospheric water-vapor column
##8	Aggregate Flag	Combined mask flags
##9	SpecTf Cloud Probability	Cloud-presence probability from the SpecTf model
##10	SpecTf Cloud Flag	Binary cloud flag from SpecTf
##11	SpecTf-Buffer Distance	Distance to the nearest cloud pixel from SpecTf
##
## These are the layer names and descriptions in the V002 product guide. 

# Combined mask flag
AGGREGATE_FLAG = 7

import os
import numpy as np

from netCDF4 import Dataset

import envi2
from envi2.constants import *

import glt

DEBUG = False

def message(s):
    print(s)

def read_emit_2a(filename, maskname=None, message=message, progress=None):
    # open mask file
    if maskname:
        rootgrpmask = Dataset(maskname, 'r')
        basename = os.path.splitext(maskname)[0]

        if 'mask' in rootgrpmask.variables.keys():
            mask = rootgrpmask.variables['mask'][...].data
            lines, samples, bands = mask.shape 
            data_type = mask.dtype
            if DEBUG:
                message(f"root group variables: {rootgrpmask.variables.keys()}")
                message(f"Shape {mask.shape}")
                message(f"Type {mask.dtype}")
            # band_mask is the packed per-pixel, per-wavelength quality mask
##            if 'band_mask' in rootgrpmask.variables.keys():
##                band_mask = rootgrpmask.variables['band_mask'][...].data
##                message(f"Shape {band_mask.shape}")
##                message(f"Type {band_mask.dtype}")
##                packed = band_mask.astype(np.uint8)
##                valid = np.unpackbits(packed, axis=-1)[..., :285]
##                #message(f"Valid: {valid}")
            message(f"Writing aggregate flag {os.path.basename(basename+'_AGGFLAG')}")
            aggflag = envi2.New(basename+'_AGGFLAG', lines=lines, samples=samples, bands=1,
                                data_type=data_type,
                                file_type=ENVI_Standard, interleave=ENVI_BIL,
                                byte_order=0,
                                description=['EMIT AGGREGATE FLAG'])
            aggflag[:,:,0] = mask[:,:,AGGREGATE_FLAG]
            del aggflag

    ## open netCDF4 dataset
    rootgrp = Dataset(filename, 'r')

    basename = os.path.splitext(filename)[0]

    ## some metadata
    message(rootgrp.title)
    spatial_ref = rootgrp.spatial_ref
    date  = rootgrp.date_created
    west  = rootgrp.westernmost_longitude
    east  = rootgrp.easternmost_longitude
    south = rootgrp.southernmost_latitude
    north = rootgrp.northernmost_latitude
    res   = rootgrp.spatialResolution  # capital R!
    description = f"""{rootgrp.title}
{date}"""
    coordinate_system_string = f"{spatial_ref}"

    if 'reflectance' in rootgrp.variables.keys():
        data_var = 'reflectance'
        outname = basename + '_rfl'
    elif 'reflectance_uncertainty' in rootgrp.variables.keys():
        data_var = 'reflectance_uncertainty'
        outname = basename + '_rfluncert'
    else:
        message(f"root group variables: {rootgrp.variables.keys()}")
        raise IOError('No reflectance data found in dataset')
        
    ## Reflectance data
    message(data_var)
    # lines, samples, bands
    lines, samples, bands = rootgrp.variables[data_var].get_dims()
    lines, samples, bands = lines.size, samples.size, bands.size
    byte_order = 0 if rootgrp.variables[data_var].endian() == 'little' else 1
    data_ignore_value = rootgrp.variables[data_var]._FillValue
    data_type = rootgrp.variables[data_var].dtype.type
    if DEBUG:
        message(f"{lines}, {samples}, {bands}")
        message(f"Fill value {data_ignore_value}")
        message(f"Data type {data_type}")

    ## group sensor_band_parameters
    # wavelengths
    wavelengths = rootgrp.groups['sensor_band_parameters'].variables['wavelengths'][...].data

    # fwhm: variable fwhm
    fwhm = rootgrp.groups['sensor_band_parameters'].variables['fwhm'][...].data

    # bbl: variable good_wavelengths
    bbl = rootgrp.groups['sensor_band_parameters'].variables['good_wavelengths'][...].data

    map_info = ["Geographic Lat/Lon", 1.0, 1.0, west, north, res, res, \
                "WGS-84", "units=Degrees"]
    message(f"map info: {map_info}")

    message(f"Writing output {os.path.basename(outname)}")

    reflname = outname
    im = envi2.New(outname, lines=lines, samples=samples, bands=bands, \
                   wavelength=wavelengths, fwhm=fwhm, bbl=bbl, data_type=data_type, \
                   file_type=ENVI_Standard, interleave=ENVI_BIL,
                   byte_order=byte_order, data_ignore_value=data_ignore_value,
                   description=description, \
                   coordinate_system_string=coordinate_system_string, \
                   map_info=map_info)
    if maskname:
        im[...] = rootgrp.variables[data_var][...].data * (1 - mask[:,:,AGGREGATE_FLAG].clip(min=0, max=1)[:,:,np.newaxis])
    else:
        im[...] = rootgrp.variables[data_var][...].data
    del im

    ## group location
    # longitude
    # lines, samples, bands
    lines, samples = rootgrp.groups['location'].variables['lon'].get_dims()
    lines, samples = lines.size, samples.size
    data_type = rootgrp.groups['location'].variables['lon'].dtype.type
    if DEBUG:
        message('location data')
        message(f"{lines}, {samples}")
        message(data_type)

    message(f"Writing lat/long data {os.path.basename(basename + '_lonlat')}")
    im = envi2.New(basename + '_lonlat', lines=lines, samples=samples, bands=2, \
                   band_names=['longitude', 'latitude'], \
                   wavelength=None, fwhm=None, bbl=None, data_type=data_type, \
                   file_type=ENVI_Standard, interleave=ENVI_BSQ)

    im[0] = rootgrp.groups['location'].variables['lon'][...].data

    # latitude
    im[1] = rootgrp.groups['location'].variables['lat'][...].data
    del im

    # elevation
    lines, samples = rootgrp.groups['location'].variables['elev'].get_dims()
    lines, samples = lines.size, samples.size
    data_type = rootgrp.groups['location'].variables['elev'].dtype.type
    if DEBUG:
        message('elevation data')
        message(f"{lines}, {samples}")
        message(data_type)

    message(f"Writing Elevation data {os.path.basename(basename + '_elev')}")
    im = envi2.New(basename + '_elev', lines=lines, samples=samples, bands=1, \
                   band_names=['elevation'], \
                   wavelength=None, fwhm=None, bbl=None, data_type=data_type, \
                   file_type=ENVI_Standard, interleave=ENVI_BSQ)

    im[0] = rootgrp.groups['location'].variables['elev'][...].data

    # glt_x, int32
    lines, samples = rootgrp.groups['location'].variables['glt_x'].get_dims()
    lines, samples = lines.size, samples.size
    data_type = rootgrp.groups['location'].variables['glt_x'].dtype.type
    if DEBUG:
        message('glt data')
        message(f"{lines}, {samples}")
        message(data_type)

    message(f"Writing Geographic Lookup Table (GLT) {os.path.basename(basename + '_glt')}")
    gltname = basename + '_glt'
    im = envi2.New(basename + '_glt', lines=lines, samples=samples, bands=2, \
                   band_names=['glt_x', 'glt_y'], \
                   wavelength=None, fwhm=None, bbl=None, data_type=data_type, \
                   file_type=ENVI_Standard, interleave=ENVI_BSQ)

    im[0] = rootgrp.groups['location'].variables['glt_x'][...].data

    # glt_y, int32
    im[1] = rootgrp.groups['location'].variables['glt_y'][...].data
    del im

    # Applying GLT
    message(f"Applying GLT")
    message(f"Writing {os.path.basename(reflname+'_geo')}")
    glt.forward(reflname, gltname, reflname+'_geo')

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='convemit.py',
        description='Convert EMIT image to ENVI format.')

    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-m', dest='mask', help='input mask name', required=False)

    options = parser.parse_args()

    read_emit_2a(options.input, maskname=options.mask)

