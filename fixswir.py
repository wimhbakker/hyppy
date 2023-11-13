#!/usr/bin/python3
## fixswir.py
##
## Copyright (C) 2018 Wim Bakker
##      Created: WHB 20180913
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

import numpy
import sys

def message(s):
    print(s)

def checkstats(im):
    stats = numpy.zeros(8)
    line = numpy.mean(im[...], axis=(0, 2))
    for i in range(8):
        stats[i] = line[i::8].mean()
    m = stats.mean()
    s = stats.std()

    start = numpy.where(numpy.fabs(stats-m)>s)[0][0]

    return start
    
def fixswir(fin, fout, start=1, sort_wavelengths=False, use_bbl=False, message=message,
            progress=None):
    try:
        im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    except ValueError as errtext:
        message("Error: %s\n" % (errtext,))
        return

    if start is None:
        start = checkstats(im)
        message("First bad sample detected at x=%d" % (start,))
    
    samples = im.samples
    lines = im.lines
    bands = im.bands

    # Create new image
    try:
        im2 = envi2.New(fout, value=numpy.nan, hdr=im)
    except Exception as errtext:
        message("Error: %s" % (errtext,))
        return

    message("Copying data...")
    im2[...] = im[...]

    message("Processing...")
    if progress:
        progress(0.0)

## Slow version...
##    for j in range(lines):
##        if progress:
##            progress(j / float(lines))
##        for i in range(1, samples, 8):
##            im2[j, i] = (im[j, i-1] + im[j, i+1]) / 2

    # Fast version...
    for i in range(start, samples, 8):
        if progress:
            progress(i / samples)
        if i==0:
            im2[:, i] = im[:, i+1]
        elif i==samples-1:
            im2[:, i] = im[:, i-1]
        else:
            im2[:, i] = (im[:, i-1] + im[:, i+1]) / 2

    if progress:
        progress(1.0)

    message("Saving...")
    del im2
    del im

if __name__ == '__main__':
##    GUI is called tkFixSWIR

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='fixswir.py',
        description='Fix unruly samples of SWIR camera.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input image file name', required=True)
    parser.add_argument('-o', dest='output', help='output image file name', required=True)

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use -f to overwrite.")

    fixswir(options.input, options.output, sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
