#!/usr/bin/python3
## thermal_correction.py
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

import planck

from pylab import *
from scipy.optimize import leastsq
##from numpy import array

const1 = 0

# blackbody curve, wavelength in microns
def blackbody(wav, temp):
    c1 = 0.000001 # per micron!
    return c1 * planck.planck(wav * 1e-6, temp)

# this models the solar radiation curve
def model1(params, wav):
    c0 = params
    return c0 * blackbody(wav, planck.SOLAR_T)

def residuals1(p, y, x):
    return y - model1(p, x)

# this models the solar curve + bb radiation from the object itself
def model2(params, wav):
    global const1
    temp = params
    # average reflectance at 5 micron is half that of the 2.5 micron
    # average reflectance at 5 micron is 0.15, emissivity = 0.85???
    return 0.5 * const1 * blackbody(wav, planck.SOLAR_T) + 0.85 * blackbody(wav, temp)
#    return const1 * blackbody(wav, planck.SOLAR_T) + blackbody(wav, temp)

def residuals2(p, y, x):
    return y - model2(p, x)

def message(s):
    pass

def thermal_correction(fin, fout, fthermal, sort_wavelengths=True, use_bbl=True,
                       message=message, progress=None):
    global const1
    im = envi2.Open(fin,
                    sort_wavelengths=True, use_bbl=use_bbl)

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl
        
    im2 = envi2.New(fout, hdr=im, bbl=bbl,
                    interleave='bip')

    therm = envi2.New(fthermal, hdr=im, bands=2,
                    band_names=['Reflectance', 'Temperature'],
                    wavelength=None, bbl=None,
                    interleave='bip')

    wav = im.wavelength

    i1 = wav.searchsorted(2.2)
    i2 = wav.searchsorted(2.5)
    i3 = wav.searchsorted(5.0)

    twav1 = wav[i1:i2]
    twav2 = wav[i3:]

    if progress:
        progress(0.0)

    for j in range(im.lines):
        if progress:
            progress(j / float(im.lines))
        for i in range(im.samples):
            spec = im.get_spectrum(j, i)

            # step 1: match solar curve
            tspec = spec[i1:i2]

            if isfinite(tspec).all():
                params = leastsq(residuals1, [0.1], args=(tspec, twav1))[0]

                const1 = params

                therm[j,i,0] = const1
            else:
                therm[j,i,0] = nan

            # step 2: match thermal curve
            tspec = spec[i3:]

            if isfinite(tspec).all():
                params = leastsq(residuals2, [230.0], args=(tspec, twav2))[0]

                temp = params

                therm[j,i,1] = temp

                # subtract thermal effect
                im2[j,i,:] = (spec - 0.85 * blackbody(wav, temp)) # / (const1 * blackbody(wav, planck.SOLAR_T))
            else:
                therm[j, i, 1] = nan
                im2[j, i, :] = nan

    if progress:
        progress(1.0)

    del im, im2, therm

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='thermal_correction.py',
##        usage='thermal_correction.py -b -f -i input -o output -t thermal',
        description='Thermal correction.')

##    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
##                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output files')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-t', dest='thermal', help='output thermal file name', required=True)

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."
##    assert options.thermal, "Option -t output thermal file required."
    assert options.force or not os.path.exists(options.thermal), "Output thermal file exists. Use -f to overwrite."

    thermal_correction(options.input, options.output, options.thermal,
                       sort_wavelengths=True,
                       use_bbl=options.use_bbl)
