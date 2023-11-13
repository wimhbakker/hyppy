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
##import scipy.stats

try:
    from numpy import nanmedian
except ImportError:
    from scipy.stats.stats import nanmedian

# kernels are BIP: j, i, band!
kernel7 = ((1, 1, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1), (1, 2, 1), (2, 1, 1), (1, 1, 2))

kernel19 = ((0, 1, 0), (1, 0, 0), (1, 1, 0), (1, 2, 0), (2, 1, 0),
            (0, 0, 1), (0, 1, 1), (0, 2, 1),
            (1, 0, 1), (1, 1, 1), (1, 2, 1),
            (2, 0, 1), (2, 1, 1), (2, 2, 1),
            (0, 1, 2), (1, 0, 2), (1, 1, 2), (1, 2, 2), (2, 1, 2))

kernel27 = ((0, 0, 0), (0, 1, 0), (0, 2, 0),
            (1, 0, 0), (1, 1, 0), (1, 2, 0),
            (2, 0, 0), (2, 1, 0), (2, 2, 0),
            (0, 0, 1), (0, 1, 1), (0, 2, 1),
            (1, 0, 1), (1, 1, 1), (1, 2, 1),
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
           sort_wavelengths=False, use_bbl=False, progress=None):
    if mode.lower()=='med27':
        median27(nameIn, nameOut, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    elif mode.lower()=='med7':
        median7(nameIn, nameOut, message=message,
                sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    elif mode.lower()=='fmed7':
        fast_median(nameIn, nameOut, kernel7, message=message,
                sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    elif mode.lower()=='fmed19':
        fast_median(nameIn, nameOut, kernel19, message=message,
                sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    elif mode.lower()=='fmed27':
        fast_median(nameIn, nameOut, kernel27, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    elif mode.lower()=='mean7':
        fast_mean(nameIn, nameOut, kernel7, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    elif mode.lower()=='mean19':
        fast_mean(nameIn, nameOut, kernel19, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    elif mode.lower()=='mean27':
        fast_mean(nameIn, nameOut, kernel27, message=message,
                 sort_wavelengths=sort_wavelengths, use_bbl=use_bbl, progress=progress)
    else:
        message("Mode %s not implemented!" % (mode,))

# 7 neighborhood median filter
def median7(nameIn, nameOut, message=message,
            sort_wavelengths=False, use_bbl=False, progress=None):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths,
                    use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples
    bands = im.bands

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    # set up output ENVI image
    im2 = envi2.New(nameOut, hdr=im, interleave='bip', bbl=bbl)

    # copy edges of the original image
    im2[0]       = im[0]
    im2[bands-1] = im[bands-1]
    
    for i in range(samples):
        im2[0, i, :]       = im[0, i, :]
        im2[lines-1, i, :] = im[lines-1, i, :]

    for j in range(lines):
        im2[j, 0, :]         = im[j, 0, :]
        im2[j, samples-1, :] = im[j, samples-1, :]

    # go for it!
    if progress:
        progress(0.0)

    for j in range(1, lines-1):         # lines
        if progress:
            progress(j / float(lines))
        for i in range(1, samples-1):   # samples
            for b in range(1, bands-1): # bands
                values = []
                append2(values, im[j-1, i  , b  ])
                append2(values, im[j+1, i  , b  ])
                append2(values, im[j  , i-1, b  ])
                append2(values, im[j  , i  , b  ])
                append2(values, im[j  , i+1, b  ])
                append2(values, im[j  , i  , b-1])
                append2(values, im[j  , i  , b+1])

                # median filtering: sort & pick middle value...
                if len(values):
                    im2[j, i, b] = sorted(values)[(len(values)-1)//2]
                else:
                    im2[j, i, b] = numpy.nan
                    
    if progress:
        progress(1.0)

    # destroy resources
    del im2, im

# 3x3x3 neighborhood median filter
def median27(nameIn, nameOut, message=message,
             sort_wavelengths=False, use_bbl=False, progress=None):
    # get ENVI image data
#    im = envi_image(nameIn, as_type='d')
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples
    bands = im.bands

    # set up output ENVI image
##    im2 = envi_image(nameOut, mode='w',
##                     hdr=envi_header(hdr=im.header, interleave='bip', datatype='d'))

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    im2 = envi2.New(nameOut,
                     hdr=im, interleave='bip', bbl=bbl)

    # copy edges of the original image
    im2[0]       = im[0]
    im2[bands-1] = im[bands-1]
    
    for i in range(samples):
        im2[0, i, :]       = im[0, i, :]
        im2[lines-1, i, :] = im[lines-1, i, :]

    for j in range(lines):
        im2[j, 0, :]         = im[j, 0, :]
        im2[j, samples-1, :] = im[j, samples-1, :]

    # go for it!
    if progress:
        progress(0.0)
    for j in range(1, lines-1): # lines
        if progress:
            progress(j / float(lines))
        for i in range(1, samples-1): # samples
            for b in range(1, bands-1): # bands
                values = im[j-1:j+2, i-1:i+2, b-1:b+2].flatten()

                # take out any nan's
                values = values[numpy.where(~numpy.isnan(values))]

                # median filtering: sort & pick middle value...
                if len(values):
                    values.sort()
                    result = values[(len(values)-1)//2]
                    im2[j, i, b] = result
                else:
                    im2[j, i, b] = numpy.nan

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im

### 3x3x3 neighborhood median filter
##def fast_median27(nameIn, nameOut, message=message,
##             sort_wavelengths=False, use_bbl=False):
##    # get ENVI image data
###    im = envi_image(nameIn, as_type='d')
##    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
##
##    lines = im.lines
##    samples = im.samples
##    bands = im.bands
##
##    bbl = None
##    if hasattr(im, 'bbl'):
##        bbl = im.bbl
##
##    im2 = envi2.New(nameOut,
##                     hdr=im, interleave='bsq', bbl=bbl)
##
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
##
##    a = numpy.zeros((lines, samples, 27))
##
##    # go for it!
##    for b in range(1, bands-1): # bands
##        message('.')
##        for j in range(3):
##            for i in range(3):
##                for bshift in range(3):
##                    a[1:-1, 1:-1, 9*j+3*i+bshift] = im[j:(lines+j-2), i:(samples+i-2), (b+bshift-1)]
##
##        # numpy version >= 1.40 puts nan's at the end!
##        a.sort(axis=2)
##
##        im2[1:-1, 1:-1, b] = a[1:-1, 1:-1, 13]
##
##    message('\n')
##
##    # destroy resources
##    del im2, im, a
##
##def fast_median7(nameIn, nameOut, message=message,
##             sort_wavelengths=False, use_bbl=False):
##    # get ENVI image data
###    im = envi_image(nameIn, as_type='d')
##    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
##
##    lines = im.lines
##    samples = im.samples
##    bands = im.bands
##
##    bbl = None
##    if hasattr(im, 'bbl'):
##        bbl = im.bbl
##
##    im2 = envi2.New(nameOut,
##                     hdr=im, interleave='bsq', bbl=bbl)
##
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
##
##    a = numpy.zeros((lines, samples, 7))
##
##    # go for it!
##    for b in range(1, bands-1): # bands
##        message('.')
##        counter = 0
##        for j, i, bshift in ((1, 1, 0), (0, 1, 1), (1, 0, 1), (1, 1, 1), (1, 2, 1), (2, 1, 1), (1, 1, 2)):
##            a[1:-1, 1:-1, counter] = im[j:(lines+j-2), i:(samples+i-2), (b+bshift-1)]
##            counter += 1
##
##        # numpy version >= 1.40 puts nan's at the end!
##        a.sort(axis=2)
##
##        im2[1:-1, 1:-1, b] = a[1:-1, 1:-1, 3]
##
##    message('\n')
##
##    # destroy resources
##    del im2, im, a
##
##def fast_median19(nameIn, nameOut, message=message,
##             sort_wavelengths=False, use_bbl=False):
##    # get ENVI image data
###    im = envi_image(nameIn, as_type='d')
##    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
##
##    lines = im.lines
##    samples = im.samples
##    bands = im.bands
##
##    bbl = None
##    if hasattr(im, 'bbl'):
##        bbl = im.bbl
##
##    im2 = envi2.New(nameOut,
##                     hdr=im, interleave='bsq', bbl=bbl)
##
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
##
##    a = numpy.zeros((lines, samples, 19))
##
##    # go for it!
##    for b in range(1, bands-1): # bands
##        message('.')
##        counter = 0
##        for j, i, bshift in ((0, 1, 0), (1, 0, 0), (1, 1, 0), (1, 2, 0), (2, 1, 0),
##                             (0, 0, 1), (0, 1, 1), (0, 2, 1),
##                             (1, 0, 1), (1, 1, 1), (1, 2, 1),
##                             (2, 0, 1), (2, 1, 1), (2, 2, 1),
##                             (0, 1, 2), (1, 0, 2), (1, 1, 2), (1, 2, 2), (2, 1, 2)):
##            a[1:-1, 1:-1, counter] = im[j:(lines+j-2), i:(samples+i-2), (b+bshift-1)]
##            counter += 1
##
##        # numpy version >= 1.40 puts nan's at the end!
##        a.sort(axis=2)
##
##        im2[1:-1, 1:-1, b] = a[1:-1, 1:-1, 9]
##
##    message('\n')
##
##    # destroy resources
##    del im2, im, a

def fast_median(nameIn, nameOut, kernel, message=message,
             sort_wavelengths=False, use_bbl=False, progress=None):
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples
    bands = im.bands

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    # note: selecting BSQ here makes a big difference for speed!
    im2 = envi2.New(nameOut, hdr=im, interleave='bsq', bbl=bbl)

    # copy edges of the original image
    im2[0]       = im[0]
    im2[bands-1] = im[bands-1]
    
    for i in range(samples):
        im2[0, i, :]       = im[0, i, :]
        im2[lines-1, i, :] = im[lines-1, i, :]

    for j in range(lines):
        im2[j, 0, :]         = im[j, 0, :]
        im2[j, samples-1, :] = im[j, samples-1, :]

    a = numpy.zeros((lines, samples, len(kernel)))

    # go for it!
    if progress:
        progress(0.0)
    for b in range(1, bands-1): # bands
        if progress:
            progress(b / float(bands))
        counter = 0
        for j, i, bshift in kernel:
            a[1:-1, 1:-1, counter] = im[j:(lines+j-2), i:(samples+i-2), (b+bshift-1)]
            counter += 1

        # note: numpy version >= 1.40 will put nan's at the end!
##        a.sort(axis=2)
##
##        im2[1:-1, 1:-1, b] = a[1:-1, 1:-1, (len(kernel)-1)/2]

        result = nanmedian(a, axis=2)

        im2[1:-1, 1:-1, b] = result[1:-1, 1:-1]

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im, a

def fast_mean(nameIn, nameOut, kernel, message=message,
             sort_wavelengths=False, use_bbl=False, progress=None):
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples
    bands = im.bands

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    # note: selecting BSQ here makes a big difference for speed!
    im2 = envi2.New(nameOut, hdr=im, interleave='bsq', bbl=bbl)

    # copy edges of the original image
    im2[0]       = im[0]
    im2[bands-1] = im[bands-1]
    
    for i in range(samples):
        im2[0, i, :]       = im[0, i, :]
        im2[lines-1, i, :] = im[lines-1, i, :]

    for j in range(lines):
        im2[j, 0, :]         = im[j, 0, :]
        im2[j, samples-1, :] = im[j, samples-1, :]

    a = numpy.zeros((lines, samples, len(kernel)))

    # go for it!
    if progress:
        progress(0.0)
    for b in range(1, bands-1): # bands
        if progress:
            progress(b / float(bands))
        counter = 0
        for j, i, bshift in kernel:
            a[1:-1, 1:-1, counter] = im[j:(lines+j-2), i:(samples+i-2), (b+bshift-1)]
            counter += 1

##        result = a.mean(axis=2)
##
##        im2[1:-1, 1:-1, b] = result[1:-1, 1:-1]

        result = numpy.nanmean(a, axis=2)

        im2[1:-1, 1:-1, b] = result[1:-1, 1:-1]

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im, a

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='median.py',
##        usage='median.py -f -i input -o output -m {med7, med27}',
        description='3D-median filter, 7, 19 and 27-neighborhood')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-m', dest='mode', choices=('med7', 'med27', 'fmed7', 'fmed27', 'fmed19',
                                                  'mean7', 'mean19', 'mean27'), default='med7',
                      help='mode: [f]med7 (7-neighborhood, default), [f]med{19|27} (19 or 27-neighborhood), or mean{7|19|27} (7, 19 or 27-neighborhood mean)')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        mode='med7')

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    median(options.input, options.output,
              mode=options.mode,
              sort_wavelengths=options.sort_wavelengths,
              use_bbl=options.use_bbl)
