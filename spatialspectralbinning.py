#!/usr/bin/python3
##
##      spatialspectralbinning.py
##
##   Created: WHB 20221220
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

def spatial_spectral_binning(fin, fout, 
             xybinsize=3, zbinsize=11,
             sort_wavelengths=False, use_bbl=True,
             message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    imwavelength = list(im.wavelength)

    wavelength = imwavelength[zbinsize//2:zbinsize*(im.bands//zbinsize):zbinsize]
    bands = len(wavelength)

    lastbinsize = im.bands % zbinsize

    if lastbinsize > 0:
        wavelength.append(imwavelength[zbinsize*(im.bands//zbinsize)+lastbinsize//2])
        bands = bands + 1

    if hasattr(im.header, "default_bands"):
        default_bands = im.header.default_bands
        if default_bands:
            default_bands = [x//zbinsize for x in default_bands]

    samples = im.samples // xybinsize
    lines = im.lines // xybinsize

    im2 = envi2.New(fout, hdr=im,
                    samples=samples,
                    lines=lines,
                    bands=bands,
                    wavelength=wavelength,
                    default_bands=default_bands)
##                    interleave=ENVI_bsq, data_type='d')

    if progress:
        progress(0.0)

    for b in range(bands):
        if progress:
            progress(b / float(bands))
        b1 = b * zbinsize
        b2 = b1 + zbinsize
        im2band = np.nanmean(im[:, :, b1:b2], axis=2)
        for j in range(lines):
            j1 = j * xybinsize
            j2 = j1 + xybinsize
            for i in range(samples):
                i1 = i * xybinsize
                i2 = i1 + xybinsize
                im2[j, i, b] = np.nanmean(im2band[j1:j2, i1:i2])

    if progress:
        progress(1.0)
    
    del im, im2


if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='spatialspectralbinning.py',
        description='Spatial spectral binning using xy and z bin sizes')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')

    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')

    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-x', dest='xybinsize', type=int, default=3,
                      help='xy bin size (default 3)')
    parser.add_argument('-z', dest='zbinsize', type=int, default=3,
                      help='z bin size (default 3)')

    options = parser.parse_args()

    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    spatial_spectral_binning(options.input, options.output,
                             sort_wavelengths=options.sort_wavelengths,
                             use_bbl=options.use_bbl,
                             xybinsize=options.xybinsize,
                             zbinsize=options.zbinsize)
