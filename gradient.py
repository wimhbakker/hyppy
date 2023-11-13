#!/usr/bin/python3
## gradient.py
##
## Copyright (C) 2010 Wim Bakker
##
## Modified, WHB 20160310, added NaN-safe functions
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
import math

##BAND_NAMES = ['gradient x', 'gradient y', 'gradient (x+y)/2',
##              'gradient up', 'gradient down', 'gradient (up+down)/2',
##              'gradient (2x+2y+u+d)/6', 'edgy4', 'edgy8']

list_choices = ['X', 'Y', 'XY', 'U', 'D', 'UD', 'XYUD', 'E4', 'E8', 'SOBX', 'SOBY', 'SOBEL']

def message(s):
    pass

def gradient(nameIn, nameOut, mode='SAM', message=message, sort_wavelengths=False,
             use_bbl=True, choices=list(), nansafe=False, progress=None):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples

    do_X    = 'X' in choices
    do_Y    = 'Y' in choices
    do_XY   = 'XY' in choices
    do_U    = 'U' in choices
    do_D    = 'D' in choices
    do_UD   = 'UD' in choices
    do_XYUD = 'XYUD' in choices
    do_E4   = 'E4' in choices
    do_E8   = 'E8' in choices
    do_SOBX = 'SOBX' in choices
    do_SOBY = 'SOBY' in choices
    do_SOBEL = 'SOBEL' in choices

    band_names = []
    if do_X:
        band_names.append('X gradient')
    if do_Y:
        band_names.append('Y gradient')
    if do_XY:
        band_names.append('X+Y gradient')
    if do_U:
        band_names.append('Up diagonal')
    if do_D:
        band_names.append('Down diagonal')
    if do_UD:
        band_names.append('U+D diagonal')
    if do_XYUD:
        band_names.append('2X+2Y+U+D gradient')
    if do_E4:
        band_names.append('Edgy 4-neighbor')
    if do_E8:
        band_names.append('Edgy 8-neighbor')
    if do_SOBX:
        band_names.append('Sobel X')
    if do_SOBY:
        band_names.append('Sobel Y')
    if do_SOBEL:
        band_names.append('Sobel Filter')

    bands = len(band_names)

    # set up output ENVI image
    im2 = envi2.New(nameOut, 
                    hdr=im.header, bands=bands, data_type='d',
                    band_names=band_names, wavelength=None,
                    fwhm=None, bbl=None, default_bands=None)

    # set mode
    if mode == 'SAM' and nansafe:
        diff_func = im.nan_spectral_angle
    elif mode == 'ED' and nansafe:
        diff_func = im.nan_euclidean_distance
    elif mode == 'ID' and nansafe:
        diff_func = im.nan_intensity_difference
    elif mode == 'BC' and nansafe:
        diff_func = im.nan_bray_curtis_distance
    elif mode == 'SID' and nansafe:
        diff_func = im.nan_spectral_information_divergence
    elif mode == 'SAM':
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
        message("Oops! Missing distance function!")
        return

    # go for it!
    if progress:
        progress(0.0)
    for j in range(1, lines-1):
        if progress:
            progress(j / float(lines))
        for i in range(1, samples-1):
            band = 0
            # X and Y
            x = diff_func((i-1, j), (i+1, j))
            y = diff_func((i, j-1), (i, j+1))
            if do_X:
                im2[j, i, band] = x
                band = band + 1
            if do_Y:
                im2[j, i, band] = y
                band = band + 1
            if do_XY:
                im2[j, i, band] = (x+y) / 2
                band = band + 1

            # UP and DOWN diagonals
            u = diff_func((i+1, j-1), (i-1, j+1))
            d = diff_func((i-1, j-1), (i+1, j+1))
            if do_U:
                im2[j, i, band] = u
                band = band + 1
            if do_D:
                im2[j, i, band] = d
                band = band + 1
            if do_UD:
                im2[j, i, band] = (u+d) / 2
                band = band + 1

            # weighted total
            if do_XYUD:
                im2[j, i, band] = (2*x+2*y+u+d)/6
                band = band + 1

            # edgy4
            if do_E4:
                sam =   diff_func((i  , j-1), (i, j)) \
                      + diff_func((i-1, j  ), (i, j)) \
                      + diff_func((i+1, j  ), (i, j)) \
                      + diff_func((i  , j+1), (i, j))

                im2[j, i, band] = sam / 4
                band = band + 1

            # edgy8
            if do_E8:
                sam =       diff_func((i-1, j-1), (i, j)) \
                      + 2 * diff_func((i  , j-1), (i, j)) \
                      +     diff_func((i+1, j-1), (i, j)) \
                      + 2 * diff_func((i-1, j  ), (i, j)) \
                      + 2 * diff_func((i+1, j  ), (i, j)) \
                      +     diff_func((i-1, j+1), (i, j)) \
                      + 2 * diff_func((i  , j+1), (i, j)) \
                      +     diff_func((i+1, j+1), (i, j))

                im2[j, i, band] = sam / 12
                band = band + 1

            if do_SOBX or do_SOBY or do_SOBEL:
                x = (     diff_func((i-1, j-1), (i+1, j-1)) \
                    + 2 * diff_func((i-1, j  ), (i+1, j  )) \
                    +     diff_func((i-1, j+1), (i+1, j+1))) / 4
                    
                y = (     diff_func((i-1, j-1), (i-1, j+1)) \
                    + 2 * diff_func((i  , j-1), (i  , j+1)) \
                    +     diff_func((i+1, j-1), (i+1, j+1))) / 4

                sobel = math.hypot(x, y)

            if do_SOBX:
                im2[j, i, band] = x
                band = band + 1
                
            if do_SOBY:
                im2[j, i, band] = y
                band = band + 1

            if do_SOBEL:
                im2[j, i, band] = sobel
                band = band + 1

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im

if __name__ == '__main__':
##    print "Run this module using tkGradient!"

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='gradient.py',
##        usage='gradient.py -s -b -f -i input -o output -m {SAM|ED|ID|BC|SID} -a X Y XY U D UD XYUD E4 E8 SOBX SOBY SOBEL',
        description='Hyperspectral edge detection and gradient filters.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-n', action='store_true', dest='nansafe',
                      help='use nan-safe distance functions')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-a', action='store_true', dest='all',
                      help='select all gradient filters')
    parser.add_argument('-m', dest='mode', choices=('SAM', 'ED', 'ID', 'BC', 'SID'), default='SAM',
                      help='mode: SAM (spectral angle, default), ED (Euclidean distance), ID (intensity difference), BC (Bray-Curtis), SID (spectral information divergence)')
    parser.add_argument('gradient', nargs='*',
                      help='select gradient filters from {X Y XY U D UD XYUD E4 E8 SOBX SOBY SOBEL}')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        mode='SAM', all=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.all:
        gradient(options.input, options.output,
                 mode=options.mode,
                 choices=list_choices,
                 sort_wavelengths=options.sort_wavelengths,
                 use_bbl=options.use_bbl, nansafe=options.nansafe)
    else:
        gradient(options.input, options.output,
                 mode=options.mode,
                 choices=options.gradient,
                 sort_wavelengths=options.sort_wavelengths,
                 use_bbl=options.use_bbl, nansafe=options.nansafe)
