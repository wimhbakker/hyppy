#!/usr/bin/python3
## transmittance.py
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

##delta = 1

def message(s):
    pass

def save_transmittance(ftrans, w, t):
    f = open(ftrans, 'w')
    for tup in zip(w, t):
        f.write("%f %f\n" % tup)
    f.close()

def transmittance(fin, fmola, ftrans, sort_wavelengths=True, use_bbl=True,
           message=message):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    mola = envi2.Open(fmola)

    two = mola.get_band(0).astype('float64')
    albedo = im.get_band(im.wavelength2index(1.7149)).astype('float64')

    w = [0.25, 0.99]
    t = [1.0, 1.0]
    tmins = [1.0, 1.0]
    tmaxs = [1.0, 1.0]
    R2 = [1.0, 1.0]
    for i in range(im.wavelength2index(1.0), im.wavelength2index(3.5)):
        one = im.get_band(i).astype('float64') / albedo
        x = two.flatten()
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
            coefs = polyfit(xsample, ysample, 1, full=False)
            ts.append(exp(-exp(coefs[1])))
        tmins.append(min(ts))
        tmaxs.append(max(ts))
        ## end sensitivity analysis...

        coefs = polyfit(x, y, 1)

        # calculate R-squared for this fit
        SStot = ((y - y.mean())**2).sum()
        SSerr = ((y - polyval(coefs, x))**2).sum()
        Rsquared = 1 - SSerr / SStot

        trans = exp(-exp(coefs[1]))
        w.append(im.wavelength[i])
        t.append(trans)
        R2.append(Rsquared)

        message("%f %f" % (im.wavelength[i], trans))
        
    w.append(3.7)
    t.append(1.0)
    tmins.append(1.0)
    tmaxs.append(1.0)
    R2.append(1.0)

    w.append(5.5)
    t.append(1.0)
    tmins.append(1.0)
    tmaxs.append(1.0)
    R2.append(1.0)

    R2 = array(R2)

    save_transmittance(ftrans, w, t)
    
    plot(w, tmins, 'r', lw=0.5, label="minimum")
    plot(w, tmaxs, 'r', lw=0.5, label="maximum")
    plot(w, array(t), 'k', label="transmittance")
##    plot(w, R2, label="R-squared")
    xlabel('wavelength')
    ylabel('transmittance')
    axis([1.0, 2.7, 0.3, 1.01])
    legend(loc=0)
    
    message("R-squared mean: %f" % (R2[2:-2].mean(),))
    message("R-squared max : %f" % (R2[2:-2].max(),))
##    message('\n')

    del im, two

if __name__ == '__main__':
##    transmittance('/data/tmp/4604/ORB4604_5_jdat_Scor', '/data/tmp/4604/ORB4604_5_mola', '/data/tmp/4604/ORB4604_5_jdat_Scor_trans.dat')
##    transmittance('/data/tmp/0422/ORB0422_4_jdat_Scor', '/data/tmp/0422/ORB0422_4_mola', '/data/tmp/0422/ORB0422_4_jdat_Scor_trans.dat')

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='transmittance.py',
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
