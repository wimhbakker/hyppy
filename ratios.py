#!/usr/bin/python3
## ratios.py
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

##delta = 1

def message(s):
    pass

def ratios(fin, fout, delta=1, sort_wavelengths=False, use_bbl=True,
           message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if hasattr(im, 'wavelength'):
        wavelength = im.wavelength[:-delta]
    else:
        wavelength = None

    im2 = envi2.New(fout,
                          hdr=im, interleave='bsq', bbl=None,
                          bands=im.bands-delta,
                          wavelength=wavelength,
                          data_type='d', band_names=None, fwhm=None)

    if progress:
        progress(0.0)
    for i in range(im.bands-delta):
        if progress:
            progress(i / float(im.bands-delta))
        one = im.get_band(i).astype('float64')
        two = im.get_band(i+delta).astype('float64')

        data = one / two

        im2[:,:,i] = data[:,:]

    if progress:
        progress(1.0)

    del im, im2

if __name__ == '__main__':
##    fin = direct + '\\' + fin
##    fout = fin + '_rat' + str(delta)
##    ratios(fin, fout, delta=delta)

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='ratios.py',
##        usage='ratios.py -s -b -f -i input -o output -d delta',
        description='Calculate Band Ratios.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-d', dest='delta', type=int, default=1,
                      help='delta, shift between bands (default=1)')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        delta=1)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    ratios(options.input, options.output,
           delta=options.delta,
           sort_wavelengths=options.sort_wavelengths,
           use_bbl=options.use_bbl)
