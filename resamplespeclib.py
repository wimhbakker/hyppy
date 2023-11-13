#!/usr/bin/python3
## resamplespeclib.py
##
## Copyright (C) 2019 Wim Bakker
##  Created: WHB 20190207
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
##from envi2.constants import *
import spectrum
import ascspeclib

import numpy as np
##from scipy.interpolate import interp1d
##from scipy.optimize import fmin
import os

import time

def message(s):
    print(s)

##def load_spectra(nameIn, recursive=False):
##    if os.path.isdir(nameIn):
##        speclib = ascspeclib.AscSpeclib(nameIn, recursive=recursive)
##    else:
##        try:
##            speclib = envi2.Speclib(nameIn)
##        except (AttributeError, IOError):
##            speclib = ascspeclib.AscSpeclib(nameIn, recursive=recursive)
##    return speclib

def load_spectra(nameIn, recursive=False):
    return ascspeclib.AscSpeclib(nameIn, recursive=recursive)

def convert_pseudo_speclib(fin, dirout=None, message=message, progress=None):
    speclib = envi2.Open(fin, sort_wavelengths=False, use_bbl=False)

    if not (os.path.exists(dirout) and os.path.isdir(dirout)):
        os.makedirs(dirout)

    if progress:
        progress(0.0)

    for j, spec_name in enumerate(speclib.header.spectra_names):
        if progress:
            progress(j / speclib.lines)
            
        message(spec_name)

        fname = os.path.join(dirout, spec_name.translate(str.maketrans({'/':'_'}))+'.txt')
        f = open(fname, "w")
        f.write("# Spectral Library:\n")
        f.write("# %s\n" % (fin,))
        f.write("# Spectra name:\n")
        f.write("# %s\n" % (spec_name,))
        for band_name, s in zip(speclib.band_names, speclib[j,0,:]):
            f.write("\"%s\" %f\n" % (band_name, s))
        f.close()

    if progress:
        progress(1.0)

def resample_speclib(fin, dirout=None, to_spec=None, sort_wavelengths=True, use_bbl=False, recursive=False,
                     wmultiplier=1.0, message=message, progress=None):

    try:
        sl = envi2.Open(fin, sort_wavelengths=False, use_bbl=False)
        if not hasattr(sl, 'wavelength') and hasattr(sl, 'band_names'):
            convert_pseudo_speclib(fin, dirout=dirout, message=message, progress=None)
            return
    except ValueError:
        pass
    
    speclib = load_spectra(fin)

    if not (os.path.exists(dirout) and os.path.isdir(dirout)):
        os.makedirs(dirout)

    if to_spec:    
        try: # try ENVI image first
            im = envi2.Open(to_spec, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
            if hasattr(im.header, 'fwhm'):
                to_spectrum = spectrum.Spectrum(wavelength=im.wavelength, fwhm=im.header.fwhm)
            else:
                to_spectrum = spectrum.Spectrum(wavelength=im.wavelength)
        except ValueError: # try an ENVI or ASCII spectral library
            to_speclib = load_spectra(to_spec)
            to_spectrum = to_speclib[0]
    else:
        to_spectrum = speclib[0]
        
    if progress:
        progress(0.0)

    i = 0
    for S in speclib:
        if progress:
            i = i + 1
            progress(i / len(speclib))
            
        message(S.name)
        S.wavelength = S.wavelength * wmultiplier
        if to_spectrum.fwhm:
            out_S = S.resample_bandwidth(to_spectrum.w, to_spectrum.fwhm)
        else:
            out_S = S.resample(to_spectrum.w)
        out_S.save(dirout)

    if progress:
        progress(1.0)

def resample_speclib_to_envi(fin, enviout=None, to_spec=None, sort_wavelengths=True, use_bbl=False, recursive=False,
                     wmultiplier=1.0, message=message, progress=None):

    speclib = load_spectra(fin)

    if to_spec:       
        try: # try ENVI image / SL first
            im = envi2.Open(to_spec, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
            if hasattr(im.header, 'fwhm'):
                to_spectrum = spectrum.Spectrum(wavelength=im.wavelength, fwhm=im.header.fwhm)
            else:
                to_spectrum = spectrum.Spectrum(wavelength=im.wavelength)
        except ValueError: # try an ENVI or ASCII spectral library
            to_speclib = load_spectra(to_spec)
            to_spectrum = to_speclib[0]
    else:
        to_spectrum = speclib[0]
        
    if progress:
        progress(0.0)

    i = 0
    for S in speclib:
        if progress:
            i = i + 1
            progress(i / len(speclib))
            
        message(S.name)
        S.wavelength = S.wavelength * wmultiplier

    speclib.save_as_envi(enviout, wavelength=to_spectrum.wavelength)

    if progress:
        progress(1.0)

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='resamplespeclib.py',
        description='Convert / Resample Spectral Library.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-r', action='store_true', dest='recursive',
                      help='recursively scan input directory')
    parser.add_argument('-m', dest='wmultiplier', help='input wavelength multiplier',
                        default=1.0, type=float, required=False)
    parser.add_argument('-i', dest='input', help='input spectral library', required=True)
    parser.add_argument('-t', dest='tospec', help='resample to', required=False)

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-o', dest='output', help='output ASCII directory')
    group.add_argument('-e', dest='envioutput', help='output ENVI Speclib')

    options = parser.parse_args()

    if options.output:
        resample_speclib(options.input, dirout=options.output, to_spec=options.tospec, sort_wavelengths=options.sort_wavelengths,
                 use_bbl=options.use_bbl, recursive=options.recursive, wmultiplier=options.wmultiplier)
    else:
        resample_speclib_to_envi(options.input, enviout=options.envioutput, to_spec=options.tospec, sort_wavelengths=options.sort_wavelengths,
                 use_bbl=options.use_bbl, recursive=options.recursive, wmultiplier=options.wmultiplier)
