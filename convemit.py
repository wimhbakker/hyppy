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

import os

from netCDF4 import Dataset

import envi2
from envi2.constants import * 

def message(s):
    print(s)

def read_emit_2a(filename, message=message, progress=None):
    ## open netCDF4 dataset
    rootgrp = Dataset(filename, 'r')

    basename = os.path.splitext(filename)[0]

    ## some metadata
    message(rootgrp.title)
    spatial_ref = rootgrp.spatial_ref
    date = rootgrp.date_created
    west = rootgrp.westernmost_longitude
    east = rootgrp.easternmost_longitude
    south = rootgrp.southernmost_latitude
    north = rootgrp.northernmost_latitude

    if 'reflectance' in rootgrp.variables.keys():
        ## Reflectance data
        message('reflectance')
        # lines, samples, bands
        lines, samples, bands = rootgrp.variables['reflectance'].get_dims()
        lines, samples, bands = lines.size, samples.size, bands.size
        message(f"{lines}, {samples}, {bands}")
        data_type = rootgrp.variables['reflectance'].dtype.type
        message(data_type)

        ## group sensor_band_parameters
        # wavelengths
        wavelengths = rootgrp.groups['sensor_band_parameters'].variables['wavelengths'][...].data

        # fwhm: variable fwhm
        fwhm = rootgrp.groups['sensor_band_parameters'].variables['fwhm'][...].data

        # bbl: variable good_wavelengths
        bbl = rootgrp.groups['sensor_band_parameters'].variables['good_wavelengths'][...].data

        im = envi2.New(basename + '_refl', lines=lines, samples=samples, bands=bands, \
                       wavelength=wavelengths, fwhm=fwhm, bbl=bbl, data_type=data_type, \
                       file_type=ENVI_Standard, interleave=ENVI_BIL)
                       
        im[...] = rootgrp.variables['reflectance'][...].data
        del im

        ## group location
        message('location')
        # longitude
        # lines, samples, bands
        lines, samples = rootgrp.groups['location'].variables['lon'].get_dims()
        lines, samples = lines.size, samples.size
        message(f"{lines}, {samples}")
        data_type = rootgrp.groups['location'].variables['lon'].dtype.type
        message(data_type)

        im = envi2.New(basename + '_lonlat', lines=lines, samples=samples, bands=2, \
                       band_names=['longitude', 'latitude'], \
                       wavelength=None, fwhm=None, bbl=None, data_type=data_type, \
                       file_type=ENVI_Standard, interleave=ENVI_BSQ)

        im[0] = rootgrp.groups['location'].variables['lon'][...].data

        # latitude
        im[1] = rootgrp.groups['location'].variables['lat'][...].data
        del im

        # elevation
        message('elevation')
        lines, samples = rootgrp.groups['location'].variables['elev'].get_dims()
        lines, samples = lines.size, samples.size
        message(f"{lines}, {samples}")
        data_type = rootgrp.groups['location'].variables['elev'].dtype.type
        message(data_type)

        im = envi2.New(basename + '_elev', lines=lines, samples=samples, bands=1, \
                       band_names=['elevation'], \
                       wavelength=None, fwhm=None, bbl=None, data_type=data_type, \
                       file_type=ENVI_Standard, interleave=ENVI_BSQ)

        im[0] = rootgrp.groups['location'].variables['elev'][...].data

        # glt_x, int32
        message('glt')
        lines, samples = rootgrp.groups['location'].variables['glt_x'].get_dims()
        lines, samples = lines.size, samples.size
        message(f"{lines}, {samples}")
        data_type = rootgrp.groups['location'].variables['glt_x'].dtype.type
        message(data_type)

        im = envi2.New(basename + '_glt', lines=lines, samples=samples, bands=2, \
                       band_names=['glt_x', 'glt_y'], \
                       wavelength=None, fwhm=None, bbl=None, data_type=data_type, \
                       file_type=ENVI_Standard, interleave=ENVI_BSQ)

        im[0] = rootgrp.groups['location'].variables['glt_x'][...].data

        # glt_y, int32
        im[1] = rootgrp.groups['location'].variables['glt_y'][...].data
        del im
    else:
        raise IOError('No reflectance data found in dataset')

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='convemit.py',
        description='Convert EMIT image to ENVI format.')

#    parser.add_argument('-f', action='store_true', dest='force',
#                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
#    parser.add_argument('-o', dest='output', help='output file name', required=True)

    options = parser.parse_args()

##    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    read_emit_2a(options.input)

