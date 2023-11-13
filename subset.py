#!/usr/bin/python3
## subset.py
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
from envi2.constants import *

def message(s):
    pass

def subset(nameIn, nameOut,
           output_format=ENVI_bsq,
           top=0, bottom=0,
           left=0, right=0,
           band_selection=None,
           message=message, sort_wavelengths=True,
           use_bbl=True, data_type='keep'):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    # safety checks
    if top > bottom:
        top, bottom = bottom, top

    if left > right:
        left, right = right, left

    top    = max(0, top)
    bottom = min(im.lines, bottom)
    left   = max(0, left)
    right  = min(im.samples, right)

    # set up metadata for output image
    lines = bottom - top
    samples = right - left

    bands = im.bands
    band_names = getattr(im, "band_names", None)
    wavelength = getattr(im, "wavelength", None)
    bbl = getattr(im, "bbl", None)
    
    if band_selection:
        bands = len(band_selection)
        if band_names is not None:
            band_names = [band_names[i] for i in band_selection]
        if wavelength is not None:
            wavelength = [wavelength[i] for i in band_selection]
        if bbl is not None:
            bbl = [bbl[i] for i in band_selection]

    # set up subset image, output ENVI image
    if data_type == 'keep':
        im2 = envi2.New(nameOut,
                    hdr=im,
                    lines=lines,
                    samples=samples,
                    bands=bands,
                    band_names=band_names,
                    wavelength=wavelength,
                    fwhm=None, bbl=bbl,
                    interleave=output_format)
    else:
        im2 = envi2.New(nameOut,
                    hdr=im,
                    lines=lines,
                    samples=samples,
                    bands=bands,
                    band_names=band_names,
                    wavelength=wavelength,
                    fwhm=None, bbl=bbl,
                    interleave=output_format, data_type=data_type)

    # Here we go!
    if band_selection:
##        if bands == 1:
##            im2[...] = im[top:bottom, left:right, band_selection].squeeze()
##        else:
##            im2[...] = im[top:bottom, left:right, band_selection]
        im2[...] = im[top:bottom, left:right, band_selection]
    else:
        im2[...] = im[top:bottom, left:right, :]

    # destroy resources
    del im2, im

def parse(s, min_, max_):
    """For parsing band lists:
10, add band 10
>10, add band 10 and all above
<10, add band 10 and all below
10-20, add bands 10 and 20 and all between.
"""
    result = []
    for term in s.split():
        if term[0] == '>':
            result.extend(list(range(int(term[1:]), max_)))
        elif term[0] == '<':
            result.extend(list(range(min_, int(term[1:])+1)))
        elif term.find('-') >= 0:
            i = term.find('-', 1)
            result.extend(list(range(max(min_, int(term[:i])), min(max_, int(term[i+1:])+1))))
        else:
            result.extend(list(range(max(min_, int(term)), min(max_, int(term)+1))))
    result = sorted(list(set(result)))
    return result

if __name__ == '__main__':
##    print "Run this module using tkSubset!"

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='subset.py',
##        usage='subset.py -s -b -f -i input -o output -x x0 -X x1 -y y0 -Y y1 -B bandlist -m {bip|bil|bsq}',
        description='Make subset')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)
    parser.add_argument('-x', dest='x0', type=int, default=0, help='first sample')
    parser.add_argument('-X', dest='x1', type=int, default=1000000, help='last sample')
    parser.add_argument('-y', dest='y0', type=int, default=0, help='first line')
    parser.add_argument('-Y', dest='y1', type=int, default=1000000, help='last line')
    parser.add_argument('-B', dest='bandlist',
                      help='band list (string!), e.g. "<2 4 6-8 >10" for 0 1 2 4 6 7 8 10 11 12...')
    parser.add_argument('-m', dest='mode', choices=('bip', 'bil', 'bsq'), default='bsq',
                      help='format of output file: bip, bil or bsq (default)')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        x0=0, x1=1000000, y0=0, y1=1000000,
##                        mode='bsq')

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
##    assert options.x0 is not None, "Option -x first column required."
##    assert options.x1 is not None, "Option -X last column required."
##    assert options.y0 is not None, "Option -y first row required."
##    assert options.y1 is not None, "Option -Y last row required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.bandlist:
        im = envi2.Open(options.input,
                        sort_wavelengths=options.sort_wavelengths,
                        use_bbl=options.use_bbl)

        max_ = im.bands
        del im

        band_selection = parse(options.bandlist, 0, max_)
    else:
        band_selection = None

    subset(options.input, options.output, output_format=options.mode,
           top=options.y0, bottom=options.y1,
           left=options.x0, right=options.x1,
           band_selection=band_selection,
           sort_wavelengths=options.sort_wavelengths,
           use_bbl=options.use_bbl)
