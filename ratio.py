#!/usr/bin/python3
## ratio.py
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

def message(s):
    pass

def ratio(fin, fout, band1, band2, sort_wavelengths=False, use_bbl=True,
           message=message):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if hasattr(im, 'wavelength'):
        band1 = im.wavelength2index(band1)
        band2 = im.wavelength2index(band2)
        wav1 = im.index2wavelength(band1)
        wav2 = im.index2wavelength(band2)
        band_names=['Ratio of wavelengths: %f / %f' % (wav1, wav2)]
    else:
        band_names=['Ratio of bands: %d / %d' % (band1, band2)]

    im2 = envi2.New(fout,
                    hdr=im, interleave='bsq', bbl=None,
                    bands=1,
                    wavelength=None,
                    band_names=band_names,
                    data_type='d', fwhm=None)
    
    one = im.get_band(band1).astype('float64')
    two = im.get_band(band2).astype('float64')

    data = one / two

    im2[:,:,0] = data[:,:]

    del im, im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='ratio.py',
##        usage='ratio.py -s -b -f -i input -o output -w numerator -W denominator',
        description='Calculate Band Ratio.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-w', dest='wav1', type=float,
                      help='wavelength of numerator', required=True)
    parser.add_argument('-W', dest='wav2', type=float,
                      help='wavelength of denominator', required=True)

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

##    assert options.wav1, "Option -w wavelength of numerator required."
##    assert options.wav2, "Option -W wavelength of denominator required."

    ratio(options.input, options.output,
          options.wav1, options.wav2,
           sort_wavelengths=options.sort_wavelengths,
           use_bbl=options.use_bbl)
