#!/usr/bin/python3
## flip.py
##
## Copyright (C) 2018 Wim Bakker
##      Created: WHB 20180927
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

import envi2
##from envi2.constants import *

import numpy as np

import sys

def message(s):
    print(s)

def flip(fin, fout, mode='x',
         sort_wavelengths=False, use_bbl=False, message=message,
         progress=None, full=False):
    try:
        im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    except ValueError as errtext:
        message("Error: %s\n" % (errtext,))
        return
    
    samples = im.samples
    lines = im.lines
    bands = im.bands

    # Create new image
    try:
        im2 = envi2.New(fout, hdr=im)
    except Exception as errtext:
        message("Error: %s" % (errtext,))
        return

    if mode=='x':
        im2[...] = np.flip(im[...], 1)
    elif mode=='y':
        im2[...] = np.flip(im[...], 0)
    elif mode=='z':
        im2[...] = np.flip(im[...], 2)
    else:
        message("Unknown mode: %s\n" % (mode,))
        return
    
    del im
    del im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='flip.py',
        description='Flip image')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite of existing output file')
    parser.add_argument('-i', dest='input', help='input image file name', required=True)
    parser.add_argument('-o', dest='output', help='output image file name', required=True)
    parser.add_argument('-m', dest='mode', choices=('x', 'y', 'z'), default='x',
               help='flip mode: x (flip left and right (default)), y (flip up and down), z (flip spectrum)')

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use -f to overwrite.")

    flip(options.input, options.output, mode=options.mode,
          sort_wavelengths=options.sort_wavelengths,
          use_bbl=options.use_bbl)
