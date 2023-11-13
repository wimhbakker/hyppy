#!/usr/bin/python3
## concolve.py
##
## Copyright (C) 2011 Wim Bakker
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

import numpy

# kernels are:  j, i, weight!
smoothing = ((0, 0, 1), (0, 1, 1), (0, 2, 1),
             (1, 0, 1), (1, 1, 1), (1, 2, 1),
             (2, 0, 1), (2, 1, 1), (2, 2, 1))

laplace   = ((0, 0,  0),  (0, 1, -1),  (0, 2,  0),
             (1, 0, -1),  (1, 1,  4),  (1, 2, -1),
             (2, 0,  0),  (2, 1, -1),  (2, 2,  0))

def str2kernel(s):
    try:
        result = []
        k = list(map(float, s.split()))
        for j in range(3):
            for i in range(3):
                result.append((j, i, k[3*j+i]))
        return result
    except:
        return None

def message(s):
    pass

def fast_convolve(nameIn, nameOut, kernel='laplace', bias=1.0,
                  offset=0.0, message=message,
                  sort_wavelengths=False, use_bbl=False, progress=None):
    """
Linear Filter

fast_convolve(nameIn, nameOut, kernel='laplace',
              bias=1.0, offset=0.0, message=message,
              sort_wavelengths=False, use_bbl=False)

Expects kernels in the form of a string, or a tuple of tuples:
'smoothing'
'laplace'
'0 -1 0 -1 4 -1 0 -1 0'
((0, 0,  0),  (0, 1, -1),  (0, 2,  0),
 (1, 0, -1),  (1, 1,  4),  (1, 2, -1),
 (2, 0,  0),  (2, 1, -1),  (2, 2,  0))
"""
    if type(kernel)==str:
        if kernel=='smoothing':
            kernel = smoothing
        elif kernel=='laplace':
            kernel = laplace
        else:
            kernel = str2kernel(kernel)
            if not kernel:
                raise ValueError('bad kernel')
        
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines   = im.lines
    samples = im.samples
    bands   = im.bands

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    # note: selecting BSQ here makes a big difference for speed!
    im2 = envi2.New(nameOut, hdr=im, interleave='bsq', bbl=bbl, data_type='d')

##    # copy edges of the original image
##    for i in range(samples):
##        im2[0, i, :]       = im[0, i, :]
##        im2[lines-1, i, :] = im[lines-1, i, :]
##
##    for j in range(lines):
##        im2[j, 0, :]         = im[j, 0, :]
##        im2[j, samples-1, :] = im[j, samples-1, :]

    # go for it!
    if progress:
        progress(0.0)
    for b in range(0, bands): # bands
        if progress:
            progress(b / float(bands))
        result = numpy.zeros((lines, samples))
        a      = numpy.zeros((lines, samples))
        for j, i, weight in kernel:
            if weight:
                a[1:-1, 1:-1] = im[j:(lines+j-2), i:(samples+i-2), b]
                result += weight * a

        im2[1:-1, 1:-1, b] = bias * result[1:-1, 1:-1] + offset

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im, a

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='convolve.py',
##        usage='convolve.py -f -i input -o output -k kernel --bias bias --offset offset',
        description="""Linear filter
\n
Expects kernels in the form of a string, or a tuple of tuples:
'smoothing' OR
'laplace' OR
'0 -1 0 -1 4 -1 0 -1 0' OR
((0, 0,  0),  (0, 1, -1),  (0, 2,  0),
 (1, 0, -1),  (1, 1,  4),  (1, 2, -1),
 (2, 0,  0),  (2, 1, -1),  (2, 2,  0))
"""
)

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-k', dest='kernel', help='kernel: smooth, laplace or 9 weights', default='laplace')
    parser.add_argument('--bias', dest='bias', type=float, default=1.0,
                      help='Constant for bias (default 1.0)')
    parser.add_argument('--offset', dest='offset', type=float, default=0.0,
                      help='Constant for offset (default 0.0)')

    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
                        kernel='laplace', bias=1.0, offset=0.0)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    fast_convolve(options.input, options.output,
                  kernel=options.kernel,
                  bias=options.bias, offset=options.offset,
                  sort_wavelengths=options.sort_wavelengths,
                  use_bbl=options.use_bbl)
