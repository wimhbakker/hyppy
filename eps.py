#!/usr/bin/python3
## eps.py
##
## Copyright (C) 2025 Wim Bakker
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

import numpy as np

filter0 = \
np.array([[0, 0, 0, 1, 0],
          [0, 0, 1, 0, 0],
          [0, 0, 1, 0, 0],
          [0, 0, 1, 0, 0],
          [0, 1, 0, 0, 0]])
ifilter0 = np.where(filter0)

filter1 = \
np.array([[0, 0, 0, 0, 0],
          [0, 0, 0, 1, 1],
          [0, 0, 1, 0, 0],
          [1, 1, 0, 0, 0],
          [0, 0, 0, 0, 0]])
ifilter1 = np.where(filter1)

filter2 = \
np.array([[0, 0, 0, 0, 0],
          [1, 0, 0, 0, 0],
          [0, 1, 1, 1, 0],
          [0, 0, 0, 0, 1],
          [0, 0, 0, 0, 0]])
ifilter2 = np.where(filter2)

filter3 = \
np.array([[0, 1, 0, 0, 0],
          [0, 1, 0, 0, 0],
          [0, 0, 1, 0, 0],
          [0, 0, 0, 1, 0],
          [0, 0, 0, 1, 0]])
ifilter3 = np.where(filter3)

filter4 = \
np.array([[0, 1, 0, 0, 0],
          [0, 0, 1, 0, 0],
          [0, 0, 1, 0, 0],
          [0, 0, 1, 0, 0],
          [0, 0, 0, 1, 0]])
ifilter4 = np.where(filter4)

filter5 = \
np.array([[0, 0, 0, 1, 0],
          [0, 0, 0, 1, 0],
          [0, 0, 1, 0, 0],
          [0, 1, 0, 0, 0],
          [0, 1, 0, 0, 0]])
ifilter5 = np.where(filter5)

filter6 = \
np.array([[0, 0, 0, 0, 0],
          [0, 0, 0, 0, 1],
          [0, 1, 1, 1, 0],
          [1, 0, 0, 0, 0],
          [0, 0, 0, 0, 0]])
ifilter6 = np.where(filter6)

filter7 = \
np.array([[0, 0, 0, 0, 0],
          [1, 1, 0, 0, 0],
          [0, 0, 1, 0, 0],
          [0, 0, 0, 1, 1],
          [0, 0, 0, 0, 0]])
ifilter7 = np.where(filter7)

filters = np.array([filter0, filter1, filter2, filter3, filter4, filter5, filter6, filter7])

ifilters = np.array([ifilter0, ifilter1, ifilter2, ifilter3, ifilter4, ifilter5, ifilter6, ifilter7])


def message(s):
    pass

def eps(nameIn, nameOut, message=message,
                  sort_wavelengths=False, use_bbl=False, progress=None):
    """Edge-Preserving Smoothing"""

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
    for b in range(bands): # bands
        for j in range(2, lines-2):
            if progress:
                progress(j / float(lines))
            for i in range(2, samples-2):
                the_mean = 0
                min_busy = np.inf
                for ifilter in ifilters:
                    values = im[j-2:j+3, i-2:i+3, b]
                    five = values[ifilter]
                    # mean
                    mean = five.mean()
                    # busyness
                    busy = np.sum(np.fabs(five[0:-1] - five[1:]))
                    if busy < min_busy:
                        the_mean = mean
                        min_busy = busy

                im2[j, i, b] = the_mean
        
    if progress:
        progress(1.0)

    # destroy resources
    del im2, im

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='eps.py',
##        usage='eps.py -f -i input -o output',
        description="""Edge-Preserving Smoothing"""
)

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    eps(options.input, options.output,
                  sort_wavelengths=options.sort_wavelengths,
                  use_bbl=options.use_bbl)
