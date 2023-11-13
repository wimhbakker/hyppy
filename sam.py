#!/usr/bin/python3
## sam.py
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

# load support for ENVI images
import os

import envi2
import envi2.spectral
from envi2.constants import *

import ascspeclib

##import envi2.resample

##from numpy import array, nanmin, nanmax, where, isnan
##
##from scipy.stats.stats import nanmean, nanstd

import numpy
import numpy.random

def message(s):
    print(s)

def classify(nrule, nclass, nquality, mode='min', message=message,
             progress=None, threshold=None, thresholds=None, class_lookup=None):
    reverse = mode=='max'
    
    irule = envi2.Open(nrule)

    samples = irule.samples
    lines = irule.lines
    bands = irule.bands
    class_names = irule.header.band_names[:]

    if bands<256:
        data_type = 'u1'
    else:
        data_type = 'i'

    iquality = envi2.New(nquality, hdr=irule, bands=1, data_type='d',
                         band_names=['Class rule value'])

    if not class_lookup:
        class_lookup = numpy.concatenate(((0,0,0), (64+numpy.random.random(3*bands)*192).astype('i')))
    else:
        class_lookup = numpy.concatenate(class_lookup)
    
    iclass = envi2.New(nclass, hdr=irule,
                    file_type=ENVI_Classification,
                    classes=bands + 1,
                    class_lookup=class_lookup,
                    class_names=["Unclassified"] + class_names,
                    band_names=None,
                    bands=1, data_type=data_type)

    if progress:
        progress(0.0)
    for j in range(lines):
        if progress:
            progress(j / float(lines))
        for i in range(samples):
            rules = irule[j, i]
            if mode=='min':
                if thresholds:
                    rules = numpy.where(rules<thresholds, rules, +numpy.inf)
                rules_bands = sorted(zip(rules, list(range(1, bands+1))), reverse=False)
            else: # mode=='max'
                if thresholds:
                    rules = numpy.where(rules>thresholds, rules, -numpy.inf)
                rules_bands = sorted(zip(rules, list(range(1, bands+1))), reverse=True)

            if numpy.isfinite(rules_bands[0][0]):
                iclass[j, i] = rules_bands[0][1]
                iquality[j, i] = rules_bands[0][0]
            else:
                iclass[j, i] = 0
                iquality[j, i] = numpy.nan
            
    if progress:
        progress(1.0)

    del irule, iclass, iquality

def sam(nameIn, nameOut, speclib=None, mode='SAM',
        spec_selection=None, band_selection=None,
          message=message, sort_wavelengths=True,
          use_bbl=True, progress=None):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples

    # get SPECLIB data
    if os.path.isdir(speclib):
        sl = ascspeclib.AscSpeclib(speclib)
    else:
        sl = envi2.Speclib(speclib)

    if not spec_selection:
        spec_selection = list(range(len(sl)))

    band_names = [sl.name(i) for i in spec_selection]

    bands = len(spec_selection)

    # set up rule image, output ENVI image
    im2 = envi2.New(nameOut,
                    hdr=im,
                    bands=bands,
                    data_type='d',
                    band_names=band_names,
                    default_bands=None,
                    wavelength=None,
                    fwhm=None, bbl=None,
                    description=["%s rule images" % (mode,)],
                    interleave='bsq')

    # set mode
    if mode=='SAM':
        diff_func = envi2.spectral.spectral_angle
    elif mode=='BC':
        diff_func = envi2.spectral.bray_curtis_distance
    elif mode=='SID':
        diff_func = envi2.spectral.spectral_information_divergence
    elif mode=='ED':
        diff_func = envi2.spectral.euclidean_distance
    elif mode=='ID':
        diff_func = envi2.spectral.intensity_difference
    else:
        raise ValueError("Unknown mode '%s'" % (mode,))

    message("Using the '%s' distance measure" % (mode,))

    # go for it!
    b = 0
    if band_selection:
        band_selection = numpy.array(band_selection)
        for s in spec_selection:
            message(sl.name(s))

            spec = sl.resampled(s, im.wavelength)[band_selection]
##            spec = sl[s].resample(im.wavelength[band_selection])
            
            if progress:
                progress(0.0)
            for j in range(lines):
                if progress:
                    progress(j / float(lines))
                for i in range(samples):
                    im2[j, i, b] = diff_func(im[j, i][band_selection], spec)

            b = b + 1

            if progress:
                progress(1.0)
    else:
        for s in spec_selection:
            message(sl.name(s))

            spec = sl.resampled(s, im.wavelength)
##            spec = sl[s].resample(im.wavelength)
            
            if progress:
                progress(0.0)
            for j in range(lines):
                if progress:
                    progress(j / float(lines))
                for i in range(samples):
                    im2[j, i, b] = diff_func(im[j, i], spec)

            b = b + 1

            if progress:
                progress(1.0)

    # destroy resources
    del im2, im

if __name__ == '__main__':
    print("Run this module using tkSAM!")
