#!/usr/bin/python3
##
##      spectralbinning.py
##
##   Created: WHB 20221219
##
## Copyright (C) 2022 Wim Bakker
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

#import math

import envi2
from envi2.constants import *

import numpy as np
np.seterr(all='ignore')

def message(s):
    pass

def spectral_binning(fin, fout, 
             binsize=3,
             sort_wavelengths=False, use_bbl=True,
             message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    imwavelength = list(im.wavelength)

    wavelength = imwavelength[binsize//2:binsize*(im.bands//binsize):binsize]
    bands = len(wavelength)

    lastbinsize = im.bands % binsize

    if lastbinsize > 0:
        wavelength.append(imwavelength[binsize*(im.bands//binsize)+lastbinsize//2])
        bands = bands + 1

    if hasattr(im.header, "default_bands"):
        default_bands = im.header.default_bands
        if default_bands:
            default_bands = [x//binsize for x in default_bands]

    im2 = envi2.New(fout, hdr=im,
                    samples=im.samples,
                    lines=im.lines,
                    bands=bands,
                    wavelength=wavelength,
                    default_bands=default_bands)
##                    interleave=ENVI_bsq, data_type='d')

    if progress:
        progress(0.0)

    for b in range(bands):
        b1 = b * binsize
        b2 = b1 + binsize
        im2[:, :, b] = np.nanmean(im[:, :, b1:b2], axis=2)

        if progress:
            progress(b / float(bands))

    if progress:
        progress(1.0)
    
    del im, im2


if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='spectralbinning.py',
        description='Spectral binning using bin size')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')

    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')

    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-z', dest='binsize', type=int, default=3,
                      help='bin size (default 3)')

    options = parser.parse_args()

    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    spectral_binning(options.input, options.output,
               sort_wavelengths=options.sort_wavelengths,
               use_bbl=options.use_bbl,
               binsize=options.binsize)
