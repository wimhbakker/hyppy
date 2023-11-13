#!/usr/bin/python3
## mask_noisy_bands.py
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

import os
import envi2
import numpy
import time

from pylab import *
ion()

#from scipy.stats.stats import nanmean, nanstd
from numpy import nanmean, nanstd

def message(s):
    print(s)

def silent(s):
    pass

# this should be pushed to envi2.header
def find_header_file(fname):
    result = fname + '.hdr'
    if os.path.isfile(result):
        return result
    
    result = os.path.splitext(fname)[0] + '.hdr'
    if os.path.isfile(result):
        return result
    
    result = fname
    if os.path.isfile(result):
        return result
    
    return None

def local_busyness(band):
    x = nanmean(numpy.fabs(band[:, 1:] - band[:, :-1]).flatten())
    y = nanmean(numpy.fabs(band[1:, :] - band[:-1, :]).flatten())
    return max(x, y)

def mask_noisy_bands(fin, threshold=20.0,
                 sort_wavelengths=False, use_bbl=False,
                 message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=False, use_bbl=False)

    snr = []
    bsnr = []
    message("band: mean, std, snr, mean/busyness")
    if progress:
        progress(0.0)
    for b in range(im.bands):
        if progress:
            progress(b / float(im.bands))
        band = im[b]
        busy = local_busyness(band)
        
        band = im[b].flatten()
        m = nanmean(band)
        s = nanstd(band)
        message("%d: %.2f, %.2f, %.2f, %.2f" % (b, m, s, (m/s)**2, (m/busy)))
        if s == 0.0:
            snr.append(0.0)
            bsnr.append(0.0)
        else:
            snr.append((m / s)**2)
            bsnr.append((m / busy))

    wav = im.wavelength[:]

    a = numpy.where(numpy.array(bsnr) <= threshold)

    message(" These %d bands will be marked as bad" % (len(a[0]),))
    message(str(a[0]))

    if hasattr(im.header, 'original_bbl'):
        original_bbl = numpy.array(im.header.original_bbl[:])
    elif hasattr(im.header, 'bbl'):        
        original_bbl = numpy.array(im.header.bbl[:])
    else:
        original_bbl = numpy.array(im.bands * [1])
        
    new_bbl = numpy.array(original_bbl[:])

    if a:
        new_bbl[a] = 0

    message("Original BBL:")
    message(str(original_bbl))

    message("New BBL:")
    message(str(new_bbl))

    message("Setting up new header")
    hdr = envi2.Header(hdr=im, bbl=new_bbl, original_bbl=original_bbl)

    if progress:
        progress(1.0)

    del im

    hdr_file = find_header_file(fin)
    if hdr_file:
        message('Writing header file: ' + hdr_file)
        hdr.write(hdr_file)
    else:
        message('No header file found!')

    # make plot
    wav, snr, bsnr = list(zip(*sorted(zip(wav, snr, bsnr))))
    
##    plot(wav, snr, 'b')
    plot([wav[0], wav[-1]], [threshold, threshold], 'r')
    plot(wav, bsnr, 'g')

if __name__ == '__main__':
##    print "Run this module using tkMaskNoisyBands.py!"

    # command line version
    import optparse
    import os

    parser = optparse.OptionParser(
        usage='mask_noisy_bands.py -v -p -i input -t threshold',
        description='Mask noisy bands in bad band list (BBL) of the header.')

##    parser.add_option('-s', action='store_true', dest='sort_wavelengths',
##                      help='sort bands on wavelength')
##    parser.add_option('-b', action='store_true', dest='use_bbl',
##                      help='use bad band list from the header')
##    parser.add_option('-f', action='store_true', dest='force',
##                      help='force overwrite on existing output file')
    parser.add_option('-i', dest='input', help='input file name')
##    parser.add_option('-o', dest='output', help='output file name')

    parser.add_option('-v', action='store_true', dest='verbose',
                      help='verbose: print useful info')
    parser.add_option('-p', action='store_true', dest='plot',
                      help='plot signal to noise ratio and threshold')
    parser.add_option('-t', dest='threshold', type='float',
                      help='threshold for bad bands')

    parser.set_defaults(threshold=20.0, verbose=False, plot=False)

    (options, args) = parser.parse_args()

    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
##    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.verbose:
        mask_noisy_bands(options.input, threshold=options.threshold,
                         message=message)
    else:
        mask_noisy_bands(options.input, threshold=options.threshold,
                         message=silent)

    if options.plot:
        show()

##    close('all')
