#!/usr/bin/python3
## smile.py
##
## Copyright (C) 2018 Wim Bakker
##      Created: WHB 20180912
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

import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import fmin, minimize
import sys

import time

def message(s):
    print(s)

## function for minimization process...
## s is the shift
def f(s, spec1, f2, z):
    gain = s[0]
    shift = s[1]

    z2 = (gain*z + shift).clip(0, len(z)-1)
    data1 = spec1[z][2:-2] # cut off some of the edges...
    data2 = f2(z2)[2:-2]
    
##    z2 = gain*z + shift
##
##    overlap = np.where((0<=z2)&(z2<=(len(z)-1)))
##
##    data1 = spec1[z[overlap]]
##    data2 = f2(z2[overlap])

    # determine normalized autocorrelation...
    a = data1
    b = data2
##    a = (a - np.mean(a)) / (np.std(a) * len(a))
##    b = (b - np.mean(b)) / (np.std(b))
##    c = -np.correlate(a, b)[0] # turn maximum into minimum...

    a = a - a.mean()
    b = b - b.mean()
    c = -np.dot(a / np.linalg.norm(a), b / np.linalg.norm(b))
    return c

def smile(fin, fout, sort_wavelengths=False, use_bbl=False, message=message,
            progress=None, full=False):
    try:
        im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    except ValueError as errtext:
        message("Error: %s\n" % (errtext,))
        return
    
    samples = im.samples
    lines = im.lines
    bands = im.bands

    # Create new image for recording smile, x=sample, y=band!
    try:
        im2 = envi2.New(fout, value=np.nan, samples=samples, lines=bands, bands=1,
                        file_type = ENVI_Standard, byte_order=0,
                        interleave='bsq', data_type='d')
    except Exception as errtext:
        message("Error: %s" % (errtext,))
        return

##    midsample = samples // 2
##    midsample = 3
##    message("midsample: %d" % (midsample,))
    
    fullz = np.arange(bands)

    jstep = 1 if full else max(1, lines//20)
    message("line step %d" % (jstep,))

    if progress:
        progress(0.0)

    for i in range(samples):
        if progress:
            progress(i/samples)

        count = 0
        accu_smile = np.zeros(fullz.shape)
        for j in range(0, lines, jstep):
            if jstep==1:
                spec1 = im[j, 0, :]
                spec2 = im[j, i, :]
            else:
                spec1 = np.mean(im[j:j+jstep, 0, :], axis=(0,))
                spec2 = np.mean(im[j:j+jstep, i, :], axis=(0,))

##            f1 = interp1d(fullz, spec1, kind='quadratic')
            f2 = interp1d(fullz, spec2, kind='cubic') # spec2 interpolated with cubic spline...

##            result = fmin(f, [1.0, 0.0], (spec1, f2, fullz), ftol=0.000001, full_output=1, disp=0)
##            g_max = result[0][0]
##            s_max = result[0][1]
##            c_max = -result[1] # turn minimum into maximum...

            result = minimize(f, [1.0, 0.0], (spec1, f2, fullz))
            g_max = result.x[0]
            s_max = result.x[1]
            c_max = -result.fun # turn minimum into maximum...

            if c_max > 0.9: # only record good correlations...
                accu_smile = accu_smile + ((g_max - 1) * fullz + s_max)
                count = count + 1

        im2[:, i] = accu_smile[:, np.newaxis] / count
    
    if progress:
        progress(1.0)

    del im

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='smile.py',
        description='Determine smile')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-i', dest='input', help='input image file name', required=True)
    parser.add_argument('-o', dest='output', help='output smile file name', required=True)

    options = parser.parse_args()

    smile(options.input, options.output,
          sort_wavelengths=options.sort_wavelengths,
          use_bbl=options.use_bbl)

##    smile('/data2/data/SWIRtest/2018-08-06_15-05-07_SWIR_smile/2018-08-06_15-05-07_SWIR_smile_dwref2_fx8',
##          use_bbl=True)
