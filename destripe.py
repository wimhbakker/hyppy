#!/usr/bin/python3
## destripe.py
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
from numpy import zeros, newaxis, polyfit, poly1d, where, isnan, nan

##from pylab import plot

def message(s):
    pass

def interpolate(a, order=2):
    bands = a.shape[1]
    result = a.copy()

    for band in range(bands):
        y = a[:, band]
        x = list(range(len(y)))
##        plot(x, y, 'b')
        t = polyfit(x, y, order)
        p = poly1d(t)
        ysmooth = p(x)
##        plot(x, ysmooth, 'r')
        result[:, band] = ysmooth

    return result

def destripe(fin, fout, direction='h', mode='d', order=None,
             sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    direction = direction.lower()
    mode = mode.lower()
    if direction.startswith('h') and mode.startswith('d'):
        destripe_horizontal_divide(fin, fout, order=order,
                                   sort_wavelengths=sort_wavelengths,
                            use_bbl=use_bbl, message=message, progress=progress)
    elif direction.startswith('v') and mode.startswith('d'):
        destripe_vertical_divide(fin, fout, order=order,
                                 sort_wavelengths=sort_wavelengths,
                          use_bbl=use_bbl, message=message, progress=progress)
    elif direction.startswith('h') and mode.startswith('s'):
        destripe_horizontal_subtract(fin, fout, order=order,
                                     sort_wavelengths=sort_wavelengths,
                            use_bbl=use_bbl, message=message, progress=progress)
    elif direction.startswith('v') and mode.startswith('s'):
        destripe_vertical_subtract(fin, fout, order=order,
                                   sort_wavelengths=sort_wavelengths,
                          use_bbl=use_bbl, message=message, progress=progress)
    else:
        raise ValueError("Unknown direction '%s'", direction)

def destripe_horizontal_subtract(fin, fout, order=None,
                                 sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)

    a = im[...]
    avrow = nanmean(a, axis=1)

    if progress:
        progress(0.2)

    if order:
        avrow = interpolate(avrow, order=order)
    
    if progress:
        progress(0.4)

    avband = nanmean(avrow, axis=0)

    if progress:
        progress(0.6)

    avrow = avrow - avband[newaxis, :]

    if progress:
        progress(0.8)

    im2[...] = im[...] - avrow[:, newaxis, :]

    if progress:
        progress(1.0)

    del im, im2

def destripe_horizontal_divide(fin, fout, order=None,
                               sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)

    a = im[...]
    avrow = nanmean(a, axis=1)

    if progress:
        progress(0.2)

    if order:
        avrow = interpolate(avrow, order=order)
    
    if progress:
        progress(0.4)

    avband = nanmean(avrow, axis=0)

    if progress:
        progress(0.6)

    avrow = avrow / avband[newaxis, :]

    if progress:
        progress(0.8)

    im2[...] = im[...] / avrow[:, newaxis, :]

    if progress:
        progress(1.0)

    del im, im2

def destripe_vertical_subtract(fin, fout, order=None,
                               sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)

    a = im[...]
    avcol = nanmean(a, axis=0)

    if progress:
        progress(0.2)

    if order:
        avcol = interpolate(avcol, order=order)
    
    if progress:
        progress(0.4)

    avband = nanmean(avcol, axis=0)

    if progress:
        progress(0.6)

    avcol = avcol - avband[newaxis, :]

    if progress:
        progress(0.8)

    im2[...] = im[...] - avcol[newaxis, :, :]

    if progress:
        progress(1.0)

    del im, im2

def destripe_vertical_divide(fin, fout, order=None,
                             sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)

    a = im[...]
    avcol = nanmean(a, axis=0)

    if progress:
        progress(0.2)

    if order:
        avcol = interpolate(avcol, order=order)
    
    if progress:
        progress(0.4)

    avband = nanmean(avcol, axis=0)

    if progress:
        progress(0.6)

    avcol = avcol / avband[newaxis, :]

    if progress:
        progress(0.8)

    im2[...] = im[...] / avcol[newaxis, :, :]

    if progress:
        progress(1.0)

    del im, im2

################# band-by-band versions ###################

def bbb_interpolate(a, order=2):
    (x,) = where(~isnan(a))

    if len(x)==0:
        return a
    
    y = a[x]

##    plot(x, y, 'b')
    
    t = polyfit(x, y, order)
    p = poly1d(t)

    x = list(range(len(a)))
    ysmooth = p(x)

##    plot(x, ysmooth, 'r')

    return ysmooth

def bbb_destripe(fin, fout, direction='h', mode='d', order=None,
             sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    direction = direction.lower()
    mode = mode.lower()
    if direction.startswith('h') and mode.startswith('d'):
        bbb_destripe_horizontal_divide(fin, fout, order=order,
                                   sort_wavelengths=sort_wavelengths,
                            use_bbl=use_bbl, message=message, progress=progress)
    elif direction.startswith('v') and mode.startswith('d'):
        bbb_destripe_vertical_divide(fin, fout, order=order,
                                 sort_wavelengths=sort_wavelengths,
                          use_bbl=use_bbl, message=message, progress=progress)
    elif direction.startswith('h') and mode.startswith('s'):
        bbb_destripe_horizontal_subtract(fin, fout, order=order,
                                     sort_wavelengths=sort_wavelengths,
                            use_bbl=use_bbl, message=message, progress=progress)
    elif direction.startswith('v') and mode.startswith('s'):
        bbb_destripe_vertical_subtract(fin, fout, order=order,
                                   sort_wavelengths=sort_wavelengths,
                          use_bbl=use_bbl, message=message, progress=progress)
    else:
        raise ValueError("Unknown direction '%s'", direction)

def bbb_destripe_horizontal_subtract(fin, fout, order=None,
                                 sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)
    for band in range(im.bands):
        if progress:
            progress(band / float(im.bands))
        a = im[band]
        avrow = nanmean(a, axis=1)

        if order:
            avrow = bbb_interpolate(avrow, order=order)
        
        avband = nanmean(avrow, axis=0)

        avrow = avrow - avband

        im2[band] = im[band] - avrow[:, newaxis]

    if progress:
        progress(1.0)
    
    del im, im2

def bbb_destripe_horizontal_divide(fin, fout, order=None,
                               sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)
    for band in range(im.bands):
        if progress:
            progress(band / float(im.bands))
        a = im[band]
        avrow = nanmean(a, axis=1)

        if order:
            avrow = bbb_interpolate(avrow, order=order)
        
        avband = nanmean(avrow, axis=0)

        avrow = avrow / avband

        im2[band] = im[band] / avrow[:, newaxis]

    if progress:
        progress(1.0)
    
    del im, im2

def bbb_destripe_vertical_subtract(fin, fout, order=None,
                               sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)
    for band in range(im.bands):
        if progress:
            progress(band / float(im.bands))
        a = im[band]
        avcol = nanmean(a, axis=0)

        if order:
            avcol = bbb_interpolate(avcol, order=order)
        
        avband = nanmean(avcol, axis=0)

        avcol = avcol - avband

        im2[band] = im[band] - avcol[newaxis, :]

    if progress:
        progress(1.0)
    
    del im, im2    

def bbb_destripe_vertical_divide(fin, fout, order=None,
                             sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d')

    if progress:
        progress(0.0)
    for band in range(im.bands):
        if progress:
            progress(band / float(im.bands))
        a = im[band]
        avcol = nanmean(a, axis=0)

        if order:
            avcol = bbb_interpolate(avcol, order=order)
        
        avband = nanmean(avcol, axis=0)

        avcol = avcol / avband

        im2[band] = im[band] / avcol[newaxis, :]

    if progress:
        progress(1.0)
    
    del im, im2



if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='destripe.py',
##        usage='destripe.py -s -b -f -i input -o output -d {hor, ver} -m {sub, div} -p {0, 1, 2, ...} -F',
        description='Destriping (p=0) and illumination correction (p>0) with order p')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-d', dest='direction', choices=('hor', 'ver'), default='hor',
                      help='direction: hor (horizontal, default) or ver (vertical)')
    parser.add_argument('-m', dest='mode', choices=('sub', 'div'), default='sub',
                      help='correction method: sub (subtract, default) or div (divide)')
    parser.add_argument('-p', dest='order', type=int, default=0,
                      help='polynomial order of correction: destriping (p=0, default) or illumination correction (p>0)') # p for Polynomial order

    parser.add_argument('-F', action='store_true', dest='fast',
                      help='fast version, keeps the entire image in memory!')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        direction='hor', mode='sub', order=0, fast=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.fast:
        destripe(options.input, options.output,
                  direction=options.direction,
                  mode=options.mode,
                  order=options.order,
                  sort_wavelengths=options.sort_wavelengths,
                  use_bbl=options.use_bbl)
    else:
        bbb_destripe(options.input, options.output,
                  direction=options.direction,
                  mode=options.mode,
                  order=options.order,
                  sort_wavelengths=options.sort_wavelengths,
                  use_bbl=options.use_bbl)
