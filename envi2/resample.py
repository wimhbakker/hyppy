## resample.py
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

import numpy

##def resample(s1, w1, w2):
##    """
##This functions takes one spectrum s1 with wavelengths w1 and returns a
##resampled spectrum for wavelengths w2.
##
##The wavelengths are assumed to be sorted arrays.
##
##Bilinear interpolation is performed on s1.
##"""
##
###    wout = w2[:]
##
##    sout = numpy.zeros((len(w2),))
##    w1 = numpy.array(w1)
##    
##    for i in range(len(w2)):
##        w_center = w2[i]
##        i_right = w1.searchsorted(w_center)
##        if i_right == 0 and w_center == w1[0]:
##            sout[i] = s1[0]
##        elif i_right != 0 and i_right != len(w1):
##            i_left = i_right - 1
##            w_left = w1[i_left]
##            w_right = w1[i_right]
##            a = (w_right - w_center) / (w_right - w_left)
##            b = 1 - a
##            sout[i] = a * s1[i_left] + b * s1[i_right]
##
##    return sout

def resample(s1, w1, w2):
    """
This functions takes one spectrum s1 with wavelengths w1 and returns a
resampled spectrum for wavelengths w2.

The wavelengths are assumed to be sorted arrays.

Bilinear interpolation is performed on s1.
"""

#    wout = w2[:]

    sout = numpy.zeros((len(w2),))
    w1 = numpy.array(w1)
    
    for i in range(len(w2)):
        w_center = w2[i]
        i_right = w1.searchsorted(w_center)
        if i_right == 0:
            sout[i] = s1[0]
        elif i_right == len(w1):
            sout[i] = s1[-1]
        else:
            i_left = i_right - 1
            w_left = w1[i_left]
            w_right = w1[i_right]
            a = (w_right - w_center) / (w_right - w_left)
            b = 1 - a
            sout[i] = a * s1[i_left] + b * s1[i_right]

    return sout

def gaussian(a, b, c):
    def f(x):
        return a * numpy.exp(-0.5*((x-b)/c)**2)
    return f

def convolve_gaussian(spec1, wav1, wav2, fwhm):
    spec2 = []
    for w, width in zip(wav2, fwhm):
        start = wav1.searchsorted(w - 2*width)
        end = wav1.searchsorted(w + 2*width)
        if start < end:
            factors = gaussian(1, w, width/(2*numpy.sqrt(2*numpy.log(2))))(wav1[start:end])
            s = sum(spec1[start:end] * factors) / sum(factors)
            spec2.append(s)
        else:
            spec2.append(0.0)
    return numpy.array(spec2)

# for testing
if __name__ == '__main__':
    from pylab import *

    def read_data(fname):
        f = open(fname)
        data = list(map(float, f.read().split()))
        f.close()
        return data

    def sort_wav(wav, atmo):
        data = sorted(zip(wav, atmo))
        return [x[0] for x in data], [x[1] for x in data]

    wav = read_data('wavelength.dat')
    solar = read_data('specsol_0403.dat')

    wav, solar = sort_wav(wav, solar)

    wav = array(wav)
    solar = array(solar)

    plot(wav, solar)

    grid()
    title('Mars solar spectrum (specsol_0403.dat)')
    xlabel('Wavelength (micron)')
    ylabel('Irradiance')

#    wav2 = arange(0.5, 5.0, 0.1)
#    wav2 = wav

    wav2 = wav[0] + (wav[-1] - wav[0]) * random(50)
    wav2.sort()
    
    spec2 = resample(solar, wav, wav2)

    plot(wav2, spec2)
