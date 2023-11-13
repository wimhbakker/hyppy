#!/usr/bin/python3
## keystone.py
##
## Copyright (C) 2018 Wim Bakker
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
from scipy.optimize import fmin
import sys

import pylab as plt
plt.ion()

import time

import csv
def savetxt(fname, someiterable):
    with open(fname, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=' ', quoting=csv.QUOTE_NONE)
        writer.writerows(someiterable)

def message(s):
    print(s)

## function for minimization process...
## s is the scale factor
def f(s, line1, line2, f1, f2, x):
    s = s[0]

    mid = (len(x) - 1) / 2
    if s<1:
        x2 = s * (x - mid) + mid
        data2 = f2(x2)
        data1 = line1
    else:
        x1 = (x - mid) / s + mid
        data1 = f1(x1)
        data2 = line2

    # determine normalized autocorrelation...
    a = data1
    b = data2
##    a = (a - np.mean(a)) / (np.std(a) * len(a))
##    b = (b - np.mean(b)) / (np.std(b))
##    c = 1 - np.correlate(a, b)[0] # turn maximum into minimum...

    a = a - a.mean()
    b = b - b.mean()
    c = -np.dot(a / np.linalg.norm(a), b / np.linalg.norm(b))
    return c

def keystone(fin, fout=None, sort_wavelengths=False, use_bbl=False, message=message,
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
    bstep = 1
    message("band step %d" % (bstep,))
    jstep = max(1, lines//100)
    message("line step %d" % (jstep,))
    for band in range(0, bands, bstep):
        if progress:
            progress(band/bands)
        scales = list()
        corrs = list()
        for j in range(0, lines, jstep):
            line1 = im[j, :, midband]
            line2 = im[j, :, band]

            f1 = interp1d(x, line1, kind='quadratic')
            f2 = interp1d(x, line2, kind='quadratic')

            result = fmin(f, 1.0, (line1, line2, f1, f2, x), ftol=0.000001, full_output=1, disp=0)
            s_max = result[0][0]
            c_max = -result[1] # turn minimum into maximum...

            scales.append(s_max)
            corrs.append(c_max)

        corrsmean = np.array(corrs).mean()
        if corrsmean>0.9:
            listbands.append(band)
            listscales.append(np.array(scales).mean())
            listcorrs.append(corrsmean)
    
##    plt.plot(listbands, listscales, label="scale")
##    plt.plot(listbands, listcorrs, label="correlation")

    # calculate keystone in pixels...
    coefs = plt.polyfit(listbands, listscales, 3, full=False)
    allbands = range(bands)
    yy = plt.polyval(coefs, allbands) # these are the estimated scales
##    plt.plot(allbands, yy, label="fitted scale")

    measured_bands = listbands
    measured_wavelengths = im.wavelength[listbands]
    measured_keystone = (np.array(listscales)/yy[0]-1)*samples/2

    savetxt(fin+'_measured_keystone.txt', zip(measured_bands, measured_wavelengths, measured_keystone))
    plt.plot(measured_wavelengths, measured_keystone, 'k', lw=0.2, label="measured keystone")

    fitted_bands = allbands
    fitted_wavelengths = im.wavelength[allbands]
    fitted_keystone = (yy/yy[0]-1)*samples/2
    
    savetxt(fin+'_fitted_keystone.txt', zip(fitted_bands, fitted_wavelengths, fitted_keystone))
    plt.plot(fitted_wavelengths, fitted_keystone, 'k', label="fitted keystone in pixels")
    
    message("Measured keystone in pixels over all bands, from left to center or from center to right: %0.1f pixels" %
            (np.fabs((yy[0]/yy[bands-1]-1)*samples/2),))

    plt.xlabel("wavelength [nm]")
    plt.ylabel("keystone in pixels")
##    plt.title("Keystone per band")
##    plt.legend(loc=0)
    
    if progress:
        progress(1.0)

    if fout:
        message("Correcting keystone...")
        # Create new image
        try:
            im2 = envi2.New(fout, value=np.nan, hdr=im)
        except Exception as errtext:
            message("Error: %s" % (errtext,))
            return

        if progress:
            progress(0.0)

        for band in range(bands):
            if progress:
                progress(band/bands)

            s = yy[band] # the scale for this band
            mid = (len(x) - 1) / 2
            xx = s * (x - mid) + mid
##                xx = (x - mid) / s + mid
            xx = xx.clip(0, samples-1)

            for j in range(lines):
                line1 = im[j, :, band]

                f1 = interp1d(x, line1, kind='quadratic')

                im2[j, :, band] = f1(xx)

        del im2

        if progress:
            progress(1.0)

    del im

if __name__ == '__main__':
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
    parser.add_argument('-o', dest='output', help='output image file name', required=False)

    options = parser.parse_args()

    keystone(options.input, fout=options.output, sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
