#!/usr/bin/python3
## atmo_correction.py
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
from envi2.resample import resample

##from pylab import *
from scipy.optimize import *
import numpy

def message(s):
    pass

##def read_data(fname):
##    f = open(fname)
##    data = f.readlines()
##    f.close()
##
##    temp = []
##    for l in data:
##        for e in l.split():
##            temp.append(float(e.strip()))
##
##    return temp

def read_data2(fname, message=message):
    f = open(fname)
    data = f.readlines()
    f.close()

    wav = []
    spec = []
    for l in data:
        if len(l)==0:       # empty lines
            pass
        elif l[0] in '#;':  # comment lines
            pass
        else:
            e = l.split()
            wav.append(float(e[0].strip()))
            spec.append(float(e[1].strip()))
            
##    if not (len(wav)==352 and len(spec)==352):
##        message("incomplete transmission spectrum")
##        raise IOError("incomplete transmission spectrum")

    return wav, spec

def sort_wav(wav, spec):
    data = sorted(zip(wav, spec))
    return [x[0] for x in data], [x[1] for x in data]

def transmission(a, atmo_res):
    return atmo_res**a

def spec_busyness(a, spec, atmo_res, i1, i2):
    spec2 = spec / transmission(a, atmo_res)
    spec2 = spec2[i1:i2]
    return numpy.add.reduce(numpy.fabs(spec2[:-1] - spec2[1:]))

##def _fit_and_plot():
##    im = envi2.Open('ORB0422_4_jdat',
##                    sort_wavelengths=True, use_bbl=False)
##
###    spec = im.get_spectrum(im.lines/2, im.samples/2)
##    spec = im[100, 100]
##    wav = im.wavelength
##
##    atmo_res = resample(atmo_spec, atmo_wav, wav)
##
####    i1 = im.wavelength2index(4.0)
####    i2 = im.wavelength2index(6.0)
##    i1 = im.wavelength2index(1.8)
##    i2 = im.wavelength2index(2.2)
##
##    x, y = [], []
##    for a in arange(0.7, 1.0, 0.0001):    
##        x.append(a)
##        y.append(spec_busyness(a, spec, atmo_res, i1, i2))
##    figure(1)
##    plot(x, y)
##
##    a = fmin(spec_busyness, 0.9, (spec, atmo_res, i1, i2), ftol=0.0001)[0]
##
##    print a
##
##    T = transmission(a, atmo_res)
##    
##    cutoff = im.wavelength2index(3.5)
##    T[cutoff:] = 1.0  # cut off the transimission model above 3.5 micron
##    
##    spec2 = spec / T
##
##    figure(2)
##    plot(wav, spec, label='data', color='black', linewidth=1.0)
##    plot(wav, spec2, label='atmocor', color='blue', linewidth=1.0)

def atmo_correction(fin, fatmos, fout, falpha, sort_wavelengths=True, use_bbl=False,
                    message=message, progress=None):
    im = envi2.Open(fin,
                    sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    atmo_wav, atmo_spec = read_data2(fatmos, message)

    atmo_wav, atmo_spec = sort_wav(atmo_wav, atmo_spec)

##    plot(atmo_wav, atmo_spec)

    im2 = envi2.New(fout, hdr=im,
                    bbl=bbl,
                    interleave='bip')

    alpha = envi2.New(falpha, hdr=im, bands=1,
                    band_names=['alpha'],
                    wavelength=None, bbl=None,
                    interleave='bip')

    wav = im.wavelength

    atmo_res = resample(atmo_spec, atmo_wav, wav)

    i1 = im.wavelength2index(1.8)
    i2 = im.wavelength2index(2.2)

    if progress:
        progress(0.0)

    for j in range(im.lines):
        if progress:
            progress(j / float(im.lines))
            
        for i in range(im.samples):
            spec = im[j, i]

            # check if the spectrum is valid
            if numpy.isnan(spec_busyness(0.9, spec, atmo_res, i1, i2)):
                im2[j,i,:] = numpy.nan
                alpha[j, i] = numpy.nan
            else:
                xopt, fopt, iters, funcalls, warnflag = fmin(spec_busyness,
                            0.9, (spec, atmo_res, i1, i2), ftol=0.0001,
                            disp=False, full_output=True)
                a = xopt[0]

                T = transmission(a, atmo_res)
                
                cutoff = im.wavelength2index(3.5)
                T[cutoff:] = 1.0  # cut off the transimission model above 3.5 micron

                spec2 = spec / T

                im2[j,i,:] = spec2
                alpha[j, i] = a

    if progress:
        progress(1.0)

    del im, im2, alpha

## MAIN ##

#fit_and_plot()

#do_correct()

if __name__ == '__main__':
##    print "Run this module with tkAtmoCorrection!"

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='atmo_correction.py',
##        usage='atmo_correction.py -b -f -i input -t transmission -o output -a alpha',
        description='Atmospheric correction.')

##    parser.add_option('-s', action='store_true', dest='sort_wavelengths',
##                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output files')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-t', dest='trans', help='input transmission file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)
    parser.add_argument('-a', dest='alpha', help='output optical depth (alpha) file name', required=True)

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.trans, "Option -t input transmission file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."
##    assert options.alpha, "Option -a output alpha file required."
    assert options.force or not os.path.exists(options.alpha), "Output alpha file exists. Use -f to overwrite."

    atmo_correction(options.input, options.trans,
                    options.output, options.alpha,
                    sort_wavelengths=True,
                    use_bbl=options.use_bbl)
