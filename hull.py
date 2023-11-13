#!/usr/bin/python3
## hull.py
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
from quickhull2d import hull_resampled

import numpy

def message(s):
    pass

def continuum_removal_divide(fin, fout,
                             cutoff=None,
                             sort_wavelengths=False, use_bbl=True,
                             message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if cutoff:
        if hasattr(im, 'wavelength'):
            icutoff = im.wavelength2index(cutoff) + 1
        else:
            icutoff = int(cutoff)
    else:
        icutoff = im.bands

    bbl = None
    if not use_bbl and hasattr(im, 'bbl'):
        bbl = im.bbl[:icutoff] # copy partly bbl to output header

    im2 = envi2.New(fout,
                          hdr=im, interleave='bsq', bbl=bbl,
                          bands=icutoff,
                          wavelength=im.wavelength[:icutoff],
                          data_type='d')

    oldsettings = numpy.seterr(all='ignore')
    
    if progress:
        progress(0.0)

    for j in range(im2.lines):
        if progress:
            progress(j / float(im2.lines))
        for i in range(im2.samples):
            spec = im[j, i, :icutoff].copy()
            if numpy.all(numpy.isnan(spec)):
                im2[j,i,:] = spec
            else:
                nans = numpy.where(numpy.isnan(spec))
                spec[nans] = 0
                spec_hull = hull_resampled(numpy.array(list(zip(im2.wavelength, spec))))[:,1]
                result = spec / spec_hull
                result[nans] = numpy.nan
                im2[j,i,:] = result
            
    if progress:
        progress(1.0)

    numpy.seterr(**oldsettings)
    
    del im, im2

def continuum_removal_subtract(fin, fout,
                               cutoff=None,
                               sort_wavelengths=False, use_bbl=True,
                               message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if cutoff:
        if hasattr(im, 'wavelength'):
            icutoff = im.wavelength2index(cutoff) + 1
        else:
            icutoff = int(cutoff)
    else:
        icutoff = im.bands

    bbl = None
    if not use_bbl and hasattr(im, 'bbl'):
        bbl = im.bbl[:icutoff] # copy partly bbl to output header

    im2 = envi2.New(fout,
                          hdr=im, interleave='bsq', bbl=bbl,
                          bands=icutoff,
                          wavelength=im.wavelength[:icutoff],
                          data_type='d')

    if progress:
        progress(0.0)

    for j in range(im2.lines):
        if progress:
            progress(j / float(im2.lines))
        for i in range(im2.samples):
            spec = im[j, i, :icutoff].copy()
            if numpy.all(numpy.isnan(spec)):
                im2[j,i,:] = spec
            else:
                nans = numpy.where(numpy.isnan(spec))
                spec[nans] = 0
                spec_hull = hull_resampled(numpy.array(list(zip(im2.wavelength, spec))))[:,1]
                result = 1 + (spec - spec_hull)
                result[nans] = numpy.nan
                im2[j,i,:] = result
            
    if progress:
        progress(1.0)

    del im, im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='hull.py',
##        usage='hull.py -s -b -f -i input -o output -m {div|sub} -c cutoff',
        description='Convex hull removal.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-m', dest='mode', choices=('div', 'sub'), default='div',
                      help='mode: div (divide, default), sub (subtract)')
    parser.add_argument('-c', dest='cutoff', type=float, 
                      help='cutoff wavelength (or band)')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        mode='div', cutoff=None)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.mode=='div':
        continuum_removal_divide(options.input, options.output,
                                 cutoff=options.cutoff,
                                 sort_wavelengths=options.sort_wavelengths,
                                 use_bbl=options.use_bbl)
    else:
        continuum_removal_subtract(options.input, options.output,
                                 cutoff=options.cutoff,
                                 sort_wavelengths=options.sort_wavelengths,
                                 use_bbl=options.use_bbl)
