#!/usr/bin/python3
## statistics.py
##
## Copyright (C) 2018 Wim Bakker
##  Modified: 201804.. WHB major revision
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
#import spectrum

import numpy

def get_histogram(b, numbins=256):
    bf = b.flatten()
    # take out nan's
    bf = bf[numpy.where(~numpy.isnan(bf))]
    min_ = numpy.nanmin(bf)
    max_ = numpy.nanmax(bf)
    if numbins < 1:
        bins = arange(min_, max_, 1)
    else:
        bins = numpy.arange(min_, max_, (max_ - min_) / float(numbins))
##        hist = histogram2(bf, bins)
    hist, bins = numpy.histogram(bf, bins)
    return bins[:-1], hist

def print_histogram(im, b, numbins=256):
    s = im[b]
    bins, hist = get_histogram(s, numbins=numbins)
    hist = hist/float(hist.sum())
    print('# histogram band %d' % (b,))
    for x, y in zip(bins, hist):
        print(x, y)

def print_band_statistics(im, b):
    band = im[b].flatten()
    # skip the NaN's
    band = band[numpy.where(~numpy.isnan(band))]
    if len(band) == 0: # all NaN's
        pass
    else:
        band.sort()
        mean = band.mean()
        sdev = band.std()
        min_ = band[0]
        max_ = band[len(band)-1]
        perc01  = float(band[int(0.01*len(band))]) # why float???
        perc02 = float(band[int(0.02*len(band))])
        perc50 = float(band[int(0.50*len(band))])
        perc98 = float(band[int(0.98*len(band))])
        perc99 = float(band[int(0.99*len(band))])
        median_ = numpy.median(band)
        mad = numpy.median(numpy.fabs(band - median_))

        print('min  %f'%(min_,))
        print('max  %f'%(max_,))
        print('mean %f'%(mean,))
        print('sdev %f\n'%(sdev,))

        print('m-3s %f'%(mean-3*sdev,))
        print('m-2s %f'%(mean-2*sdev,))
        print('m-1s %f'%(mean-1*sdev,))
        print('m    %f'%(mean,))
        print('m+1s %f'%(mean+1*sdev,))
        print('m+2s %f'%(mean+2*sdev,))
        print('m+3s %f\n'%(mean+3*sdev,))
        
        print(' 1%%  %f'%(perc01,))
        print(' 2%%  %f'%(perc02,))
        print('50%%  %f'%(perc50,))
        print('98%%  %f'%(perc98,))
        print('99%%  %f\n'%(perc99,))

        print('median    %f'%(median_,))
        print('MAD       %f'%(mad,))
        print('med-2mad  %f'%(median_-2*mad,))
        print('med+2mad  %f\n'%(median_+2*mad,))

def statistics(nameIn,
                  sort_wavelengths=False,
                  use_bbl=False,
               histogram=False,
               stats=False,
               numbins=256,
               band=None,
               wavelength=None,
               bandname=None):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    bands = im.bands

    if bandname:
        band = im.band_names.index(bandname)
        print("#### BANDNAME %s ####" % (bandname,))

    if wavelength:
        band = im.wavelength2index(wavelength)
        print("#### WAVELENGTH %f ####" % (im.index2wavelength(band),))

    # go for it!
    if band is not None:
        if histogram:
            print_histogram(im, band, numbins=numbins)
        if stats:
            print_band_statistics(im, band)
    else:
        for b in range(bands):
            print("#### BAND %d ####" % (b,))
            if histogram:
                print_histogram(im, b, numbins=numbins)
            if stats:
                print_band_statistics(im, b)

    # destroy resources
    del im

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='statistics.py',
        description='Calculate statistics')

    parser.add_argument('-b', action='store_true', dest='use_bbl', help='use bad band list')
    parser.add_argument('-s', action='store_true', dest='sort_wavelengths', help='sort wavelengths')
    parser.add_argument('-hist', action='store_true', dest='histogram', help='calculate histogram')
    parser.add_argument('-stats', action='store_true', dest='stats', help='calculate statistics')
    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-band', dest='band', type=int, required=False, help='select band')
    parser.add_argument('-w', dest='wavelength', type=float, required=False, help='select band by wavelength')
    parser.add_argument('-bandname', dest='bandname', type=str, required=False, help='select band by bandname')
    parser.add_argument('-n', dest='numbins', type=int, default=256, required=False, help='number of bins to use for histogram (default 256)')

    options = parser.parse_args()

    statistics(options.input,
                  sort_wavelengths=options.sort_wavelengths,
                  use_bbl=options.use_bbl,
               histogram=options.histogram,
               stats=options.stats,
               numbins=options.numbins,
               band=options.band,
               wavelength=options.wavelength,
               bandname=options.bandname)

    sys.exit(0)
