#!/usr/bin/python3
## replace_value.py
##
## Copyright (C) 2010,2011 Wim Bakker
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
import numpy
import os

def message(s):
    pass

class Equal:
    def __init__(self, value):
        self.value = value
    def test(self, n):
        if numpy.isfinite(self.value):
            return n == self.value
        elif numpy.isnan(self.value):
            return numpy.isnan(n)
        elif numpy.isinf(self.value):
            return numpy.isinf(n)
        elif numpy.isposinf(self.value):
            return numpy.isposinf(n)
        elif numpy.isneginf(self.value):
            return numpy.isneginf(n)
        else:
            return False

class LessThan:
    def __init__(self, value):
        self.value = value

    def test(self, n):
        return n <= self.value

class GreaterThan:
    def __init__(self, value):
        self.value = value

    def test(self, n):
        return n >= self.value

class Between:
    def __init__(self, value1, value2):
        self.value1 = value1
        self.value2 = value2
        
    def test(self, n):
        return (self.value1 <= n) & (n <= self.value2)

def parse(s):
    result = []
    for term in s.split():
        if term[0] == '>':
            result.append(GreaterThan(float(term[1:])))
        elif term[0] == '<':
            result.append(LessThan(float(term[1:])))
        elif term.find('-') > 0:
            i = term.find('-', 1)
            result.append(Between(float(term[:i]), float(term[i+1:])))
        else:
            result.append(Equal(float(term)))
    return result

def replace_values(fin, fout, nodata=None, newdata='nan',
              sort_wavelengths=False, use_bbl=True,
              message=message, progress=None):

    nodata = parse(nodata)
    
    if os.path.exists(newdata):
        filler = envi2.Open(newdata, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
        from_file = True
    else:
        newdata = float(newdata)
        from_file = False
        
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    band_names = getattr(im, "band_names", None)
    wavelength = getattr(im, "wavelength", None)
    bbl = getattr(im, "bbl", None)
    fwhm = getattr(im, "fwhm", None)

    im2 = envi2.New(fout, hdr=im, interleave='bsq', bbl=bbl,
                          wavelength=wavelength,
                          data_type='d', band_names=band_names, fwhm=fwhm) # data_type='d'

##    # copy data
##    im2[...] = im[...]
##
##    # replace nodata by NaN's
##    for value in nodata:
##        im2.data[numpy.where(value.test(im.data))] = numpy.nan

    # copy data
    im2[...] = im[...]

    # replace nodata by NaN's
    if progress:
        progress(0.0)
    for b in range(im.bands):
        if progress:
            progress(b / float(im.bands))
        for value in nodata:
            if from_file:   # values from file
                here = numpy.where(value.test(im[b]))
                im2[b][here] = filler[b][here]
            else:           # constant value
                im2[b][numpy.where(value.test(im[b]))] = newdata

##    for j in range(im.lines):
##        if j%10==0:
##            message('.')
##        for i in range(im.samples):
##            for b in range(im.bands):
##                for value in nodata:
##                    pixel = im[j, i, b]
##                    if value.test(pixel):
##                        im2[j, i, b] = numpy.nan
##                    else:
##                        im2[j, i, b] = pixel

##    for j in range(im.lines):
##        if j%10 == 0:
##            message('.')
##        for i in range(im.samples):
##            for b in range(im.bands):
##                if im[j, i, b] in nodata:
##                    im2[j, i, b] = numpy.nan

    if progress:
        progress(1.0)

    del im, im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='replace_values.py',
##        usage='replace_values.py -s -b -f -i input -o output -n string -v newvalue',
        description='Replace nodata values to new value')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)
    parser.add_argument('-n', dest='nodata', help='list of nodata values (=string!)', required=True)
    parser.add_argument('-v', dest='newdata', help='new output value(s), can be NaN or another image file', default='nan')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False, newdata=float('nan'))

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
##    assert options.nodata is not None, "Option -n nodata values required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    replace_values(options.input, options.output, nodata=options.nodata,
                   newdata=options.newdata,
              sort_wavelengths=options.sort_wavelengths,
              use_bbl=options.use_bbl)
