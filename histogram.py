#!/usr/bin/python3
## histogram.py
##
## Copyright (C) 2021 Wim Bakker
##  Modified: 20210917 WHB created
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

def get_histogram(im, b, numbins=256, range_=None):
    bf = im[b].flatten()
    # take out nan's
    bf = bf[numpy.where(~numpy.isnan(bf))]
    hist, bins = numpy.histogram(bf, bins=numbins, range=range_, density=True)
    hist = hist / float(hist.sum()) # normalize...
    return hist, bins

def print_histogram(name, b, hist, bins):
    print('# image: %s' % (name,))
    print('# histogram of band: %d' % (b,))
    print('# bins: %d' % (len(bins)-1,))
    print('# range: %f %f' % (bins[0],bins[-1]))

    for i in range(len(hist)):
        print(bins[i], hist[i])
    print('# %f 0' % (bins[-1],))

##def print_band_statistics(im, b):
##    band = im[b].flatten()
##    # skip the NaN's
##    band = band[numpy.where(~numpy.isnan(band))]
##    if len(band) == 0: # all NaN's
##        pass
##    else:
##        band.sort()
##        mean = band.mean()
##        sdev = band.std()
##        min_ = band[0]
##        max_ = band[len(band)-1]
##        perc01  = float(band[int(0.01*len(band))]) # why float???
##        perc02 = float(band[int(0.02*len(band))])
##        perc50 = float(band[int(0.50*len(band))])
##        perc98 = float(band[int(0.98*len(band))])
##        perc99 = float(band[int(0.99*len(band))])
##        median_ = numpy.median(band)
##        mad = numpy.median(numpy.fabs(band - median_))
##
##        print('min  %f'%(min_,))
##        print('max  %f'%(max_,))
##        print('mean %f'%(mean,))
##        print('sdev %f\n'%(sdev,))
##
##        print('m-3s %f'%(mean-3*sdev,))
##        print('m-2s %f'%(mean-2*sdev,))
##        print('m-1s %f'%(mean-1*sdev,))
##        print('m    %f'%(mean,))
##        print('m+1s %f'%(mean+1*sdev,))
##        print('m+2s %f'%(mean+2*sdev,))
##        print('m+3s %f\n'%(mean+3*sdev,))
##        
##        print(' 1%%  %f'%(perc01,))
##        print(' 2%%  %f'%(perc02,))
##        print('50%%  %f'%(perc50,))
##        print('98%%  %f'%(perc98,))
##        print('99%%  %f\n'%(perc99,))
##
##        print('median    %f'%(median_,))
##        print('MAD       %f'%(mad,))
##        print('med-2mad  %f'%(median_-2*mad,))
##        print('med+2mad  %f\n'%(median_+2*mad,))

def histogram(nameIn,
              sort_wavelengths=False,
              use_bbl=False,
              numbins=256,
              range_=None,
              band=0,
              wavelength=None,
              bandname=None,
              plot=False):
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
    hist, bins = get_histogram(im, band, numbins=numbins, range_=range_)
    
    print_histogram(nameIn, band, hist, bins)

    if plot:
        import pylab as plt

        plt.bar(bins[:-1], hist, align='edge', width=bins[1]-bins[0], fill=False)
        plt.show()

    # destroy resources
    del im

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='histogram.py',
        description='Calculate and plot histogram')

    parser.add_argument('-b', action='store_true', dest='use_bbl', help='use bad band list')
    parser.add_argument('-s', action='store_true', dest='sort_wavelengths', help='sort wavelengths')
    parser.add_argument('-plot', action='store_true', dest='plot', help='plot histogram')
    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-band', dest='band', type=int, default=0, required=False, help='select band')
    parser.add_argument('-w', dest='wavelength', type=float, required=False, help='select band by wavelength')
    parser.add_argument('-bandname', dest='bandname', type=str, required=False, help='select band by bandname')
    parser.add_argument('-bins', dest='numbins', type=int, default=256, required=False, help='number of bins to use for histogram (default 256)')
    parser.add_argument('-range', dest='range', type=float, nargs=2, default=None, required=False, help='range to use for the histogram (default (min, max))')

    options = parser.parse_args()

    histogram(options.input,
               sort_wavelengths=options.sort_wavelengths,
               use_bbl=options.use_bbl,
               numbins=options.numbins,
               range_=options.range,
               band=options.band,
               wavelength=options.wavelength,
               bandname=options.bandname,
               plot=options.plot)

    sys.exit(0)
