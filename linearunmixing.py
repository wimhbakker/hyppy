#!/usr/bin/python3
## linearunmixing.py
##
## Copyright (C) 2021 Wim Bakker
##    Created: 20210401 WHB, based on sam.py
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
import pysptools.abundance_maps as amp

import envi2
import envi2.spectral
from envi2.constants import *

import ascspeclib

import spectrum

##import envi2.resample

##from numpy import array, nanmin, nanmax, where, isnan
##
##from scipy.stats.stats import nanmean, nanstd

import numpy as np

#import numpy.random

def message(s):
    print(s)

##def classify(nrule, nclass, nquality, mode='min', message=message,
##             progress=None, threshold=None):
##    reverse = mode=='max'
##    
##    irule = envi2.Open(nrule)
##
##    samples = irule.samples
##    lines = irule.lines
##    bands = irule.bands
##    class_names = irule.header.band_names[:]
##
##    if bands<256:
##        data_type = 'u1'
##    else:
##        data_type = 'i'
##
##    iquality = envi2.New(nquality, hdr=irule, bands=1, data_type='d',
##                         band_names=['Class rule value'])
##
##    iclass = envi2.New(nclass, hdr=irule,
##                    file_type=ENVI_Classification,
##                    classes=bands + 1,
##                    class_lookup=numpy.concatenate(((0,0,0), (64+numpy.random.random(3*bands)*192).astype('i'))),
##                    class_names=["Unclassified"] + class_names,
##                    band_names=None,
##                    bands=1, data_type=data_type)
##
##    if progress:
##        progress(0.0)
##    for j in range(lines):
##        if progress:
##            progress(j / float(lines))
##        for i in range(samples):
##            rules = irule[j, i]
##            rules_bands = sorted(zip(rules, list(range(1, bands+1))), reverse=reverse)
##            if threshold:
##                if mode=='min' and rules_bands[0][0] <= threshold:
##                    iclass[j, i] = rules_bands[0][1]
##                elif mode!='min' and rules_bands[0][0] >= threshold:
##                    iclass[j, i] = rules_bands[0][1]
##                else:
##                    iclass[j, i] = 0
##            else:
##                iclass[j, i] = rules_bands[0][1]
##            iquality[j, i] = rules_bands[0][0]
##            
##    if progress:
##        progress(1.0)
##
##    del irule, iclass, iquality

def linear_unmixing(nameIn, nameOut, estimate=None, error=None, speclib=None,
        spec_selection=None, band_selection=None,
          message=message, sort_wavelengths=True,
          use_bbl=True, progress=None, normalize=True):
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
                    description=["Linear Unmixing rule images"],
                    interleave='bsq')


    # go for it!
    if band_selection:
        band_selection = np.array(band_selection)
        M = im[:,:,band_selection]
        U = np.zeros((bands, len(band_selection)), dtype=float)
        
        for i,s in enumerate(spec_selection):
            message(sl.name(s))

            spec = sl.resampled(s, im.wavelength[band_selection])
            U[i,:] = spec
    else:
        M = im[...]
        U = np.zeros((bands, im.bands), dtype=float)

        for i,s in enumerate(spec_selection):
            message(sl.name(s))

            spec = sl.resampled(s, im.wavelength)
            U[i,:] = spec
            
    fcls = amp.FCLS()
    # strange, fcls doesn't accept memmap just ndarray...
    abundance = fcls.map(M.view(type=np.ndarray), U, normalize=normalize)

    im2[...] = abundance

    if estimate:
        lines, samples, bands = M.shape
        if band_selection:
            wavelength = im.wavelength[band_selection]
        else:
            wavelength = im.wavelength
        im_estimate = envi2.New(estimate,
                    hdr=im,
                    lines=lines,
                    samples=samples,
                    bands=bands,
                    data_type='d',
                    default_bands=None,
                    wavelength=wavelength,
                    fwhm=None, bbl=None,
                    description=["estimate"])
        print("matmul")
        im_estimate[...] = np.matmul(abundance, U)

        if error:
            im_error = envi2.New(error,
                        hdr=im,
                        lines=lines,
                        samples=samples,
                        bands=1,
                        data_type='d',
                        default_bands=None,
                        wavelength=wavelength,
                        fwhm=None, bbl=None,
                        description=["error"])

            for j in range(im.lines):
                for i in range(im.samples):
                    if band_selection:
                        spec1 = spectrum.Spectrum(wavelength=wavelength, spectrum=im[j,i,band_selection])
                    else:
                        spec1 = spectrum.Spectrum(wavelength=wavelength, spectrum=im[j,i,:])
                    spec2 = spectrum.Spectrum(wavelength=wavelength, spectrum=im_estimate[j,i,:])
                    im_error[j,i,0] = spec2.SA(spec1)

            del im_error
            
        del im_estimate

    # destroy resources
    del im2, im, M, U

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='linearunmixing.py',
        description='Linear Unmixing (fully constrained).')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-n', action='store_true', dest='normalize',
                      help='normalize input data')
    parser.add_argument('-i', dest='input', help='input ENVI Image or ENVI SpecLib', required=True)
    parser.add_argument('-l', dest='speclib', help='input SpecLib (ENVI or ASCII)', required=True)
    parser.add_argument('-o', dest='output', help='output rule images', required=True)
#    group = parser.add_argument_group('estimate', 'calculate estimate and error')
    parser.add_argument('--estimate', dest='estimate', help='output estimate image (optional)', required=False)
    parser.add_argument('--error', dest='error', help='output error image (optional), calculates spectral angle between INPUT and ESTIMATE', required=False)

    options = parser.parse_args()

    linear_unmixing(options.input, options.output, estimate=options.estimate, error=options.error,
                    speclib=options.speclib,
                    sort_wavelengths=options.sort_wavelengths,
                    use_bbl=options.use_bbl,
                    normalize=options.normalize)
