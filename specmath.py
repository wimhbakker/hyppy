#!/usr/bin/python3
## specmath.py
##
## Copyright (C) 2018 Wim Bakker
##      Created: WHB 20181008, CLI of the SpecMath GUI...
##      Modified: WHB 20240327, added mask
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

import collections

import envi2
from envi2.constants import *

import numpy
##from scipy.interpolate import interp1d
##from scipy.optimize import fmin, minimize
##import sys
##
##import time

from spectrum import Spectrum

def message(s):
    print(s)

def specmath(fin, fout, expression, maskfile=None, data_type=None,
             sort_wavelengths=False, use_bbl=False, message=message,
             progress=None):
    message("Input file(s): %s" % fin)
    message("Output file: %s" % fout)

    fnames = fin

    hdr = None
    imlist = []
    for fname in fnames:
        im = envi2.Open(fname,
                        sort_wavelengths=sort_wavelengths,
                        use_bbl=use_bbl)

        if hdr is None:      # copy header info from first image...
            hdr = im.header.copy()
            if data_type is None:
                data_type = hdr.data_type

        imlist.append(im)

    mask = None
    if maskfile:
        mask = envi2.Open(maskfile)
        assert mask.lines==hdr.lines and mask.samples==hdr.samples, "Mask extent must match image extent."

    message('Evaluating: %s' % (expression,))
    ## Try the expression once for the very first pixel
    for k in range(len(imlist)):
        myS = Spectrum(wavelength=imlist[k].wavelength, spectrum=imlist[k][0, 0],
                       wavelength_units=getattr(imlist[k].header, 'wavelength_units', None))
        ## Construct a variable name
        globals()['S%d' % (k+1,)] = myS

    try:
        ## result can be Spectrum, tuple or value...
        result = eval(expression)
    except Exception as e:
        message(repr(e))

    wavelength = None
    band_names = None
    try:
        if isinstance(result, Spectrum): # only get these if it's a Spectrum
            bands = len(result)
            if numpy.issubdtype(result.wavelength.dtype, str):
                band_names = result.wavelength
            else:
                wavelength = result.wavelength
        else:
            bands = len(numpy.ndarray.flatten(result))
    except TypeError:
        bands = 1

    message("Output image will have %d band(s)" % (bands,))

    imout = envi2.New(fout, value=numpy.nan,
                      hdr=hdr, data_type='f' if data_type=='f' else 'd', # data_type=data_type,
                      bands=bands,
                      wavelength=wavelength,
                      bbl=None,
                      band_names=band_names,
                      fwhm=None,
                      interleave='bip',
                      default_bands=None,
                      description=['spectral math: %s' % (expression,)])

    if progress: progress(0.0)
    ## Loop over lines and samples
    lines = imlist[0].lines
    for j in range(lines):
        if progress: progress(j / float(lines-1))
        for i in range(imlist[0].samples):
            if not mask or mask[j, i, 0]:
                ## Loop over the set of input images to collect spectra
                for k in range(len(imlist)):
    ##                myS = Spectrum(wavelength=imlist[k].wavelength, spectrum=imlist[k][j, i],
    ##                               wavelength_units=getattr(imlist[k].header, 'wavelength_units', None))
    ##
    ##                ## Construct a variable name
    ##                vars()['S%d' % (k+1,)] = myS

                    # Recycle Spectrum object and replace spectrum for speedup...
                    globals()['S%d' % (k+1,)].spectrum = imlist[k][j, i]
                    
                try:
                    #S = S1 # first is also known as S... (this doesn't work...)
                    result = eval(expression)
                    if isinstance(result, Spectrum):
                        result = result.spectrum
                        # what about wavelength?
                    elif not isinstance(result, collections.abc.Iterable): # scalar
                        pass
                    else: # result is a tuple or a value
                        result = numpy.ndarray.flatten(result) # result is always a list
                    try:
                        imout[j, i] = result
                    except ValueError: # arrays don't match!
                        result = result[:bands]
                        lenresult = len(result)
                        imout[j, i, :lenresult] = result
                        imout[j, i, lenresult:] = nan
                except Exception as e:
                    message(repr(e))
                    return
            
    if progress: progress(1.0)          
    message('Completed!')

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='specmath.py',
        description='Spectral math')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                        help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                        help='use bad band list from the header')
    parser.add_argument('-o', dest='output', help='output image file name', required=True)
    parser.add_argument('-m', dest='maskfile', help='input mask file name (optional)', required=False)
    parser.add_argument('-t', dest='data_type', help='output data type (double, float32, int32, uint16, ...)')
    parser.add_argument('-e', dest='expression', help='Python expression', required=True)
    parser.add_argument('filenames', metavar='image', type=str, nargs='+',
                        help='input filenames')

    options = parser.parse_args()

    specmath(options.filenames, options.output, options.expression,
             maskfile=options.maskfile,
             data_type=options.data_type,
             sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
