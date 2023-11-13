#!/usr/bin/python3
## spectralgradient.py
##
## Copyright (C) 2020 Wim Bakker
##  Modified: 
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

# load support for ENVI images
import envi2
#import spectrum

import numpy

def message(s):
    pass

def spectralgradient(nameIn, nameOut,
                  message=message, sort_wavelengths=True,
                  use_bbl=True, progress=None):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples

    # set up output ENVI image
    im2 = envi2.New(nameOut, value=numpy.nan,
                     hdr=im.header, data_type='d',
                     fwhm=None, bbl=None)

    # go for it!
    if progress:
        progress(0.0)
    for j in range(lines):
        if progress:
            progress(j / float(lines))
        im2[j, :, :] = numpy.gradient(im[j, :, :], axis=-1)

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='spectralgradient.py',
        description='Calculate spectral gradient')

    parser.add_argument('-b', action='store_true', dest='use_bbl', help='use bad band list')
    parser.add_argument('-s', action='store_true', dest='sort_wavelengths', help='sort wavelengths')
    parser.add_argument('-f', action='store_true', dest='force', help='force overwrite of output file')
    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-o', dest='output', required=True, help='ouput file')

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use option -f to overwrite.")

    spectralgradient(options.input, options.output,
                  sort_wavelengths=options.sort_wavelengths,
                  use_bbl=options.use_bbl)

    sys.exit(0)
