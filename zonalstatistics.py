#!/usr/bin/python3
## zonalstatistics.py
##
## Copyright (C) 2020 Wim Bakker
##  Created: 20200925 WHB
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

# load support for ENVI images
import envi2
from envi2.constants import *
#import spectrum

import numpy

SEP = '_'
EXTENSION = '.txt'

# mean minus two sdtdev
def m_min_2s(a, axis=0):
    return numpy.mean(a, axis=axis) - 2*numpy.std(a, axis=axis)

# mean plus two sdtdev
def m_plus_2s(a, axis=0):
    return numpy.mean(a, axis=axis) + 2*numpy.std(a, axis=axis)

methods = {'max':numpy.max, 'mean':numpy.mean, 'median':numpy.median, 'min':numpy.min, 'std':numpy.std, 'sum':numpy.sum, \
           'm-2s':m_min_2s, 'm+2s':m_plus_2s}

def message(s):
    print(s)

### Version all at once...
##def zonal_statistics_fast(zones, nameIn,
##                  sort_wavelengths=False,
##                  use_bbl=False,
##                    method='mean',
##                     message=message,
##                     progress=None):
##    # get ENVI image data
##    imzones = envi2.Open(zones)
##    if imzones.bands>1:
##        raise ValueError('Zones image must have one band only')
##    
##    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
##
##    if imzones.samples!=im.samples or imzones.lines!=im.lines:
##        raise ValueError('Zones image and input image must have equal spatial dimensions')
##
####    bands = im.bands
##
####    for classvalue in range(imzones.header.classes):
##    for classvalue in sorted(set(imzones[...].flatten())): # check which class values occur in the zones image...
##        indices = numpy.where(imzones[...].flatten()==classvalue)
##        result = methods[method](im[...].reshape((im.lines*im.samples,im.bands))[indices], axis=0)
##
##        classname = imzones.header.class_names[classvalue] if imzones.header.file_type==ENVI_Classification else classvalue
##
##        try:
##            textfile = nameIn + SEP + classname + SEP + method + EXTENSION
##            f = open(textfile, 'w')
##        except FileNotFoundError:
##            textfile = nameIn + SEP + classvalue + SEP + method + EXTENSION
##            f = open(textfile, 'w')
##        
##        message('created: ' + textfile)
##
##        print('# Zonal statistics', file=f)
##        print('# Zones: %s' % (zones,), file=f)
##        print('# Image: %s' % (nameIn,), file=f)
##        print('# Sort wavelength: %s' % (sort_wavelengths,), file=f)
##        print('# Use BBL: %s' % (use_bbl,), file=f)
##        print('# Method: %s' % (method,), file=f)
##        print('# Zone: %s' % (classname,), file=f)
##        print('# Zone value: %d' % (classvalue,), file=f)
##
##        if hasattr(im, 'wavelength'):
##            if im.bands==1:
##                print('%f %f' % (im.wavelength[0], result), file=f)
##            else:
##                for b in range(im.bands):
##                    print('%f %f' % (im.wavelength[b], result[b]), file=f)
##        else:
##            if im.bands==1:
##                print('%d %f' % (0, result), file=f)
##            else:
##                for b in range(im.bands):
##                    print('%d %f' % (b, result[b]), file=f)
##        f.close()
##
##    # destroy resources
##    del imzones, im

### Version per band...
def zonal_statistics(zones, nameIn,
                  sort_wavelengths=False,
                  use_bbl=False,
                    method='mean',
                     message=message,
                     progress=None):
    # get ENVI image data
    imzones = envi2.Open(zones)
    if imzones.bands>1:
        raise ValueError('Zones image must have one band only')
    
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if imzones.samples!=im.samples or imzones.lines!=im.lines:
        raise ValueError('Zones image and input image must have equal spatial dimensions')

##    bands = im.bands

##    for classvalue in range(imzones.header.classes):
    for classvalue in sorted(set(imzones[...].flatten())): # check which class values occur in the zones image...
        indices = numpy.where(imzones[...].flatten()==classvalue)

        classname = imzones.header.class_names[classvalue] if imzones.header.file_type==ENVI_Classification else "%g" % (classvalue,)

        try:
            textfile = nameIn + SEP + classname + SEP + method + EXTENSION
            f = open(textfile, 'w')
        except FileNotFoundError:
            textfile = nameIn + SEP + ("%g" % (classvalue,)) + SEP + method + EXTENSION
            f = open(textfile, 'w')
        
        message('created: ' + textfile)

        print('# Zonal statistics', file=f)
        print('# Zones: %s' % (zones,), file=f)
        print('# Image: %s' % (nameIn,), file=f)
        print('# Sort wavelength: %s' % (sort_wavelengths,), file=f)
        print('# Use BBL: %s' % (use_bbl,), file=f)
        print('# Method: %s' % (method,), file=f)
        print('# Zone name: %s' % (classname,), file=f)
        print('# Zone value: %g' % (classvalue,), file=f)
        print('# Zone pixel count: %d' % (len(indices[0]),), file=f)

        if progress:
            progress(0.0)

        for b in range(im.bands):
            if progress:
                progress(b / float(im.bands))

            result = methods[method](im[b].flatten()[indices], axis=0)

            if hasattr(im, 'wavelength'):
                print('%f %f' % (im.wavelength[b], result), file=f)
            else:
                print('%d %f' % (b, result), file=f)

        if progress:
            progress(1.0)

        f.close()

    # destroy resources
    del imzones, im

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='zonalstatistics.py',
        description='Calculate zonal statistics (as tables)')

    parser.add_argument('-z', dest='zones', required=True, help='zones file')
    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-b', action='store_true', dest='use_bbl', help='use bad band list (on input)')
    parser.add_argument('-s', action='store_true', dest='sort_wavelengths', help='sort wavelengths (on input)')
    parser.add_argument('-m', dest='method', choices=methods.keys(), default='mean', help='method (default \'mean\')')

    options = parser.parse_args()

    zonal_statistics(options.zones, options.input,
                  sort_wavelengths=options.sort_wavelengths,
                  use_bbl=options.use_bbl,
                     method=options.method)

    sys.exit(0)
