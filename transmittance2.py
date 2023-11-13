#!/usr/bin/python3
## transmittance.py
##
##      Created: WHB 20110622
##
## Copyright (C) 2011 Wim Bakker
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
from pylab import *

from scipy.optimize import leastsq

def message(s):
    pass

def save_transmittance(ftrans, w, t, header=None):
    f = open(ftrans, 'w')
    if header:
        for line in header.split('\n'):
            f.write("# %s\n" % (line,))
    for tup in zip(w, t):
        f.write("%f %f\n" % tup)
    f.close()

# model 1, linear, two degrees of freedom: c0 and c1
def model1(p, x):
    c0, c1 = p
    return c0 * x + c1

def residuals1(p, y, x):
    return y - model1(p, x)

# model 2, linear, fixed c0, one degree of freedom: c1
def model2(p, x, c0):
    c1 = p
    return c0 * x + c1

def residuals2(p, y, x, c0):
    return y - model2(p, x, c0)

def transmittance(fin, fmola, ftrans, sort_wavelengths=True, use_bbl=True,
           message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    mola = envi2.Open(fmola)

    two = mola.get_band(0).astype('float64')
    x = two.flatten()
    albedo = im.get_band(im.wavelength2index(1.7149)).astype('float64')

########  PASS 1  ################
    message('PASS 1: determining scale height')

    t     = []
    c0s   = []

    # look at features between 1.8 and 2.2 micron
    for i in range(im.wavelength2index(1.8), im.wavelength2index(2.2)):
        one = im.get_band(i).astype('float64') / albedo
        one[where(~isfinite(one))] = 1

        y = log(clip(-log(one.flatten()), 0.001, 1000))

        coefs = leastsq(residuals1, [-2.0, -0.1], args=(y, x))[0]

        trans = exp(-exp(coefs[1]))
        t.append(trans)
        c0s.append(coefs[0])
        
        message('wavelength, transmittance: %f, %f' % (im.wavelength[i], trans))
        
    #determine best c0, at the deepest transmisson feature
    c0 = min(list(zip(t, c0s)))[1]
    message("c0 from the deepest feature: %f" % (c0,))
    message("Scale height H of atmosphere: %.2f km" % (-1/c0,))
    H = -1/c0




###########  PASS 2  ###################################
    message('PASS 2: determining standard transmittance')

    w     = []
    t     = []
    tmins = []
    tmaxs = []
##    R2    = []

    if progress:
        progress(0.0)

    for i in range(im.wavelength2index(0.9), im.wavelength2index(3.5)+1):
        if progress:
            progress(i / float(im.bands))
            
        one = im.get_band(i).astype('float64') / albedo
        one[where(~isfinite(one))] = 1

        y = log(clip(-log(one.flatten()), 0.001, 1000))

        ## Sensitivity analysis...
        SAMPLES = 100
        ts = []
        n = len(x)
        sidx = list(range(n))
        shuffle(sidx)
        for j in range(SAMPLES):
            idx = sidx[j*n//SAMPLES:(j+1)*n//SAMPLES]
            xsample = x[idx]
            ysample = y[idx]
            # convert to scalar by using float()
            c1 = float(leastsq(residuals2, [-2.0], args=(ysample, xsample, c0))[0])
            coefs = (c0, c1)
            ts.append(exp(-exp(coefs[1])))
        tmins.append(min(ts))
        tmaxs.append(max(ts))
        ## end sensitivity analysis...

        # convert to scalar by using float()
        c1 = float(leastsq(residuals2, [-2.0], args=(y, x, c0))[0])
        coefs = (c0, c1)

##        # calculate R-squared for this fit
##        SStot = ((y - y.mean())**2).sum()
##        SSerr = ((y - model1(coefs, x))**2).sum()
##        Rsquared = 1 - SSerr / SStot

        trans = exp(-exp(coefs[1]))
        w.append(im.wavelength[i])
        t.append(trans)
##        R2.append(Rsquared)

        message("wavelength, transmittance: %f, %f" % (im.wavelength[i], trans))
        
    if progress:
        progress(1.0)

### taken out 20131014
##    w     = hstack(([0.25, 0.99], w,     [3.7, 5.5]))
##    t     = hstack(([1.0, 1.0],   t,     [1.0, 1.0]))
##    tmins = hstack(([1.0, 1.0],   tmins, [1.0, 1.0]))
##    tmaxs = hstack(([1.0, 1.0],   tmaxs, [1.0, 1.0]))

##    R2    = hstack(([1.0, 1.0],   R2,    [1.0, 1.0]))

    save_transmittance(ftrans, w, t,
                       header="transmittance from: %s\nscale height H=%0.2f" % (fin, H))
    
    plot(w, tmins, color=(.2, .2, .2), lw=0.5, label="minimum")
    plot(w, tmaxs, color=(.2, .2, .2), lw=0.5, label="maximum")
    plot(w, array(t), 'k', label="transmittance")
##    plot(w, R2, label="R-squared")
    xlabel('wavelength')
    ylabel('transmittance')
    axis([1.0, 2.7, 0.3, 1.01])
    legend(loc=0)
    
##    message("R-squared mean: %f" % (R2[2:-2].mean(),))
##    message("R-squared max : %f" % (R2[2:-2].max(),))
##    message('\n')

    del im, two

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='transmittance2.py',
##        usage='transmittance.py -s -b -f -i input -m mola -t transmittance',
        description='Calculate Atmospheric Transmittance from OMEGA scene.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths', default=True,
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl', default=True,
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')

    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-m', dest='mola', help='MOLA input file name', required=True)

    parser.add_argument('-t', dest='transmittance', help='transmittance output file name', required=True)

##    parser.set_defaults(sort_wavelengths=True, use_bbl=True)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.mola, "Option -m MOLA input file name required."
##
##    assert options.transmittance, "Option -t transmittance output file name required."
    assert options.force or not os.path.exists(options.transmittance), "Output file exists. Use -f to overwrite."

    transmittance(options.input, options.mola, options.transmittance,
           sort_wavelengths=options.sort_wavelengths,
           use_bbl=options.use_bbl)
