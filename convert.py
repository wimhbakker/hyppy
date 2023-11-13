#!/usr/bin/python3
## convert.py
##
## Copyright (C) 2010 Wim Bakker
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
##     Hengelosestraat 99
##     7514 AE Enschede
##     Netherlands
##

import os
import envi2
from envi2.constants import *

# Try to import from Pillow or PIL
try:
    from PIL import Image
except ImportError as errtext:
    import Image

import numpy
import sys

import worldfile

##dtypedict = {
##    numpy.dtype('uint8'):'u1',
##    numpy.dtype('int16'):'h',
##    numpy.dtype('int32'):'i',
##    numpy.dtype('float32'):'f',
##    numpy.dtype('float64'):'d',
##    numpy.dtype('uint16'):'H',
##    numpy.dtype('uint32'):'I',
##    numpy.dtype('int64'):'l',
##    numpy.dtype('uint64'):'L'}

def message(s):
    print(s)

def guess_units(x, y):
    return 'Degrees' if abs(x)<200 and abs(y)<100 else 'Meters'

def image2envi(fin, fout, message=message):

    try:
        im = Image.open(fin)
    except Exception as errtext:
        message("Exception: %s\n" % (errtext,))
        return
    
    samples, lines = im.size

    band_names = None
    default_bands = None

    if im.mode=='RGB':
        bands = 3
        band_names = ['R', 'G', 'B']
        default_bands = [1, 2, 3]
    elif im.mode=='L':
        bands = 1
        band_names = [os.path.basename(fin)]
    elif im.mode.startswith('I'):
        bands = 1
        band_names = [os.path.basename(fin)]
    elif im.mode.startswith('F'):
        bands = 1
        band_names = [os.path.basename(fin)]
    elif im.mode=='P':
        bands = 3
        im = im.convert('RGB')
        band_names = ['R', 'G', 'B']
        default_bands = [1, 2, 3]
    elif im.mode=='RGBA':
        bands = 4
        band_names = ['R', 'G', 'B', 'A']
        default_bands = [1, 2, 3]
    elif im.mode=='CMYK':
        bands = 4
        band_names = ['C', 'M', 'Y', 'K']
    elif im.mode=='1':
        bands = 1
        band_names = [os.path.basename(fin)]
    else:
        raise ValueError("Unsupported image mode '%s'" % (im.mode,))
    
    ima = numpy.asarray(im)

    dtype = ima.dtype

##    try:
##        data_type = dtypedict[dtype]
##    except KeyError:
##        raise KeyError("Data type not understood '%s'" % (dtype,))

    data_type = dtype

    # See if we can find coordinates with this image
    map_info = None

    # Try GeoTIFF first
    if os.path.splitext(fin)[1].lower() in ['.tif', '.tiff']:
        try:
            # map info obtained from GeoTIFF tags (don't ask!)
            map_info = ['Arbitrary', 1.0, 1.0, im.ifd[33922][3], im.ifd[33922][4],
                        im.ifd[33550][0], im.ifd[33550][1], 1,
                        'units=%s' % (guess_units(im.ifd[33922][3], im.ifd[33922][4]),)]
        except KeyError:
            map_info = None

    # Try to find World File
    if not map_info:
        tup = worldfile.worldfile_get(fin)
        if tup:
            A, D, B, E, C, F = tup
            # parameter 8: 1=map-based, 0=pixel-based, WTF?
            map_info = ['Arbitrary', 1.0, 1.0, C, F, A, -E, 1,
                        'units=%s' % (guess_units(C, F),)]

    # Byte order of this box
    if sys.byteorder == 'little':
        byte_order = 0
    else:
        byte_order = 1

    # Create new image
    try:
        im2 = envi2.New(fout, file_type=ENVI_Standard,
                    samples=samples, lines=lines, bands=bands,
                    data_type=data_type, interleave='bip',
                        byte_order=byte_order,
                    bbl=None,
                    band_names=band_names,
                    wavelength=None,
                    fwhm=None, default_bands=default_bands,
                    map_info=map_info)
    except ValueError as errtext:
        message("ValueError: %s" % (errtext,))
        return

    # Copy image data
    if len(ima.shape)==2:
        im2[:,:,0] = ima[...]
    else:
        im2[...] = ima[...]

    del im2
    del im

if __name__ == '__main__':
##    print "Run this module using tkConvert!"

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='convert.py',
##        usage='convert.py -f -i input -o output',
        description='Convert image to ENVI format.')

##    parser.add_option('-s', action='store_true', dest='sort_wavelengths',
##                      help='sort bands on wavelength')
##    parser.add_option('-b', action='store_true', dest='use_bbl',
##                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

##    parser.set_defaults(force=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    image2envi(options.input, options.output)
