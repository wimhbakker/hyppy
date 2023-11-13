#!/usr/bin/python3
## edgy.py
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

def message(s):
    pass

def edgy(nameIn, nameOut, mode='SAM', sort_wavelengths=True, use_bbl=True,
         message=message, progress=None):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples

    # set up output ENVI image
    im2 = envi2.New(nameOut, 
                     hdr=envi2.Header(hdr=im.header, bands=1, data_type='d',
                                     band_names=None, wavelength=None,
                                     fwhm=None, bbl=None,
                                      default_bands=None))
    b = im2.data

    # set mode
    mode = mode.upper()
    if mode == 'SAM':
        diff_func = im.spectral_angle
    elif mode == 'ED':
        diff_func = im.euclidean_distance
    elif mode == 'ID':
        diff_func = im.intensity_difference
    elif mode == 'BC':
        diff_func = im.bray_curtis_distance
    elif mode == 'SID':
        diff_func = im.spectral_information_divergence
    else:
        message("Mode %s not implemented!" % (mode,))
        return

    # go for it!
    if progress:
        progress(0.0)

    for j in range(1, lines-1):
        if progress:
            progress(j / float(lines))

        for i in range(1, samples-1):
            sam =       diff_func((i-1, j-1), (i, j)) \
                  + 2 * diff_func((i  , j-1), (i, j)) \
                  +     diff_func((i+1, j-1), (i, j)) \
                  + 2 * diff_func((i-1, j  ), (i, j)) \
                  + 2 * diff_func((i+1, j  ), (i, j)) \
                  +     diff_func((i-1, j+1), (i, j)) \
                  + 2 * diff_func((i  , j+1), (i, j)) \
                  +     diff_func((i+1, j+1), (i, j))

            result = sam / 12

            b[j, i] = result

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im, b

if __name__ == '__main__':
##    print "Run this module using tkEdgy!"

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='edgy.py',
##        usage='edgy.py -s -b -f -i input -o output -m {SAM|ED|ID|BC|SID}',
        description='Hyperspectral edge filter')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-m', dest='mode', choices=('SAM', 'ED', 'ID', 'BC', 'SID'), default='SAM',
                      help='mode: SAM (spectral angle, default), ED (Euclidean distance), ID (intensity difference), BC (Bray-Curtis), SID (spectral information divergence)')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        mode='SAM')

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    edgy(options.input, options.output,
         mode=options.mode,
         sort_wavelengths=options.sort_wavelengths,
         use_bbl=options.use_bbl)
