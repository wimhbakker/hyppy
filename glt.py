#!/usr/bin/python3
## glt.py
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

import os
import envi2
from envi2.constants import *

import numpy
import sys

def message(s):
    print(s)

def backward(fin, fglt, fout, sort_wavelengths=False, use_bbl=False, message=message,
             progress=None):
    try:
        im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
        glt = envi2.Open(fglt)
    except ValueError as errtext:
        message("Error: %s\n" % (errtext,))
        return
    
    samples = glt[0].max()
    lines = glt[1].max()

    # Create new image
    try:
        im2 = envi2.New(fout, value=numpy.nan, hdr=im, samples=samples, lines=lines)
    except Exception as errtext:
        message("Error: %s" % (errtext,))
        return

    if progress:
        progress(0.0)

    for j in range(glt.lines):
        if progress:
            progress(j / float(glt.lines))
        for i in range(glt.samples):
            ii = (glt[j, i, 0])
            jj = (glt[j, i, 1])
            if ii>0 and jj>0:
                im2[jj-1, ii-1] = im[j, i]

    if progress:
        progress(1.0)

    del im2
    del glt
    del im

def forward(fin, fglt, fout, sort_wavelengths=False, use_bbl=False, message=message,
            progress=None):
    try:
        im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
        glt = envi2.Open(fglt)
    except ValueError as errtext:
        message("Error: %s\n" % (errtext,))
        return
    
    samples = glt[0].max()
    lines = glt[1].max()

    # Create new image
    try:
        if hasattr(glt.header, 'map_info'):
            im2 = envi2.New(fout, value=numpy.nan, hdr=im, samples=glt.samples, lines=glt.lines, map_info=glt.header.map_info)
        else:
            im2 = envi2.New(fout, value=numpy.nan, hdr=im, samples=glt.samples, lines=glt.lines)
    except Exception as errtext:
        message("Error: %s" % (errtext,))
        return

    if progress:
        progress(0.0)

    for j in range(glt.lines):
        if progress:
            progress(j / float(glt.lines))
        for i in range(glt.samples):
            ii = abs(glt[j, i, 0])
            jj = abs(glt[j, i, 1])
            if ii>0 and jj>0:
                im2[j, i] = im[jj-1, ii-1]

    if progress:
        progress(1.0)

    del im2
    del glt
    del im

if __name__ == '__main__':
##    GUI is called tkGLT

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='glt.py',
        description='Forward or backward GLT transform.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input image file name', required=True)
    parser.add_argument('-g', dest='glt', help='input GLT file name', required=True)
    parser.add_argument('-o', dest='output', help='output image file name', required=True)
    parser.add_argument('-m', dest='mode', help='mode forward (default) or backward',
                        choices=('forward', 'backward'), default='forward')

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use -f to overwrite.")

    if options.mode=='forward':
        forward(options.input, options.glt, options.output, sort_wavelengths=options.sort_wavelengths,
                 use_bbl=options.use_bbl)
    else:
        backward(options.input, options.glt, options.output, sort_wavelengths=options.sort_wavelengths,
                 use_bbl=options.use_bbl)
