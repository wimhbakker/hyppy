#!/usr/bin/python3
## merge.py
##
## Copyright (C) 2024 Wim Bakker
##      Created: WHB 20240305, CLI of the tkMerge.py GUI...
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
from envi2.constants import *

#from numpy import *
##from scipy.interpolate import interp1d
##from scipy.optimize import fmin, minimize
##import sys
##
##import time
#from scipy.stats import *

def message(s):
    print(s)

def merge(fnames, fout, sort_wavelengths=False, use_bbl=False, message=message,
            progress=None):
    message("Input file(s): %s" % str(fnames))
    message("Output file: %s" % fout)

    biglist = []
    hdr = None
    for fname in fnames:
        im = envi2.Open(fname,
                        sort_wavelengths=sort_wavelengths,
                        use_bbl=use_bbl)

        if hdr == None:      # copy header info from first image...
            hdr = im.header.copy()
            
        for band in range(im.bands):
            wl = 0
            if hasattr(im, 'wavelength'):
                wl = im.wavelength[band]
            if hasattr(im, 'band_names'):
                bn = im.band_names[band]
            else:
                bn = "Band %d" % (band,)
            biglist.append((wl, fname, band, bn))

        del im

    if sort_wavelengths:
        biglist.sort()
##        print biglist

    bands = len(biglist)

    wavelength = [x[0] for x in biglist]
    if wavelength[0] == 0:
        wavelength = None
        
    band_names = [x[3] for x in biglist]        

    imout = envi2.New(fout,
                      hdr=hdr,
                      bands=bands,
                      wavelength=wavelength,
                      bbl=None,
                      band_names=band_names,
                      fwhm=None,
                      interleave='bsq')

    i = 0
    for wav, fname, band, bn in biglist:
#            print wav, fname, band
        im = envi2.Open(fname,
                        sort_wavelengths=sort_wavelengths,
                        use_bbl=use_bbl)
##            if im.bands==1:
##                imout[i] = im[...]
##            else:
##                imout[i] = im[band]
        imout[i] = im[band]
        i = i+1
        del im

    del imout

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='merge.py',
        description='Merge')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                        help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                        help='use bad band list from the header')
    parser.add_argument('-o', dest='output', help='output image file name', required=True)
    parser.add_argument('filenames', metavar='image', type=str, nargs='+',
                        help='input filenames')

    options = parser.parse_args()

    merge(options.filenames, options.output,
             sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
