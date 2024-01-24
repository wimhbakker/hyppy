#!/usr/bin/python3
##
##      destripe3d.py
##
##   Created: WHB 20160301
##  Modified: WHB 20180327, added 8-neighbor version...
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

import envi2
from envi2.constants import *

import numpy as np
np.seterr(all='ignore')

def message(s):
    pass

## 9-neighborhood version
def destriping_filter9(fin, fout, foffset=None,
               sort_wavelengths=False, use_bbl=True,
               maxmean=1000, maxstddev=500,
               replace_nan=False, apply_offset=True,
               message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave=ENVI_bsq, data_type='d')

    message("PASS 1: calculating offsets...")
    message("bad pixels: (x, band) mean stddev")

##    bias = np.ones((im.samples, im.bands))
    offset = np.zeros((im.samples, im.bands))
    deviat = np.zeros((im.samples, im.bands))
##    bad = offset.astype(np.bool8)
    
    # bands
    bad_pixels = list()

    if progress:
        progress(0.0)

    for band in range(1, im.bands-1):
        if progress:
            progress(band / float(im.bands))

        # samples
        for x in range(1, im.samples-1):
            
            # lines
            cube = im[:, x-1:x+2, band-1:band+2]
            xs = cube[:, 1, 1]
            ys = np.nanmean(cube, axis=(1,2))
            diff = ys - xs

            mean = np.nanmean(diff)
            stddev = np.sqrt(np.nanmean(np.square(diff)) - mean**2)
            offset[x, band] = mean
            deviat[x, band] = stddev

            if np.fabs(mean) > maxmean or stddev > maxstddev or not np.isfinite(mean) or not np.isfinite(stddev):
                offset[x, band] = np.nan
                deviat[x, band] = np.nan
                bad_pixels.append((x, band))
                message("(%d, %d) %f %f" % (x, band, mean, stddev))

    if progress:
        progress(1.0)
    
    message("PASS 2: recalculating offsets around bad pixels...")

    # recalculate offsets next to bad pixels...
    
    if progress:
        progress(0.0)

    count = 0
    for this_x, this_band in bad_pixels:
        if progress:
            progress(count / float(len(bad_pixels)))
        count += 1

        #bands
        for band in range(this_band-1, this_band+2):
            # samples
            for x in range(this_x-1, this_x+2):
                if not(band == this_band and x == this_x) and (0<band<im.bands-1 and 0<x<im.samples-1):
                    # lines
                    cube = im[:, x-1:x+2, band-1:band+2] + 0*offset[np.newaxis, x-1:x+2, band-1:band+2]
                    xs = cube[:, 1, 1]
                    ys = np.nanmean(cube, axis=(1,2))
                    diff = ys - xs

                    mean = np.nanmean(diff)
                    stddev = np.sqrt(np.nanmean(np.square(diff)) - mean**2)
                    offset[x, band] = mean
                    deviat[x, band] = stddev

    if progress:
        progress(1.0)
    
    message("Saving output image...")

    if apply_offset:
        message("Applying offset...")
        im2[...] = im[...] + offset[np.newaxis, :, :]
    else:
        message("Skipping offset, keeping NaN's... (new)")
 ##       im2[...] = im[...] + 0 * offset[np.newaxis, :, :]

        if progress:
            progress(0.0)

        nans = 0 * offset[:, :]
        for j in range(im.lines):
            if progress:
                progress(j / float(im.lines))

            im2[j, :, :] = im[j, :, :] + nans[:, :]

        if progress:
            progress(1.0)

    if foffset:
        message("Saving offset and stddev image...")
        im3 = envi2.New(foffset, file_type=ENVI_Standard,
                        lines=im.bands, samples=im.samples, bands=2,
                        band_names=['offset', 'stddev'],
                        byte_order=0,
                        interleave=ENVI_bsq, data_type='d')
        im3[0] = offset.transpose()
        im3[1] = deviat.transpose()
        del im3

    if replace_nan:
        message("PASS 3: replacing NaNs...")

        if progress:
            progress(0.0)

        count = 0
        for x, band in bad_pixels:
            if progress:
                progress(count / float(len(bad_pixels)))
            count += 1

            #bands
            for y in range(im.lines):
                cube = im2[y, x-1:x+2, band-1:band+2]
                im2[y, x, band] = np.nanmean(cube)

        if progress:
            progress(1.0)
        

    del im, im2


## 8-neighborhood version
def destriping_filter(fin, fout, foffset=None,
               sort_wavelengths=False, use_bbl=True,
               maxmean=1000, maxstddev=500,
               replace_nan=False, apply_offset=True,
               message=message, progress=None, smallkernel=False):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if im.header.data_type=='f' or im.lines*im.samples*im.bands*8 > 4000000000:
        im2 = envi2.New(fout, hdr=im, interleave=ENVI_bsq, data_type='f')
    else:
        im2 = envi2.New(fout, hdr=im, interleave=ENVI_bsq, data_type='d')

    message("PASS 1: calculating offsets...")
    message("bad pixels: (x, band) mean stddev")

##    bias = np.ones((im.samples, im.bands))
    offset = np.zeros((im.samples, im.bands))
    deviat = np.zeros((im.samples, im.bands))
##    bad = offset.astype(np.bool8)
    
    # bands
    bad_pixels = list()

    if progress:
        progress(0.0)

    for band in range(1, im.bands-1):
        if progress:
            progress(band / float(im.bands))

        # samples
        for x in range(1, im.samples-1):
            
            # lines
            cube = im[:, x-1:x+2, band-1:band+2].astype('d').copy()
            xs = cube[:, 1, 1].copy()
            cube[:, 1, 1] = np.nan  # set middle pixels to nan
            if smallkernel:         # set corner pixels to nan as well
                cube[:, 0, 0] = np.nan
                cube[:, 0, 2] = np.nan
                cube[:, 2, 0] = np.nan
                cube[:, 2, 2] = np.nan
            ys = np.nanmean(cube, axis=(1,2))
            diff = ys - xs

            mean = np.nanmean(diff)
            stddev = np.sqrt(np.nanmean(np.square(diff)) - mean**2)
            offset[x, band] = mean
            deviat[x, band] = stddev

            if np.fabs(mean) > maxmean or stddev > maxstddev or not np.isfinite(mean) or not np.isfinite(stddev):
                offset[x, band] = np.nan
                deviat[x, band] = np.nan
                bad_pixels.append((x, band))
                message("(%d, %d) %f %f" % (x, band, mean, stddev))

    if progress:
        progress(1.0)
    
    message("PASS 2: recalculating offsets around bad pixels...")

    # recalculate offsets next to bad pixels...
    
    if progress:
        progress(0.0)

    count = 0
    for this_x, this_band in bad_pixels:
        if progress:
            progress(count / float(len(bad_pixels)))
        count += 1

        #bands
        for band in range(this_band-1, this_band+2):
            # samples
            for x in range(this_x-1, this_x+2):
                if not(band == this_band and x == this_x) and (0<band<im.bands-1 and 0<x<im.samples-1):
                    # lines
                    cube = im[:, x-1:x+2, band-1:band+2] + 0*offset[np.newaxis, x-1:x+2, band-1:band+2]
                    xs = cube[:, 1, 1].copy()
                    cube[:, 1, 1] = np.nan
                    ys = np.nanmean(cube, axis=(1,2))
                    diff = ys - xs

                    mean = np.nanmean(diff)
                    stddev = np.sqrt(np.nanmean(np.square(diff)) - mean**2)
                    offset[x, band] = mean
                    deviat[x, band] = stddev

    if progress:
        progress(1.0)
    
    message("Saving output image...")

    if apply_offset:
        message("Applying offset...")
        im2[...] = im[...] + offset[np.newaxis, :, :]
    else:
        message("Skipping offset, keeping NaN's... (new)")
 ##       im2[...] = im[...] + 0 * offset[np.newaxis, :, :]

        if progress:
            progress(0.0)

        nans = 0 * offset[:, :]
        for j in range(im.lines):
            if progress:
                progress(j / float(im.lines))

            # the slice is there for avoiding having two advanced indices with a slice in the middle!
            # j, slice, bands (bands are always advanced indices!).
            # because then the axes get swapped... (bands, samples)
            # Now it's [slice, slice, advanced], resulting in dimensions (1, samples, bands)
            im2[j, :, :] = im[j:j+1, :, :] + nans[:, :]

        if progress:
            progress(1.0)

    if foffset:
        message("Saving offset and stddev image...")
        im3 = envi2.New(foffset, file_type=ENVI_Standard,
                        lines=im.bands, samples=im.samples, bands=2,
                        band_names=['offset', 'stddev'],
                        byte_order=0,
                        interleave=ENVI_bsq, data_type='d')
        im3[0] = offset.transpose()
        im3[1] = deviat.transpose()
        del im3

    if replace_nan:
        message("PASS 3: replacing NaNs...")

        if progress:
            progress(0.0)

        count = 0
        for x, band in bad_pixels:
            if progress:
                progress(count / float(len(bad_pixels)))
            count += 1

            #bands
            for y in range(im.lines):
                cube = im2[y, x-1:x+2, band-1:band+2]
                im2[y, x, band] = np.nanmean(cube)

        if progress:
            progress(1.0)
        

    del im, im2


if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='destripefilt.py',
##        usage='destripefilt.py -s -b -f -i input -o output -m maxmean -d maxstddev -r',
        description='Destriping using spatio-spectral filtering')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-r', action='store_true', dest='replace_nan',
                      help='replace NaNs')
    parser.add_argument('-a', action='store_true', dest='apply_offset',
                      help='apply offset')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-4', action='store_true', dest='small_kernel',
                      help='use 1+2+1 kernel in case of odd-even effects')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)
    parser.add_argument('-c', dest='offset', help='offset file name')

    parser.add_argument('-m', dest='maxmean', type=float, default=500.0,
                      help='maximum mean, larger values will be set to NaN')
    parser.add_argument('-d', dest='maxstddev', type=float, default=500.0,
                      help='maximum stddev, larger values will be set to NaN')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        maxmean=1000.0, maxstddev=500.0, replace_nan=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    destriping_filter(options.input, options.output,
                       foffset=options.offset,
                       sort_wavelengths=options.sort_wavelengths,
                       use_bbl=options.use_bbl,
                       maxmean=options.maxmean,
                       maxstddev=options.maxstddev,
                       replace_nan=options.replace_nan,
                       apply_offset=options.apply_offset,
                       smallkernel=options.small_kernel)
