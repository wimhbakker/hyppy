#!/usr/bin/python3
##
##      spatialbinning.py
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

def spatial_binning(fin, fout, 
             binsize=3,
             sort_wavelengths=False, use_bbl=True,
             message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    samples = im.samples // binsize
    lines = im.lines // binsize

    im2 = envi2.New(fout, hdr=im,
                    samples=samples,
                    lines=lines)
##                    interleave=ENVI_bsq, data_type='d')

    if progress:
        progress(0.0)

    for j in range(lines):
        j1 = j * binsize
        j2 = j1 + binsize
        if progress:
            progress(j / float(lines))
        for i in range(samples):
            i1 = i * binsize
            i2 = i1 + binsize
            im2[j, i, :] = np.nanmean(im[j1:j2, i1:i2, :], axis=(0, 1))
            
    if progress:
        progress(1.0)
    
    del im, im2


if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='spatialbinning.py',
        description='Spatial binning using bin size')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')

    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')

    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-x', dest='binsize', type=int, default=3,
                      help='bin size (default 3)')

    options = parser.parse_args()

    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    spatial_binning(options.input, options.output,
               sort_wavelengths=options.sort_wavelengths,
               use_bbl=options.use_bbl,
               binsize=options.binsize)
