#!/usr/bin/python3
##
##      destripe3d.py
##
##   Created: WHB 20160301
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

import math

import envi2
from envi2.constants import *

import numpy as np
np.seterr(all='ignore')

def message(s):
    pass

def resample(fin, fout, 
             stepsize=2,
             sort_wavelengths=False, use_bbl=True,
             message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im,
                    samples=math.ceil(im.samples/stepsize),
                    lines=math.ceil(im.lines/stepsize))
##                    interleave=ENVI_bsq, data_type='d')

    if progress:
        progress(0.0)

    im2[...] = im[::stepsize, ::stepsize, :] 

##    for band in range(1, im.bands-1):
##        if progress:
##            progress(band / float(im.bands))
##
##        # samples
##        for x in range(1, im.samples-1):
##            
##            # lines
##            cube = im[:, x-1:x+2, band-1:band+2]
##            xs = cube[:, 1, 1]
##            ys = np.nanmean(cube, axis=(1,2))
##            diff = ys - xs
##
##            mean = np.nanmean(diff)
##            stddev = np.sqrt(np.nanmean(np.square(diff)) - mean**2)
##            offset[x, band] = mean
##            deviat[x, band] = stddev
##
##            if np.fabs(mean) > maxmean or stddev > maxstddev or not np.isfinite(mean) or not np.isfinite(stddev):
##                offset[x, band] = np.nan
##                deviat[x, band] = np.nan
##                bad_pixels.append((x, band))
##                message("(%d, %d) %f %f" % (x, band, mean, stddev))

    if progress:
        progress(1.0)
    
    del im, im2


if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='resample.py',
        description='Resampling using step size')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')

    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')

    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-p', dest='stepsize', type=int, default=2,
                      help='stepsize (default 2)')

    options = parser.parse_args()

    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    resample(options.input, options.output,
               sort_wavelengths=options.sort_wavelengths,
               use_bbl=options.use_bbl,
               stepsize=options.stepsize)
