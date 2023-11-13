#!/usr/bin/python3
######################################################################
##
##  solar_correction.py
##
##      Mars Solar Correction
##
##  	Created:  WHB 20090515
##	Modified: WHB 20150930, changed string.strip to str.strip
##
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

#import string

import envi2
import envi2.resample

from numpy import array

def message(s):
    pass

def read_data(fname):
    f = open(fname)
    data = list(map(float, f.read().split()))
    f.close()
    return data

def read_data2(fname):
    f = open(fname)
    data = f.readlines()
    f.close()
    data = list(map(str.strip, data))
    data = list(map(str.split, data))
    w, s = list(zip(*data))
    w = list(map(float, w))
    s = list(map(float, s))
    return w, s

def sort_wav(wav, spec):
    data = sorted(zip(wav, spec))
    return [x[0] for x in data], [x[1] for x in data]

def solar_correction(fin, fout,
                     solar_spectrum=None,
                     sort_wavelengths=True, use_bbl=True,
                             message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=True, use_bbl=use_bbl)

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    im2 = envi2.New(fout, 
                          hdr=im, interleave='bip', bbl=bbl, # this should fix it
                          data_type='d')

    if solar_spectrum:
        message('Result will be absolute relectance.')
        solwav, solar = read_data2(solar_spectrum)

        solwav, solar = sort_wav(solwav, solar)
    else:
        message('Sun-Mars distance NOT taken into account!')
        message('Result will NOT be absolute relectance.')
        solwav = read_data('wavelength.dat')
        solar = read_data('specsol_0403.dat')

        solwav, solar = sort_wav(solwav, solar)

    # this assumes that the wavelengths of the image are sorted!!!
    solres = envi2.resample.resample(array(solar), array(solwav),
                                     array(im.wavelength))

    if progress:
        progress(0.0)

    for j in range(im.lines):
        if progress:
            progress(j / float(im.lines))
        for i in range(im.samples):
            s1 = im.get_spectrum(j, i)
            im2[j,i,:] = s1 / solres

    if progress:
        progress(1.0)

    del im, im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='solar_correction.py',
##        usage='solar_correction.py -b -f -i input -o output -s solarspec',
        description='Solar correction using Solar spectrum.')

##    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
##                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-s', dest='solarspec', help='input Solar spectrum file name', required=True)

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.solarspec, "Option -s input Solar spectrum file required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    solar_correction(options.input, options.output,
                     solar_spectrum=options.solarspec,
                     sort_wavelengths=True,
                     use_bbl=options.use_bbl)
