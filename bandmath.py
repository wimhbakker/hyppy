#!/usr/bin/python3
## bandmath.py
##
## Copyright (C) 2018 Wim Bakker
##      Created: WHB 20180925, CLI of the BandMath GUI...
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

from numpy import *
##from scipy.interpolate import interp1d
##from scipy.optimize import fmin, minimize
##import sys
##
##import time
from scipy.stats import *

from entropy import hist_entropy

def message(s):
    print(s)

def bandmath(fin, fout, expression, data_type=None, sort_wavelengths=False, use_bbl=False, message=message,
            progress=None):
    message("Input file(s): %s" % str(fin))
    message("Output file: %s" % fout)

    fnames = fin
    biglist = []
    hdr = None
    i = 1
    for fname in fnames:
        im = envi2.Open(fname,
                        sort_wavelengths=sort_wavelengths,
                        use_bbl=use_bbl)

        if hdr is None:      # copy header info from first image...
            hdr = im.header.copy()
            if data_type is None:
                data_type = hdr.data_type
            
        # This is awkward!
        if i==1:
            i1 = im
        elif i==2:
            i2 = im
        elif i==3:
            i3 = im
        elif i==4:
            i4 = im
        elif i==5:
            i5 = im
        elif i==6:
            i6 = im
        elif i==7:
            i7 = im
        elif i==8:
            i8 = im
        elif i==9:
            i9 = im
        elif i==10:
            i10 = im
        elif i==11:
            i11 = im
        elif i==12:
            i12 = im
        elif i==13:
            i13 = im
        elif i==14:
            i14 = im
        elif i==15:
            i15 = im
        elif i==16:
            i16 = im
        elif i==17:
            i17 = im
        elif i==18:
            i18 = im
        elif i==19:
            i19 = im
        elif i==20:
            i20 = im
        else:
            raise ValueError('Maximum inputs exceeded')

        i = i + 1

    message('Evaluating: %s' % (expression,))
    try:
        result = eval(expression)
    except Exception as e:
        message(repr(e))
    
    if result.ndim==2: # 2 dimensional
        imout = envi2.New(fout,
                          hdr=hdr, data_type=data_type,
                          bands=1,
                          wavelength=None,
                          bbl=None,
                          band_names=None,
                          fwhm=None,
                          interleave='bsq',
                          description=['tkBandMath: %s' % (expression,)])
        imout[0] = eval(expression)
        del imout
    elif result.ndim==1: # 1 dimensional = array / list
        message('Output is list')
        f = open(fout, 'w')
        for item in result:
            print(item, file=f)
        f.close()
    elif result.ndim==0: # 0 dimensional = scalar
        message('Output is scalar')
        f = open(fout, 'w')
        print(result, file=f)
        f.close()
    else:
        print(result.shape)
        raise ValueError('Unsupported output type %s', type(result))

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='bandmath.py',
        description='Band math')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                        help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                        help='use bad band list from the header')
    parser.add_argument('-o', dest='output', help='output image file name', required=True)
    parser.add_argument('-t', dest='data_type', help='output data type (double, float32, int32, uint16, ...)')
    parser.add_argument('-e', dest='expression', help='Python expression', required=True)
    parser.add_argument('filenames', metavar='image', type=str, nargs='+',
                        help='input filenames')

    options = parser.parse_args()

    bandmath(options.filenames, options.output, options.expression,
             data_type=options.data_type,
             sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
