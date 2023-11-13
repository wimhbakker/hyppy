#!/usr/bin/python3
## depthoffocus.py
##
## Copyright (C) 2018 Wim Bakker
##  Created: WHB 20181019
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
from scipy.interpolate import interp1d
from scipy.optimize import root
import sys

import pylab as plt
plt.ion()

import time

MAXPIXELSHIFT = 20

def message(s):
    print(s)

## function for autocorrelation...
## s is the shift
def f(s, line1, f1, x):
    x2 = (x + s)
    data2 = f1(x2[MAXPIXELSHIFT:-MAXPIXELSHIFT])
    data1 = line1[MAXPIXELSHIFT:-MAXPIXELSHIFT]

    # determine normalized autocorrelation...
    a = data1
    b = data2

    a = a - a.mean()
    b = b - b.mean()
    c = np.dot(a / np.linalg.norm(a), b / np.linalg.norm(b))
    return c

def depthoffocus(fin, sort_wavelengths=False, use_bbl=False, message=message,
            progress=None):
    try:
        im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    except ValueError as errtext:
        message("Error: %s\n" % (errtext,))
        return
    
    samples = im.samples
    lines = im.lines
    bands = im.bands

    if progress:
        progress(0.0)

    midband = bands // 2
    
    x = np.arange(samples)

    listbands = list()
    listscales = list()
    listcorrs = list()
    bstep = max(1, bands//100)
    message("band step %d" % (bstep,))
    jstep = max(1, lines//100)
    message("line step %d" % (jstep,))
##    for band in [36, 151, 267]: # SWIR3 ~1100, 1750, 2400 nm
    for band in [100, 402, 652]: # VNIR 466, 700, 900 nm
        if progress:
            progress(band/bands)
        js = list()
        roots = list()
        for j in range(0, lines, jstep):
            line1 = im[j, :, band]

            f1 = interp1d(x, line1, kind='quadratic')

            shifts = np.arange(-MAXPIXELSHIFT, MAXPIXELSHIFT, 0.1)
            autocorrs = np.zeros(shifts.shape)
            for s in range(len(shifts)):
                autocorr = f(shifts[s], line1, f1, x)
                autocorrs[s] = autocorr

            autocorrs = autocorrs - 0.95
            fauto = interp1d(shifts, autocorrs, kind='quadratic')

            try:
                r = root(fauto, 1)
                if r.success:
##                    print(j, r.x, fauto(r.x))
                    js.append(j)
                    roots.append(r.x)
            except ValueError:
                pass

        plt.plot(js, roots, label="band %d"%(band,))

    plt.legend()

    
    if progress:
        progress(1.0)

    del im

if __name__ == '__main__':

##    depthoffocus('/data2/data/SWIRtest/2018-10-23_14-37-03_SWIR_depthoffocus/2018-10-23_14-37-03_SWIR_depthoffocus_dwref2_fx8')
##    depthoffocus('/data2/data/SWIRtest/2018-10-23_07-54-51_SWIR_depthoffocus/2018-10-23_07-54-51_SWIR_depthoffocus_dwref2_fx8')
    depthoffocus('/data2/data/VNIRtest/DepthOfField/2018-12-04_11-26-47_VNIR_depthoffield/2018-12-04_11-26-47_VNIR_depthoffield_dwref2_crd')
##    depthoffocus('/data2/data/VNIRtest/DepthOfField/2018-12-04_15-08-55_VNIR_depthoffield/2018-12-04_15-08-55_VNIR_depthoffield_dwref2.raw')
##    depthoffocus('/data2/data/VNIRtest/DepthOfField/2018-12-04_15-23-41_VNIR_depthoffield/2018-12-04_15-23-41_VNIR_depthoffield_dwref2.raw')

    sys.exit(0)
    
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='keystone.py',
        description='Determine keystone')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-i', dest='input', help='input image file name', required=True)

    options = parser.parse_args()

    keystone(options.input, sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
