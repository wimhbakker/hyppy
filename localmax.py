#!/usr/bin/python3
## median.py
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

import numpy

# kernels are BIP: j, i, band!
kernel7 = (
                       (1, 1, 0),
#
                       (0, 1, 1),
            (1, 0, 1),            (1, 2, 1),
                       (2, 1, 1),
#
                       (1, 1, 2))

kernel19 = (           (0, 1, 0),
            (1, 0, 0), (1, 1, 0), (1, 2, 0),
                       (2, 1, 0),
            (0, 0, 1), (0, 1, 1), (0, 2, 1),
            (1, 0, 1),            (1, 2, 1),
            (2, 0, 1), (2, 1, 1), (2, 2, 1),
                       (0, 1, 2),
            (1, 0, 2), (1, 1, 2), (1, 2, 2),
                       (2, 1, 2))

kernel27 = ((0, 0, 0), (0, 1, 0), (0, 2, 0),
            (1, 0, 0), (1, 1, 0), (1, 2, 0),
            (2, 0, 0), (2, 1, 0), (2, 2, 0),
            (0, 0, 1), (0, 1, 1), (0, 2, 1),
            (1, 0, 1),            (1, 2, 1),
            (2, 0, 1), (2, 1, 1), (2, 2, 1),
            (0, 0, 2), (0, 1, 2), (0, 2, 2),
            (1, 0, 2), (1, 1, 2), (1, 2, 2),
            (2, 0, 2), (2, 1, 2), (2, 2, 2))

def message(s):
    pass

def append2(l, val):
    if not numpy.isnan(val):
        l.append(val)

def median(nameIn, nameOut, mode='med27', message=message,
           sort_wavelengths=False, use_bbl=False):
    if mode.lower()=='med27':
        median27(nameIn, nameOut, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    elif mode.lower()=='med7':
        median7(nameIn, nameOut, message=message,
                sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    elif mode.lower()=='fmed7':
        fast_median(nameIn, nameOut, kernel7, message=message,
                sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    elif mode.lower()=='fmed19':
        fast_median(nameIn, nameOut, kernel19, message=message,
                sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    elif mode.lower()=='fmed27':
        fast_median(nameIn, nameOut, kernel27, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    elif mode.lower()=='mean7':
        fast_mean(nameIn, nameOut, kernel7, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    elif mode.lower()=='mean19':
        fast_mean(nameIn, nameOut, kernel19, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    elif mode.lower()=='mean27':
        fast_mean(nameIn, nameOut, kernel27, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    else:
        message("Mode %s not implemented!" % (mode,))


def fast_localmax(nameIn, nameOut, kernel, message=message,
             sort_wavelengths=False, use_bbl=False):
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples
    bands = im.bands

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    # note: selecting BSQ here makes a big difference for speed!
    im2 = envi2.New(nameOut, hdr=im, interleave='bsq', bbl=bbl)

##    # copy edges of the original image
##    im2[0]       = im[0]
##    im2[bands-1] = im[bands-1]
##    
##    for i in range(samples):
##        im2[0, i, :]       = im[0, i, :]
##        im2[lines-1, i, :] = im[lines-1, i, :]
##
##    for j in range(lines):
##        im2[j, 0, :]         = im[j, 0, :]
##        im2[j, samples-1, :] = im[j, samples-1, :]

    a = numpy.zeros((lines, samples, len(kernel)))

    # go for it!
    for b in range(0, bands-0): # bands
        message('.')
        counter = 0
        for j, i, bshift in kernel:
            if 0<=(b+bshift-1)<bands:
                a[1:-1, 1:-1, counter] = im[j:(lines+j-2), i:(samples+i-2), (b+bshift-1)]
                counter += 1

        result = a.max(axis=2)

        radius = int(im.band_names[b].split()[1])
        tmp = im[1:-1, 1:-1, b]
        im2[1:-1, 1:-1, b] = ((tmp > result[1:-1, 1:-1]) & (tmp > radius)) * radius

    message('\n')

    # destroy resources
    del im2, im, a

if __name__ == '__main__':
    # command line version
    import optparse
    import os

    parser = optparse.OptionParser(
        usage='median.py -f -i input -o output -m {med7, med27}',
        description='3D-median filter, 7, 19 and 27-neighborhood')

    parser.add_option('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_option('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_option('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_option('-i', dest='input', help='input file name')
    parser.add_option('-o', dest='output', help='output file name')

    parser.add_option('-m', dest='mode', choices=('med7', 'med27', 'fmed7', 'fmed27', 'fmed19',
                                                  'mean7', 'mean19', 'mean27'),
                      help='mode: [f]med7 (7-neighborhood, default), [f]med{19|27} (19 or 27-neighborhood), or mean{7|19|27} (7, 19 or 27-neighborhood mean)')

    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
                        mode='med7')

    (options, args) = parser.parse_args()

    assert options.input, "Option -i input file name required."
    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    median(options.input, options.output,
              mode=options.mode,
              sort_wavelengths=options.sort_wavelengths,
              use_bbl=options.use_bbl)
