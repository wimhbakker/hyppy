#!/usr/bin/python3
## sortchannels.py
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
import envi2
#from numpy import array

def message(s):
    pass

def sortchannels(nameIn, nameOut, use_bbl=True, message=message, progress=None):
    # get ENVI virtual image data
    im = envi2.Open(nameIn, sort_wavelengths=True, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples
    bands = im.bands

    if not hasattr(im.header, 'wavelength'):
        message('ABORT: No wavelengths found in header!')
        return

    # set up output ENVI image
    im2 = envi2.New(nameOut, hdr=im.header,
                    bands=bands, wavelength=im.wavelength, interleave='bsq')

#    b = im2.data

    # go for it!
    if progress:
        progress(0.0)
    for band in range(bands):
        if progress:
            progress(band / float(bands))
        im2[band] = im.get_band(band)

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im#, b

if __name__ == '__main__':
##    print "Run this module using tkSortChannels!"

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='sortchannels.py',
##        usage='sortchannels.py -b -f -i input -o output',
        description='Sort bands by wavelength.')

##    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
##                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

##    parser.set_defaults(use_bbl=False, force=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    sortchannels(options.input, options.output, use_bbl=options.use_bbl)
