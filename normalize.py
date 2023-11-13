#!/usr/bin/python3
## normalize.py
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

import envi2
##from scipy.stats.stats import nanmean, nanstd
from numpy import nanmean, nanstd

def message(s):
    pass

def normalize(fin, fout, add_stdev=0.0, sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)
    for i in range(im.bands):
        if progress:
            progress(i / float(im.bands))
        
        one = im[i]
        onef = one.flatten()
        m = nanmean(onef)
        s = nanstd(onef)

        data = (one - m) / s + add_stdev

        im2[i] = data[:,:]

    if progress:
        progress(1.0)

    del im, im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='normalize.py',
##        usage='normalize.py -s -b -f -i input -o output -a stddevs',
        description='Normalize bands.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-a', dest='add_stdev', type=float, default=0.0,
                      help='add standard deviations (default=0.0)')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        add_stdev=0.0)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    normalize(options.input, options.output,
              add_stdev=options.add_stdev,
              sort_wavelengths=options.sort_wavelengths,
              use_bbl=options.use_bbl)
