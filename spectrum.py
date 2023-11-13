#!/usr/bin/python3
## spectrum.py
##
##      Created:  WHB 20120419
##      Modified: WHB 20150929, made coercion explicit for python3
##      Modified: WHB 20180413, now using scipy ConvexHull and interp1d for
##                              qhull and parabola fitting.
##      Modified: WHB 20221220, added spline()
##      Modified: WHB 20221221, changed description to multiline
##
## Copyright (C) 2012- Wim Bakker
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

import collections
#import operator
import math
import numpy
import os
import sys

from scipy.integrate import trapz
from scipy.signal import medfilt, bspline
import scipy.spatial
from scipy.interpolate import interp1d, UnivariateSpline
from scipy.stats import entropy

import pylab as pl
pl.ion()

try:
    from shapely.geometry import LineString, MultiPoint
except ImportError as err:
    print('import shapely: warning:', str(err))

try:
    # pip install colour-science
    import colour
    colour.utilities.filter_warnings(True, False)
except Exception as err:
    print('import colour: warning:', err, file=sys.stderr)
    print('Install with:')
    print('$ pip install colour-science')
  
#from quickhull2d import qhulltop

# Band depths for summary products
band_depths = {
'BD0530' : (0.440, 0.530, 0.648),
'BD0640' : (0.600, 0.648, 0.680),
'BD0860' : (0.800, 0.860, 0.920),
'BD1435' : (1.370, 1.430, 1.470),
'BD1500' : (1.300, 1.510, 1.695),
'BD1750' : (1.660, 1.750, 1.815),
'BD2210' : (2.140, 2.210, 2.250),
'BD2290' : (2.250, 2.290, 2.350),
'BD3100' : (3.000, 3.120, 3.250),
'BD3200' : (3.250, 3.320, 3.390),
'BD2000CO2' : (1.815, 2.010, 2.170),
'BD2600' : (2.530, 2.600, 2.630)}

## Primitive functions

def _interpol(s1, w1, w):
    """Linear interpolation of spectrum s1 with wavelengths w1 at wavelength w."""
    w_center = w
    i_right = w1.searchsorted(w_center)
    if i_right == 0:
        return s1[0]
    elif i_right == len(w1):
        return s1[-1]
    else:
        i_left = i_right - 1
        w_left = w1[i_left]
        w_right = w1[i_right]
        a = (w_right - w_center) / (w_right - w_left)
        b = 1 - a
        return a * s1[i_left] + b * s1[i_right]

def _resample(s1, w1, w2):
    """Take a spectrum s1 with wavelengths w1 and return a
resampled spectrum for wavelengths w2.

The wavelengths are assumed to be sorted arrays.

Linear interpolation is performed on s1.
"""
    sout = numpy.zeros((len(w2),))
    w1 = numpy.array(w1)
    
    for i in range(len(w2)):
        sout[i] = _interpol(s1, w1, w2[i])

    return sout

##-----------------------------------------------------------------------------------------------

## Primitive distance measures
## These functions silently assume that s1 and s2 have the same number of elements

def _spectral_angle(s1, s2):
    """SA, spectral angle"""
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    s1 = s1 / numpy.linalg.norm(s1)
    s2 = s2 / numpy.linalg.norm(s2)
    try:
        result = math.acos(numpy.add.reduce(s1*s2))
    except ValueError:
        result = 0.0
    return result

def _normxcorr(s1, s2):
    """Normalized cross-correlation"""
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    s1 = s1 / numpy.linalg.norm(s1)
    s2 = s2 / numpy.linalg.norm(s2)
    try:
        result = numpy.add.reduce(s1*s2)
    except ValueError:
        result = 0.0
    return result

def _euclidean_distance(s1, s2):
    """Euclidean distance"""
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    ds = s2 - s1
    return numpy.sqrt(numpy.add.reduce(ds*ds))

def _intensity_difference(s1, s2):
    """Intensity difference"""
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    i1 = numpy.sqrt(numpy.add.reduce(s1*s1))
    i2 = numpy.sqrt(numpy.add.reduce(s2*s2))
    return numpy.fabs(i2 - i1)

def _spectral_information_divergence(s1, s2):
    """SID, Spectral Information Divergence"""
    v = s1.astype('d')
#        v[where(v==0)] = 1
    w = s2.astype('d')
#        w[where(w==0)] = 1
    r1 = v / numpy.add.reduce(v)
    r2 = w / numpy.add.reduce(w)
    tmp1 = r1 * numpy.log(r1 / r2)
    tmp1[numpy.where(numpy.isnan(tmp1) | numpy.isinf(tmp1))] = 0
    tmp2 = r2 * numpy.log(r2 / r1)
    tmp2[numpy.where(numpy.isnan(tmp2) | numpy.isinf(tmp2))] = 0
    D1 = numpy.add.reduce(tmp1)
    D2 = numpy.add.reduce(tmp2)
    return D1 + D2

def _bray_curtis_distance(s1, s2):
    """Bray Curtis distance"""
    v = s1.astype('d')
    w = s2.astype('d')
    try:
        return numpy.add.reduce(numpy.fabs(v-w)) / (numpy.add.reduce(v) + numpy.add.reduce(w))
    except:
        return 0.0

## ----- entropy -----

def _entropy2(s1):
    """Entropy"""
    v = s1.astype('d')
    try:
        pi = v / numpy.add.reduce(numpy.fabs(v))
        return -numpy.add.reduce(pi * numpy.log2(pi))
    except:
        return 0.0


##-----------------------------------------------------------------------------------------------


## Class Spectrum
class Spectrum:
    def __init__(self, wavelength=None, spectrum=None, name=None, description='', wavelength_units=None, fwhm=None):
        """Constructor for the class Spectrum.
Wavelength and spectrum must be iterables.

The wavelengths are assumed to be sorted."""
        self.wavelength = numpy.array(wavelength) # also makes a copy
        self.spectrum = numpy.array(spectrum)
        self.shape = self.spectrum.shape
        self.name = name
        self.description = description
        self.index = 0
        self.wavelength_units = wavelength_units
        self.fwhm = fwhm
        # shorthand
        self.w = self.wavelength # SHOULD BE DELETED!!!
        self.s = self.spectrum   # SHOULD BE DELETED!!!
        # new
        self._wavelength2index_hints = dict()


    def save(self, dname):
        """Save a spectrum to a given directory.
The name of the spectrum will be used as a filename!"""
        if hasattr(self, 'name') and isinstance(self.name, str) and self.name:
            if self.name.endswith('.txt') or self.name.endswith('.asc'):
                fname = os.path.join(dname, self.name.translate(str.maketrans({'/':'_', '\\':'_'})))
            else:                
                fname = os.path.join(dname, self.name.translate(str.maketrans({'/':'_', '\\':'_'}))+'.txt')
            f = open(fname, "w")
            if self.description:
                for line in self.description.strip().split('\n'):
                    f.write("# %s\n" % (line))
            for w, s in zip(self.wavelength, self.spectrum):
                f.write("%f %f\n" % (w, s))
            f.close()

    def __iter__(self):
        """Return the iterator itself (copy)"""
        return self[...]

    def __next__(self):
        """Return next value of the iterable.

Values are 2-tuples containing a wavelength and a spectral value.

Example:
>>> for w, s in S:
	print w, s

	
0.2211 0.175487
0.2291 0.199842
0.2361 0.210632
0.2421 0.214605
...
"""
        if self.index < len(self):
##            result = self[self.index]
            result = self.wavelength[self.index], self.spectrum[self.index]
            self.index = self.index + 1
            return result
        raise StopIteration

    def __len__(self):
        """Returns the number of elements in the spectrum.

Example:
>>> len(S)
473
"""
        return len(self.spectrum)

    def _index(self, s):
        """Translates any index or range of indices to the proper spectrum
index.
It handles integers, floats, strings, slices and sequences.
"""
        if s is None:
            return None
        elif isinstance(s, slice):
            start, stop = s.start, s.stop
            step = 1 if s.step is None else s.step
            if step < 0:
                start, stop, step = stop, start, -step
            start = 0  if start is None else self._index(start)
            stop = len(self) if stop is None else self._index(stop)
            stop = min(len(self), stop+1)
            return list(range(start, stop, step))
        elif isinstance(s, float):
            return self.wavelength2index(s)
        elif isinstance(s, int):
            if s < 0:
                s = s % len(self)
            return s
        elif isinstance(s, str):
            return self.wavelength.searchsorted(s)
        elif isinstance(s, collections.abc.Iterable):
            return list(map(self._index, s))
        else:
            return s

    def __getitem__(self, i):
        """The Spectrum object can handle many things as indices.
Indices can be integers, floats, strings, slices, tuples and sequences.

Integers are normal indices:
>>> S[251]
0.83959899999999998

Floats are assumed to be wavelengths and are translated to the index with the
nearest wavelength (see wavelength2index):
>>> S[1.0]
0.83959899999999998

If the "wavelengths" are band names then the band name can be searched using
strings:
>>> S.pelkey()['olindex']
0.023354440658353237

(the function pelkey produces a Spectrum with band names instead of
wavelengths)

Slices are translated to ranges of a spectrum:
>>> S[100:200]
0.5273 0.776515
0.5293 0.778634
0.5313 0.780073
...

Floats can be used in slices:
>>> S[1.0:2.0]
1.0 0.839599
1.006 0.83894
1.012 0.839281
1.018 0.839616
...

Tuples can be used to select multiple parts from the spectrum:
>>> S[1.0:2.0, 2.5:]
1.0 0.839599
...
1.995 0.724337
2.496 0.399651
...
2.976 0.057666

A sequence can be used to select a list of particular wavelengths from a
spectrum:
>>> S[[0.5, 1.0, 1.5, 2.5, 3.0]]
0.4993 0.752254
1.0 0.839599
1.4985 0.66482
2.496 0.399651
2.976 0.057666

Combinations of the above are also possible:
>>> S[0.8:1.0:10, 270, [400, 410, 3.0]]
0.8015 0.844845
0.871 0.843062
0.964 0.842001
1.0985 0.84682
1.865 0.803714
1.965 0.748131
2.976 0.057666
"""
        if i is Ellipsis:
            return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum, name=self.name, description=self.description)
        else:
            idx = self._index(i)
            if isinstance(idx, collections.abc.Iterable) and idx:
                idx = sorted(set(numpy.r_[tuple(idx)]))
            s = self.spectrum[idx]
            w = self.wavelength[idx]
            if s.shape:
                return Spectrum(wavelength=w, spectrum=s, name=self.name, description=self.description)
            else:
                return s
##        else:
##            raise IndexError, 'invalid index'

    def __setitem__(self, i, value):
        if i is Ellipsis:
            self.spectrum = value
        else:
            idx = self._index(i)
            if isinstance(idx, collections.abc.Iterable) and idx:
                idx = sorted(set(numpy.r_[tuple(idx)]))
            if s.shape:
                self.spectrum[idx] = value
            else:
                raise ValueError('can not assign to empty spectrum')

    def __call__(self, wav):
        """Returns the band with given wavelength.

There is no check on units. There is no check on whether
the returned band is close to the requested band.

The difference with the index is that indices can contain slices while
function calls can not.
"""
        return self[wav]

    def __repr__(self):
        """Returns representation of spectrum.

All the wavelength/spectrum pairs will be returned as a string separated
by newlines:
>>> repr(S)
'0.2211 0.175487\n...2.976 0.057666\n'
"""
        result = ''
        for w, s in zip(self.wavelength, self.spectrum):
            result = result + '%s %s\n' % (str(w), str(s))
        return result

    def __str__(self):
        """Returns the Spectrum converted into string.

All the wavelength/spectrum pairs will be returned as a string of one line:
>>> str(S)
' 0.2211 0.175487 ... 2.976 0.057666'
"""
        result = ''
        for w, s in zip(self.wavelength, self.spectrum):
            result = result + ' %s %s' % (str(w), str(s))
        return result

    def wavelength2index(self, wavelength):
        """Returns the index of the band with the closest wavelength number.

Wavelength is the required wavelength.

Note that the units used should reflect the units used in the speclib.
Currently there is no check on whether the given units make any sense with
relation the the wavelengths supplied with the image.

Note that the "closest" wavelength may be the expected wavelength:
>>> S.wavelength2index(5.0)
472
>>> S.index2wavelength(472)
2.976
>>> S.wavelength[472]
2.976

In the example above we request a wavelength of 5.0 but get a wavelength
close to 3.0.
"""
        if wavelength in self._wavelength2index_hints:
            return self._wavelength2index_hints[wavelength]
        else:
            index = sorted(zip(numpy.abs(self.wavelength - wavelength),
                          list(range(len(self.wavelength)))))[0][1]
            self._wavelength2index_hints[wavelength] = index
            return index

    def index2wavelength(self, index):
        """Returns the wavelength of the band with this index.

The wavelength is returned in the units that are used in the header file.
These may be microns, nanometers or anything else...
"""
        return self.wavelength[index]

    def asymmetry(self, n=None, level=0.5):
        """Calculate asymmetry of peaks.

If n is given, only the asymmetry of the n highest peaks are returned.

Asymmetry is calculated from the distances of the peak to the left and right
shoulders.

Example:
>>> S.peaks().asymmetry(5)
2.175 -0.027896809228
2.215 0.768096263038
2.466 -0.253204867227
2.528 0.338614909345
2.816 -0.0931167428635

A negative asymmetry means that the left side is narrower than the right side
(the peak is leaning towards the left).

The returned spectrum is a pSpectrum (point spectrum).
"""
##        S = self.hull() - self
        S = self
        T = S.localmax(n)
        asym = []
        for wmax, smax in T:
            imax = S.wavelength2index(wmax)
            halfmax = smax * level

            left = None
            for i in range(imax, 0, -1): # search left
                if S.spectrum[i-1] <= halfmax:
                    left = i
                    break
            if left:
                wleft = (S.w[left-1]-S.w[left]) * ((halfmax-S.s[left])/(S.s[left-1]-S.s[left])) + S.w[left]
                
            right = None
            for i in range(imax, len(S)-1): # search right
                if S.spectrum[i+1] <= halfmax:
                    right = i
                    break
            if right:
                wright = (S.w[right+1]-S.w[right]) * ((halfmax-S.s[right])/(S.s[right+1]-S.s[right])) + S.w[right]

            if left and right:
                asym.append(((wmax-wleft)-(wright-wmax))/(wright-wleft))

        return pSpectrum(wavelength=T.w, spectrum=asym, name=self.name, description=self.description)

    def wshift(self, shift=0, mult=1):
        """Shift spectrum to higher/lower wavelengths.

For instance, shift the whole spectrum 10 nanometer to the higher
wavelengths:
>>> T = S.wshift(0.01)

>>> S
0.2211 0.175487
0.2291 0.199842
...

>>> T
0.2311 0.175487
0.2391 0.199842
...

Convert a spectrum to nanometers:
>>> T = S.wshift(mult=1000)
>>> T
221.1 0.175487
229.1 0.199842
...
"""
        return Spectrum(wavelength=self.wavelength*mult+shift, spectrum=self.spectrum, name=self.name, description=self.description)

    def shoulders(self, n=None, level=0.5):
        """Calculates shoulders of a spectrum.

If n is given then only the shoulders of the first n highest peaks are
returned.

A level of 0.5 gives full width half maximum (FWHM).

The shoulders are return as a pSpectrum (point spectrum).
The shoulders are not necessarily in sorted order."""
##        S = self.hull() - self
        S = self
        T = S.localmax(n)
        shou = []
        spec = []
        for wmax, smax in T:
            imax = S.wavelength2index(wmax)
            halfmax = smax * level

            left = None
            for i in range(imax, 0, -1): # search left
                if S.spectrum[i-1] <= halfmax:
                    left = i
                    break
            if left:
                wleft = (S.w[left-1]-S.w[left]) * ((halfmax-S.s[left])/(S.s[left-1]-S.s[left])) + S.w[left]
                shou.append(wleft)
                spec.append(halfmax)
                
            right = None
            for i in range(imax, len(S)-1): # search right
                if S.spectrum[i+1] <= halfmax:
                    right = i
                    break
            if right:
                wright = (S.w[right+1]-S.w[right]) * ((halfmax-S.s[right])/(S.s[right+1]-S.s[right])) + S.w[right]
                shou.append(wright)
                spec.append(halfmax)

        return pSpectrum(wavelength=shou, spectrum=spec, name=self.name, description=self.description)

    def integrate(self):
        """Integrate spectrum.

Calculates the area under a spectrum using the scipy.integrate.trapz
function."""
        return trapz(self.spectrum, self.wavelength)

    def interpol(self, w):
        """Linear interpolation of spectrum at wavelength w.

Example:
>>> S[[101]]
0.5293 0.778634

>>> S[[102]]
0.5313 0.780073

>>> S.interpol(0.53)
0.77913765000000001
"""
        return _interpol(self.spectrum, self.wavelength, w)

    def resample_old(self, w=None, step=None):
        """Resample spectrum to wavelengths w or in steps with size step.

Example, resample spectrum S into wavelengths of spectrum T:
>>> R = S.resample(T.w)

Example, resample spectrum S into steps of 1 nanometer:
>>> Q = S.resample(step=0.001)
>>> len(S)
473
>>> len(Q)
2755

That resampling means loss of information can be "proven" with:
>>> (S-T).absolute().sum()
0.061246582669433898
"""
        if step:
            delta = 1e-6
            if w is None:
                w = numpy.arange(self.wavelength.min(), self.wavelength.max()+delta, step)
            else:
                w = numpy.arange(w.min(), w.max()+delta, step)
        if w is None:
            return self
        else:
            s = _resample(self.spectrum, self.wavelength, w)
            return Spectrum(wavelength=w, spectrum=s, name=self.name, description=self.description)

    # old interface definition...
    def resampled(self, w=None, step=None, mode='linear'):
        return self.resample(w=w, step=step, mode=mode).spectrum

    def resample(self, w=None, step=None, mode='linear'):
        """Resample spectrum to wavelengths w or in steps with size step.

Example, resample spectrum S into wavelengths of spectrum T:
>>> R = S.resample(T.w)

Example, resample spectrum S into steps of 1 nanometer:
>>> Q = S.resample(step=0.001)
>>> len(S)
473
>>> len(Q)
2755

That resampling means loss of information can be "proven" with:
>>> (S-T).absolute().sum()
0.061246582669433898
"""
        if step:
            delta = 1e-6
            if w is None:
                w = numpy.arange(self.wavelength.min(), self.wavelength.max()+delta, step)
            else:
                w = numpy.arange(w.min(), w.max()+delta, step)
        if w is None:
            return self
        else:
            s = interp1d(self.wavelength, self.spectrum, kind=mode, bounds_error=False)(w)
            return Spectrum(wavelength=w, spectrum=s, name=self.name, description=self.description)

    def resample_bandwidth(self, w=None, bandwidth=None):
        """Resample spectrum to wavelengths w using band widths in bandwidth.
This assumes that the spectral response function (SRF) is a block function.

Example, resample spectrum S into wavelengths of ASTER:
>>> R = S.resample_bandwidth([0.56, 0.66, 0.81, 1.65, 2.165, 2.205, 2.26, 2.33, 2.395],
                             [0.08, 0.06, 0.1, 0.1, 0.04, 0.04, 0.05, 0.07, 0.07])
"""
        return Spectrum(w, [self.cut(w-bw/2, w+bw/2).integrate()/bw for w, bw in zip(w, bandwidth)], name=self.name, description=self.description)

    def resample2aster(self):
        """Resample spectrum to ASTER bands.
This does not use the real SRF of ASTER but uses an approximation
by a block function.

Example, resample spectrum S into ASTER bands:
>>> R = S.resample2aster()
"""
        if getattr(self, 'wavelength_units', 'Micrometers') == 'Nanometers':
            return self.resample_bandwidth([560.0, 660.0, 810.0, 1650.0, 2165.0, 2205.0, 2260.0, 2330.0, 2395.0],
                                 [80.0, 60.0, 100.0, 100.0, 40.0, 40.0, 50.0, 70.0, 70.0])
        else:
            return self.resample_bandwidth([0.56, 0.66, 0.81, 1.65, 2.165, 2.205, 2.26, 2.33, 2.395],
                                 [0.08, 0.06, 0.1, 0.1, 0.04, 0.04, 0.05, 0.07, 0.07])

    def cut(self, w1=None, w2=None):
        """Cut spectrum between w1 and w2.
w1 and w2 will always be the end points and may be interpolated.

The behavior of a "cut" is different from the behavior of a slice:
>>> S[1.1:1.2]
1.0985 0.84682
...
1.1985 0.846374

>>> S.cut(1.1, 1.2)
1.1 0.846604
1.1035 0.8461
...
1.1985 0.846374
1.2 0.8469995

You could see a slice as a "quick and dirty cut" and a cut as a "precise cut".
"""
        if w1 is None:
            w1 = self.wavelength[0]
        if w2 is None:
            w2 = self.wavelength[-1]
        if w1>w2:
            w1, w2 = w2, w1
        i1 = self.wavelength.searchsorted(w1)
        i2 = self.wavelength.searchsorted(w2, 'right')
        w = self.wavelength[i1:i2]
        s = self.spectrum[i1:i2]
        if not w1 in self.wavelength:
            w = numpy.hstack((w1, w))
            s = numpy.hstack((self.interpol(w1), s))
        if not w2 in self.wavelength or len(w)==1:
            w = numpy.hstack((w, w2))
            s = numpy.hstack((s, self.interpol(w2)))
        return Spectrum(wavelength=w, spectrum=s, name=self.name, description=self.description)

    def convolve(self, kernel):
        """Convolve spectrum with a linear kernel.

Kernel must contain exactly 3 values.

Example, average (smooth) spectrum S:
>>> T = S.convolve([1/3.,1/3.,1/3.])

Example, calculate gradient (edge filter) of S:
>>> T = S.convolve([-1, 0, 1])
"""
        s = self.spectrum
        a, b, c = kernel
        sum_ = sum(kernel)
        s = numpy.hstack((sum_*s[0],(a*s[:-2]+b*s[1:-1]+c*s[2:]),sum_*s[-1]))
        return Spectrum(wavelength=self.wavelength, spectrum=s, name=self.name, description=self.description)

    def smooth(self, n=1):
        """Smooth spectrum.

If n is given, smooth spectrum n times.

S.smooth() is equivalent to S.convolve([1/4., 1/2., 1/4.])

S.smooth(2) is equivalent to
S.convolve([1/4., 1/2., 1/4.]).convolve([1/4., 1/2., 1/4.])
"""
        s = self.spectrum
        for i in range(n):
            s = numpy.hstack((s[0],(2*s[1:-1]+s[:-2]+s[2:])/4.0,s[-1]))
        return Spectrum(wavelength=self.wavelength, spectrum=s, name=self.name, description=self.description)

##    def spline(self, s=0.001):
##        spl = UnivariateSpline(self.w, self.s, s=s)
##        mini = self.w.min()
##        maxi = self.w.max()
##        # ten times oversampling... BUT WHY?
##        x = numpy.arange(mini, maxi, (maxi-mini) / len(self.w) / 10)
##        return Spectrum(wavelength=x, spectrum=spl(x), name=self.name)

    def spline(self, s=0.001, wavelength=None):
        """UnivariateSpline. Can resample at the same time."""
        spl = UnivariateSpline(self.wavelength, self.spectrum, s=s)
        if wavelength is None:
            wavelength = self.wavelength
        return Spectrum(wavelength=wavelength, spectrum=spl(wavelength), name=self.name, description=self.description)

    def medfilt(self, n=3):
        """Smooth spectrum with a median filter.

Uses scipy.signal.medfilt

Note that median filtering may introduce flat areas in a spectrum
which means that local extrema may not be found anymore.
"""
        return Spectrum(wavelength=self.wavelength, spectrum=medfilt(self.spectrum, kernel_size=n), name=self.name, description=self.description)

## THIS NEEDS WORK
##    def bspline(self, n=2):
##        """Smooth spectrum with a bspline.
##
##Uses scipy.signal.bspline
##"""
##        return Spectrum(wavelength=self.wavelength, spectrum=bspline(self.spectrum, n), name=self.name)

    def entropy2(self):
        return _entropy2(self.spectrum)

    def entropy(self):
        return entropy(self.spectrum)

    def gradient(self):
        """returns a first order derivative of a spectrum."""
        s = self.spectrum
        w = self.wavelength
        s = numpy.hstack((0,(s[2:]-s[:-2])/(w[2:]-w[:-2]),0))
        return Spectrum(wavelength=self.wavelength, spectrum=s, name=self.name, description=self.description)

    def second(self):
        """Returns a second order derivative of a spectrum."""
        s = self.spectrum
        w = self.wavelength
        s = numpy.hstack((0,(s[2:]-2*s[1:-1]+s[:-2])/((w[2:]-w[1:-1])*(w[1:-1]-w[:-2])),0))
        return Spectrum(wavelength=self.wavelength, spectrum=s, name=self.name, description=self.description)

    def localminidx(self, n=None):
        """Return array of indices of the n smallest local minima."""
        a = self.spectrum
        idx = numpy.where((a[1:-1]<a[:-2]) & (a[1:-1]<a[2:]))[0]+1
        if n and len(idx):
            s = self.spectrum[idx]
            s, idx = list(zip(*sorted(sorted(zip(s, idx))[:n], key=lambda x:x[1])))
        return numpy.array(idx)

    def localminfit(self, n=None, broad=False):
        """Fit the n smallest local minima with a parabola."""
        idx = self.localminidx(n)
        if broad:
            return self._fitparabola_broad(idx)
        else:
            return self._fitparabola(idx)

    def _fitparabola(self, idx):
        """Fit parabola through three adjacent points"""
        w = self.wavelength
        s = self.spectrum
        new_w = []
        new_s = []
        for i in idx:
            x = [w[i-1], w[i], w[i+1]]
            y = [s[i-1], s[i], s[i+1]]
            coef = numpy.polyfit(x, y, 2)
            a, b, c = coef
            x_ext = -b / (2 * a)
            y_ext = numpy.polyval(coef, x_ext)
            new_w.append(x_ext)
            new_s.append(y_ext)
        return pSpectrum(wavelength=new_w, spectrum=new_s, name=self.name, description=self.description)

    def _fitparabola_broad(self, idx):
        """Fit broad parabola through adjacent points"""
        w = self.wavelength
        s = self.spectrum
        new_w = []
        new_s = []
        for i in idx:
            lowidx = i - 1
            while lowidx-1 > 0 and s[lowidx-1] <= (s[i]+1)/2:
                lowidx = lowidx - 1
            highidx = i + 1
            while highidx+1 < len(s)-1 and s[highidx+1] <= (s[i]+1)/2:
                highidx = highidx + 1
            x = w[lowidx:highidx+1]
            y = s[lowidx:highidx+1]
            coef = numpy.polyfit(x, y, 2)
            a, b, c = coef
            x_ext = -b / (2 * a)
            y_ext = numpy.polyval(coef, x_ext)
            new_w.append(x_ext)
            new_s.append(y_ext)
        return pSpectrum(wavelength=new_w, spectrum=new_s, name=self.name, description=self.description)

    def localmin(self, n=None):
        """Return the local minima of the spectrum.

If n is given, return the n smallest local minima.

Returns a pSpectrum (point spectrum)."""
        idx = self.localminidx(n)
        w = self.wavelength[idx]
        s = self.spectrum[idx]
        return pSpectrum(wavelength=w, spectrum=s, name=self.name, description=self.description)

    def minwav(self, n=None, mode='div', broad=False):
        """Calculate the minimum wavelength.

Equivalent to:
1 - S.nohull().localminfit(n)

Returns a pSpectrum (point spectrum) containing wavelength/depth pairs.
"""
        S = 1 - self.nohull(mode=mode).localminfit(n, broad=broad)
        return pSpectrum(wavelength=S.wavelength, spectrum=S.spectrum, name=self.name, description=self.description)

    def localmaxidx(self, n=None):
        """Return indices of the local maxima.

If n is given, return only the n largest local maxima."""
        a = self.spectrum
        idx = numpy.where((a[1:-1]>a[:-2]) & (a[1:-1]>a[2:]))[0]+1
        if n and len(idx):
            s = self.spectrum[idx]
            s, idx = list(zip(*sorted(sorted(zip(s, idx), reverse=True)[:n], key=lambda x:x[1])))
        return numpy.array(idx)

    def localmaxfit(self, n=None):
        """Fit the n largest local maxima with parabola."""
        idx = self.localmaxidx(n)
        return self._fitparabola(idx)

    def localmax(self, n=None):
        """Return the local maxima of the spectrum.

If n is given, return the n largest local maxima.

Returns a pSpectrum (point spectrum)."""
        idx = self.localmaxidx(n)
        w = self.wavelength[idx]
        s = self.spectrum[idx]
        return pSpectrum(wavelength=w, spectrum=s, name=self.name, description=self.description)

    ## miscellaneous functions

    def nonan(self):
        """Remove NaNs from spectrum."""
        w = self.wavelength
        s = self.spectrum
        idx = numpy.where(numpy.isfinite(s))[0]
        w = w[idx]
        s = s[idx]
        return Spectrum(wavelength=w, spectrum=s, name=self.name, description=self.description)

##    def hull_old(self):
##        """Returns convex hull as a spectrum.
##
##Example:
##>>> H = S.hull()
##
##Note that the hull may contain less points than the original spectrum:
##>>> len(S)
##473
##>>> len(H)
##23
##"""
##        S = self.nonan()
##        ws = qhulltop(numpy.vstack((S.wavelength, S.spectrum)).T)
##        return Spectrum(wavelength=ws[:,0], spectrum=ws[:,1], name=self.name)
##
##    def hull_v1(self):
##        """Returns convex hull as a spectrum.
##
##Example:
##>>> H = S.hull()
##
##Note that the hull may contain less points than the original spectrum:
##>>> len(S)
##473
##>>> len(H)
##23
##"""
##        S = self.nonan()
##        H = ConvexHull(numpy.vstack((S.w, S.s)).transpose())
##        # detrmine the upper part of the hull...
##        idx = numpy.roll(H.vertices, len(H.vertices) - 1 - H.vertices.argmin())[::-1]
##        idx = idx[:idx.argmax()+1]
##        return Spectrum(wavelength=S.w[idx], spectrum=S.s[idx], name=self.name)

    def hull(self):
        """Returns convex hull as a spectrum.

Example:
>>> H = S.hull()

Note that the hull may contain less points than the original spectrum:
>>> len(S)
473
>>> len(H)
23
"""
        # remove the NaN's from the spectrum, convex hull of a NaN is a NaN...
        S = self.nonan()
        if len(S)<2:
            return numpy.nan
        try:
            # determine vertices of the convex hull and make them clockwise...
            Hvert = scipy.spatial.ConvexHull(numpy.vstack((S.w, S.s)).transpose()).vertices[::-1]
            # determine the upper part of the hull, put the index zero on index zero...
            idx = numpy.roll(Hvert, -Hvert.argmin())
            # cut everything above the last index...
            idx = idx[:idx.argmax()+1]
        except scipy.spatial.qhull.QhullError: # convex hull is flat
            # return index of first and last points
            idx = numpy.array([0,len(S)-1])
        # return these points as a spectrum again...
        return Spectrum(wavelength=S.w[idx], spectrum=S.s[idx], name=self.name, description=self.description)

    def nohull(self, mode='div'):
        """Returns the continuum removed as a spectrum.

Two modes are implemented: 'div' (divide) and 'sub' (subtract).
Any other mode will simply return the spectrum itself.

Mode 'div' is equivalent to:
S / S.hull()

Mode 'sub' is equivalent to:
1 + (S - S.hull())

Mode 'div' (divide) is the default.
"""
        if mode=='div':
            return self / self.hull()
        elif mode=='sub':
            return 1 + (self - self.hull())
        else:
            return self

    def busyness(self):
        return numpy.add.reduce(numpy.fabs(self.spectrum[:-1] - self.spectrum[1:]))

    def peaks(self):
        """Calculate absorption peaks from a spectrum.

Equivalent to:
S.hull() - S
"""
        return self.hull() - self

    def dpeaks(self):
        """Calculate absorption peaks from a spectrum.

The function calculates the distance between the spectrum and its
convex hull.

The calculation is done using the geometry part of the Python module
'shapely'. If shapely is not installed this function will raise a
NotImplementedError exception.
"""
        S = self.nonan()
        try:
            l = LineString(tuple(S.hull()))
            p = MultiPoint(tuple(S))
            return Spectrum(wavelength=S.wavelength, spectrum=list(map(l.distance, p)), name=self.name, description=self.description)
        except NameError:
            raise NotImplementedError("function 'dpeaks' needs module 'shapely.geometry'")
        
    def plot(self, *args, **kwargs):
        """Plot a spectrum as lines.

Example, plot spectrum and its convex hull in one window:
>>> S.plot()
>>> S.hull().plot()
"""
        if len(self.wavelength):
            if isinstance(self.wavelength[0], str):
                bar(list(range(len(self))), self.spectrum)
                xticks(arange(0.4, len(self)), self.wavelength)
                setp(subplot(111).get_xticklabels(), rotation=30)
            else:
                pl.plot(self.wavelength, self.spectrum, *args, **kwargs)
        return 'plot'

    def pplot(self, *args, **kwargs):
        """Plot spectrum as points."""
        pl.plot(self.wavelength, self.spectrum, 'o', *args, **kwargs)
        return 'plot'

    def wplot(self, *args, **kwargs):
        """Plot wavelengths as vertical lines.

Example, plot a spectrum and indicate the 5 deepest absorption peaks
with dotted vertical lines:
>>> S.peaks().plot()
'plot'
>>> S.peaks().localmax(5).wplot()
'plot'
"""
        y1, y2 = kwargs.get('y1', 0), kwargs.get('y2', 1)
        for w in self.wavelength:
            pl.plot([w, w], [y1, y2], 'k:', *args, **kwargs)
        return 'plot'

    ## OPERATORS

    def __add__(self, other):
        """Add operator."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum+getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __radd__(self, other):
        """Radd operator (right add)."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return self.__add__(other)
        
    def __sub__(self, other):
        """Subtract operator."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum-getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __rsub__(self, other):
        """Rsub operator (right subtract)."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=getattr(other, 'spectrum', other)-self.spectrum, name=self.name, description=self.description)
        
    def __mul__(self, other):
        """Multiply operator"""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum*getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __rmul__(self, other):
        """Rmul operator (right multiply)."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return self.__mul__(other)
        
    def __truediv__(self, other):
        """Division operator."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum/getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __rtruediv__(self, other):
        """Rdiv operator (right division)."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=getattr(other, 'spectrum', other)/self.spectrum, name=self.name, description=self.description)
        
    def __pow__(self, other):
        """Power operator."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum**getattr(other, 'spectrum', other), name=self.name, description=self.description)
        
    def __rpow__(self, other):
        """Rpow operator (right power)."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=getattr(other, 'spectrum', other)**self.spectrum, name=self.name, description=self.description)

    def __neg__(self):
        """Negative operator."""
        return Spectrum(wavelength=self.wavelength, spectrum=-self.spectrum, name=self.name, description=self.description)

    def __pos__(self):
        """Positive operator."""
        return Spectrum(wavelength=self.wavelength, spectrum=+self.spectrum, name=self.name, description=self.description)

    def __abs__(self):
        """Abs operator."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.abs(self.spectrum), name=self.name, description=self.description)

    ## CONVERSIONS

    def int(self):
        """Convert spectral values to integers."""
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum.astype('int'), name=self.name, description=self.description)

    def long(self):
        """Convert spectral values to long integers."""
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum.astype('long'), name=self.name, description=self.description)

    def float(self):
        """Convert spectral values to floating point numbers."""
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum.astype('float'), name=self.name, description=self.description)

    def astype(self, t):
        """Convert spectral values to type t.

For type codes see for instance numpy.typeDict

Example, convert a spectrum to byte values:
>>> T = (255.99*S).astype('u1')
"""
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum.astype(t), name=self.name, description=self.description)

    ## COMPARISON operators

    def __lt__(self, other):
        """Operator less than."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum<getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __le__(self, other):
        """Operator less than or equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum<=getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __eq__(self, other):
        """Operator equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.equal(self.spectrum,getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def __ne__(self, other):
        """Operator not equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum!=getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __ge__(self, other):
        """Operator greater than or equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum>=getattr(other, 'spectrum', other), name=self.name, description=self.description)

    def __gt__(self, other):
        """Operator greater than."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=self.spectrum>getattr(other, 'spectrum', other), name=self.name, description=self.description)

    ## NUMPY functions

    def log(self):
        """Numpy function log."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.log(self.spectrum), name=self.name, description=self.description)

    def add(self, other):
        """Numpy function add."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.add(self.spectrum, getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def subtract(self, other):
        """Numpy function subtract."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.subtract(self.spectrum, getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def multiply(self, other):
        """Numpy function multiply."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.multiply(self.spectrum, getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def divide(self, other):
        """Numpy function divide."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.divide(self.spectrum, getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def negative(self):
        """Numpy function negative."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.negative(self.spectrum), name=self.name, description=self.description)

    def power(self, other):
        """Numpy function power."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.power(self.spectrum, getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def absolute(self):
        """Numpy function absolute."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.absolute(self.spectrum), name=self.name, description=self.description)

    def sign(self):
        """Numpy function sign."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.sign(self.spectrum), name=self.name, description=self.description)

    def exp(self):
        """Numpy function exp with base e (2.7182818284590451)."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.exp(self.spectrum), name=self.name, description=self.description)

    def exp2(self):
        """Numpy function exp2 with base 2."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.exp2(self.spectrum), name=self.name, description=self.description)

    def log2(self):
        """Numpy function log2 with base 2."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.log2(self.spectrum), name=self.name, description=self.description)

    def log10(self):
        """Numpy function log10 with base 10."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.log10(self.spectrum), name=self.name, description=self.description)

    def sqrt(self):
        """Numpy function square root."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.sqrt(self.spectrum), name=self.name, description=self.description)

    def square(self):
        """Numpy function square."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.square(self.spectrum), name=self.name, description=self.description)

    def reciprocal(self):
        """Numpy function reciprocal."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.reciprocal(self.spectrum), name=self.name, description=self.description)

    def sin(self):
        """Numpy function sin."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.sin(self.spectrum), name=self.name, description=self.description)

    def cos(self):
        """Numpy function cos."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.cos(self.spectrum), name=self.name, description=self.description)

    def tan(self):
        """Numpy function tan."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.tsn(self.spectrum), name=self.name, description=self.description)

    def arcsin(self):
        """Numpy function arcsin."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.arcsin(self.spectrum), name=self.name, description=self.description)

    def arccos(self):
        """Numpy function arccos."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.arccos(self.spectrum), name=self.name, description=self.description)

    def arctan(self):
        """Numpy function arctan."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.arctan(self.spectrum), name=self.name, description=self.description)

    def arctan2(self, other):
        """Numpy function arctan2."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.arctan2(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def hypot(self, other):
        """Numpy function hypot."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.hypot(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def sinh(self):
        """Numpy function sinh."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.sinh(self.spectrum), name=self.name, description=self.description)

    def cosh(self):
        """Numpy function cosh."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.cosh(self.spectrum), name=self.name, description=self.description)

    def tanh(self):
        """Numpy function tanh."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.tanh(self.spectrum), name=self.name, description=self.description)

    def arcsinh(self):
        """Numpy function arcsinh."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.arcsinh(self.spectrum), name=self.name, description=self.description)

    def arccosh(self):
        """Numpy function arccosh."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.arccosh(self.spectrum), name=self.name, description=self.description)

    def arctanh(self):
        """Numpy function arctanh."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.arctanh(self.spectrum), name=self.name, description=self.description)

    def deg2rad(self):
        """Numpy function deg2rad."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.deg2rad(self.spectrum), name=self.name, description=self.description)

    def rad2deg(self):
        """Numpy function rad2deg."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.rad2deg(self.spectrum), name=self.name, description=self.description)

    def greater(self, other):
        """Numpy function greater."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.greater(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def greater_equal(self, other):
        """Numpy function greater_equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.greater_equal(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def less(self, other):
        """Numpy function less."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.less(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def less_equal(self, other):
        """Numpy function less_equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.less_equal(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def not_equal(self, other):
        """Numpy function not_equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.not_equal(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def equal(self, other):
        """Numpy function equal."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.equal(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def maximum(self, other):
        """Numpy function maximum."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.maximum(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def minimum(self, other):
        """Numpy function minimum."""
        self, other = self.__coerce__(other) # force coercion into Spectrum objects
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.minimum(self.spectrum,  getattr(other, 'spectrum', other)), name=self.name, description=self.description)

    def mean(self, *args):
        """Numpy function mean."""
        return numpy.mean(self.spectrum)

    def all(self, *args):
        """Numpy function all."""
        return numpy.all(self.spectrum)

    def any(self, *args):
        """Numpy function any."""
        return numpy.any(self.spectrum)

    def clip(self, a, b, *args):
        """Numpy function clip.

Clip values to between minimum a and maximum b."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.clip(self.spectrum, a, b), name=self.name, description=self.description)

    def copy(self):
        """Numpy function copy."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.copy(self.spectrum), name=self.name, description=self.description)

    def cumprod(self, *args):
        """Numpy function cumprod."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.cumprod(self.spectrum), name=self.name, description=self.description)

    def cumsum(self, *args):
        """Numpy function cumsum."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.cumsum(self.spectrum), name=self.name, description=self.description)

    def min(self, *args):
        """Numpy function min."""
        return numpy.min(self.spectrum)

    def max(self, *args):
        """Numpy function max."""
        return numpy.max(self.spectrum)

    def prod(self, *args):
        """Numpy function prod."""
        return numpy.prod(self.spectrum)

    def round(self, *args):
        """Numpy function round."""
        return Spectrum(wavelength=self.wavelength, spectrum=numpy.round(self.spectrum), name=self.name, description=self.description)

    def std(self, *args):
        """Numpy function std."""
        return numpy.std(self.spectrum)

    def sum(self, *args):
        """Numpy function sum."""
        return numpy.sum(self.spectrum)

    def var(self, *args):
        """Numpy function var."""
        return numpy.var(self.spectrum)

    def where(self):
        """Numpy function where.

The where function returns indices of values that are true.

Example, plot all values of S where S is larger than 0.84:
>>> S[(S>0.84).where()].plot()
"""
        return where(self.spectrum)

    def __coerce_extended__(self, other):
        """Coerce one spectrum into another if needed.

This determines the union of the sets of wavelengths of both spectra and
resamples both spectra into the unioned wavelengths.

Wavelengths of the union are sorted afterwards.
"""
        if isinstance(other, Spectrum):
            ### SHOULDN'T THIS BE LIMITED TO THE OVERLAPPING RANGE(S)???
            w = sorted(set(self.wavelength)|set(other.wavelength))
            return self.resample(w), other.resample(w)
        else:
            return self, other

    def __coerce__(self, other):
        """Coerce one spectrum into another if needed.

This determines the union of the sets of wavelengths of both spectra and
resamples both spectra into the unioned wavelengths.

Wavelengths are limited to the overlapping area of the two spectra.

Wavelengths of the union are sorted afterwards.
"""
        if isinstance(other, Spectrum):
            wmin = max(self.wavelength.min(), other.wavelength.min())
            wmax = min(self.wavelength.max(), other.wavelength.max())
            w = sorted(set(self.wavelength)|set(other.wavelength))
            w = numpy.array(w)
            w = w[numpy.where((wmin<=w) & (w<=wmax))]
            return self.resample(w), other.resample(w)
        else:
            return self, other

    def pelkey(S):
        """Returns Summary Products of a spectrum.

Reference:
Pelkey et al., 2007, J. Geophys. Res.,
Crism multispectral summary products: Parameterizing mineral diversity
on Mars from reflectance.

The result is a Spectrum with band names rather than wavelengths.

Currently 39 summary products are implemented.
"""
        w = []
        s = []

        for key in band_depths:
            wl, wc, wr = band_depths[key]
            b = (wc - wl) / (wr - wl)
            a = 1 - b
            w.append(key.lower())
            s.append(1-(S[wc] / (a*S[wl] + b*S[wr])))

        w.append('olindex')
        s.append((S[1.695] / (0.1 * S[1.050] + 0.1 * S[1.210] + 0.4 * S[1.330] + 0.4 * S[1.470])) - 1)

        w.append('lcpindex')
        s.append(((S[1.330] - S[1.050]) / (S[1.330] + S[1.050])) * ((S[1.330] - S[1.815]) / ( S[1.330] + S[1.815])))

        w.append('hcpindex')
        s.append(((S[1.470] - S[1.050]) / (S[1.470] + S[1.050])) * ((S[1.470] - S[2.067]) / ( S[1.470] + S[2.067])))

############################
  
        w.append('islope1')
        s.append((S[1.815] - S[2.530]) / (2.530 - 1.815))

        CR = S[1.8:2.53].nohull()
        w.append('drop2300')
        s.append(1 - ((CR[2.290] + CR[2.320] + CR[2.330]) / (CR[2.140] + CR[2.170] + CR[2.210])))
        
        w.append('drop2400')
        s.append(1 - ((CR[2.390] + CR[2.430]) / (CR[2.290] + CR[2.320])))
        
        w.append('bd3400')
        a = 0.909
        b = 1 - a
        c = 0.605
        d = 1 - c
        s.append(1 - ((a * S[3.390] + b * S[3.500]) / (c * S[3.250] + d * S[3.630])))
        
        w.append('cindex')
        s.append((S[3.750] + (S[3.750] - S[3.630]) / (3.750-3.630) * (3.950-3.750)) / S[3.950] - 1)
        
        w.append('rbr')
        s.append(S[0.770] / S[0.440])
        
        w.append('sh600')
        b = (0.600-0.530) / (0.680-0.530)
        a = 1 - b
        s.append(S[0.600] / (a * S[0.530] + b * S[0.680]))
        
        w.append('icer1')
        s.append(S[1.510] / S[1.430])
        
        w.append('bd1900')
        b = (1.958-1.857) / (2.067-1.857)
        a = 1 - b
        s.append(1 - (((S[1.930] + S[1.985]) * 0.5) / (a * S[1.857] + b * S[2.067])))

        w.append('bd2100')
        b = (2.130-1.930) / (2.250-1.930)
        a = 1 - b
        s.append(1 - (((S[2.120] + S[2.140]) * 0.5) / (a * S[1.930] + b * S[2.250])))

        w.append('icer2')
        s.append(S[2.530] / S[2.600])

        w.append('bdcarb')
        b = (2.330-2.230) / (2.390-2.230)
        a = 1 - b
        res1 = S[2.330] / (a * S[2.230] + b * S[2.390])
        b = (2.530-2.390) / (2.600-2.390)
        a = 1 - b
        res2 = S[2.530] / (a * S[2.390] + b * S[2.600])
        s.append(1 - (numpy.sqrt(res1 * res2)))

        w.append('r410')
        s.append(S[0.410])

        w.append('r770')
        s.append(S[0.770])

        w.append('ira')
        s.append(S[1.330])

        w.append('irr1')
        s.append(S[0.800] / S[1.020])

        w.append('irr2')
        s.append(S[2.530] / S[2.210])

        w.append('irr3')
        s.append(S[3.750] / S[3.500])

        w.append('bd1270o2')
        b = (1.265 - 1.261) / (1.268 - 1.261)
        a = 1 - b
        d = (1.265 - 1.250) / (1.280 - 1.250)
        c = 1 - d
        s.append(1 - ((a * S[1.261] + b * S[1.268]) / (c * S[1.250] + d * S[1.280])))

        w.append('bd3000')
        s.append(1 - (S[3.000] / (S[2.530] * (S[2.530] / S[2.210]))))

        w.append('bd1400h2o')
        b = (1.380 - 1.370) / (1.400 - 1.370)
        a = 1 - b
        d = (1.380 - 1.330) / (1.510 - 1.330)
        c = 1 - d
        s.append(1 - ((a * S[1.370] + b * S[1.400]) / (c * S[1.330] + d * S[1.510])))

        w.append('r2700')
        s.append(S[2.700])

        w.append('bd2700')
        s.append(1 - (S[2.700] / (S[2.530] * (S[2.530] / S[2.350]))))

        w.append('var')
        T = S[1.0:2.3]
        s.append((T - T.fit()).var())

        return Spectrum(wavelength=w, spectrum=s).sort()

    def sort(self):
        """Returns a spectrum sorted by wavelength."""
        return Spectrum(*list(zip(*sorted(zip(self.wavelength, self.spectrum)))), name=self.name, description=self.description)

    def fit(self, n=1):
        """Fit a polynomial with order n through spectrum.

The resulting interpolated spectrum has exactly the same wavelengths as
the input spectrum."""
        coef = numpy.polyfit(self.wavelength, self.spectrum, n)
        s = numpy.polyval(coef, self.wavelength)
        return Spectrum(wavelength=self.wavelength, spectrum=s, name=self.name, description=self.description)

    ## distance measures
    def SA(self, other):
        if isinstance(other, Spectrum):
            self, other = self.__coerce__(other)
            return _spectral_angle(self.s, other.s)
        else:
            result = []
            for s2 in other:
                self, s2 = self.__coerce__(s2)
                result.append(_spectral_angle(self.s, s2.s))
            return result

    def normxcorr(self, other):
        if isinstance(other, Spectrum):
            self, other = self.__coerce__(other)
            return _normxcorr(self.s, other.s)
        else:
            result = []
            for s2 in other:
                self, s2 = self.__coerce__(s2)
                result.append(_normxcorr(self.s, s2.s))
            return result

    def ED(self, other):
        if isinstance(other, Spectrum):
            self, other = self.__coerce__(other)
            return _euclidean_distance(self.s, other.s)
        else:
            result = []
            for s2 in other:
                self, s2 = self.__coerce__(s2)
                result.append(_euclidean_distance(self.s, s2.s))
            return result

    def ID(self, other):
        if isinstance(other, Spectrum):
            self, other = self.__coerce__(other)
            return _intensity_difference(self.s, other.s)
        else:
            result = []
            for s2 in other:
                self, s2 = self.__coerce__(s2)
                result.append(_intensity_difference(self.s, s2.s))
            return result

    def SID(self, other):
        if isinstance(other, Spectrum):
            self, other = self.__coerce__(other)
            return _spectral_information_divergence(self.s, other.s)
        else:
            result = []
            for s2 in other:
                self, s2 = self.__coerce__(s2)
                result.append(_spectral_information_divergence(self.s, s2.s))
            return result

    def BC(self, other):
        if isinstance(other, Spectrum):
            self, other = self.__coerce__(other)
            return _bray_curtis_distance(self.s, other.s)
        else:
            result = []
            for s2 in other:
                self, s2 = self.__coerce__(s2)
                result.append(_bray_curtis_distance(self.s, s2.s))
            return result

    def dict(self):
        return collections.OrderedDict(zip(self.wavelength, self.spectrum))

    def tuple(self):
        return tuple(zip(self.wavelength, self.spectrum))

    def CIELab(S):
        Sres = S.resample(numpy.arange(int(S.w.min()), S.w.max(), 1))
        spd = colour.SpectralPowerDistribution('Sample', Sres.dict())
        cmfs = colour.STANDARD_OBSERVERS_CMFS['CIE 1931 2 Degree Standard Observer']
        illuminant = colour.ILLUMINANTS_RELATIVE_SPDS['D50']
        XYZ = colour.spectral_to_XYZ(spd, cmfs, illuminant)
        Lab = colour.XYZ_to_Lab(XYZ)
        return Lab

    def CIExyY(S):
        Sres = S.resample(numpy.arange(int(S.w.min()), S.w.max(), 1))
        spd = colour.SpectralPowerDistribution('Sample', Sres.dict())
        cmfs = colour.STANDARD_OBSERVERS_CMFS['CIE 1931 2 Degree Standard Observer']
        illuminant = colour.ILLUMINANTS_RELATIVE_SPDS['D50']
        XYZ = colour.spectral_to_XYZ(spd, cmfs, illuminant)
        xyY = colour.XYZ_to_xyY(XYZ)
        return xyY

##
## Class pSpectrum
##

class pSpectrum(Spectrum):
    """A pSpectrum is a Spectrum that plots as points.

A pSpectrum does not need to be sorted.

Except for the plotting functions the behavior of a pSpectrum is the
same as the behavior of a Spectrum."""
    def lplot(self, *args, **kwargs):
        """Plot pSpectrum as lines."""
        pl.plot(self.wavelength, self.spectrum, *args, **kwargs)
        return 'plot'

    def plot(self, *args, **kwargs):
        """Plot pSpectrum as points."""
        pl.plot(self.wavelength, self.spectrum, 'o', *args, **kwargs)
        return 'plot'

## Factory functions.........................

def Open(fname):
# assuming 2-column ascii data, cross your fingers...
##            description = data[0] # maybe there's something in line 1?
    f = open(fname, 'r')
    data = f.readlines()
    f.close()

    description = ''
    result = []
    
    for line in data:
        if line.startswith('#'): # comment?
            if description:
                description = description + '\n' + line.strip('# \n')
            else:
                description = line.strip('# \n')
            continue
        if ',' in line:
            words = line.strip().split(',')
        else:
            words = line.strip().split()
        try:
            w, r = words[0].strip(), words[1].strip()
        except IndexError:
            continue
        try:
            result.append([float(w), float(r)])
        except ValueError:
            continue

    if result:
        w, r = list(zip(*result))
        return Spectrum(name=os.path.basename(fname), wavelength=numpy.array(w),
                                 spectrum=numpy.array(r), description=description)
    else:
        return None

if __name__ == '__main__':
    """For testing."""
    from pylab import *
    
    # test data (alunite)
    w = numpy.array([ 0.2211,  0.2291,  0.2361,  0.2421,  0.2481,  0.2536,  0.2586,
        0.2636,  0.2686,  0.2731,  0.2771,  0.2971,  0.3011,  0.3051,
        0.3091,  0.3131,  0.3171,  0.3211,  0.3251,  0.3291,  0.3331,
        0.3371,  0.3411,  0.3451,  0.3491,  0.3531,  0.3571,  0.3606,
        0.3636,  0.3666,  0.3696,  0.3726,  0.3756,  0.3786,  0.3811,
        0.3831,  0.3851,  0.3871,  0.3891,  0.3911,  0.3951,  0.3971,
        0.3991,  0.4011,  0.4031,  0.4051,  0.4071,  0.4091,  0.4111,
        0.4128,  0.4158,  0.4188,  0.4218,  0.4248,  0.4278,  0.4308,
        0.4338,  0.4368,  0.4398,  0.4428,  0.4458,  0.4488,  0.4513,
        0.4533,  0.4553,  0.4573,  0.4593,  0.4613,  0.4633,  0.4653,
        0.4673,  0.4693,  0.4713,  0.4733,  0.4753,  0.4773,  0.4793,
        0.4813,  0.4833,  0.4853,  0.4873,  0.4893,  0.4913,  0.4933,
        0.4953,  0.4973,  0.4993,  0.5013,  0.5033,  0.5053,  0.5073,
        0.5093,  0.5113,  0.5133,  0.5153,  0.5173,  0.5193,  0.5213,
        0.5233,  0.5253,  0.5273,  0.5293,  0.5313,  0.5333,  0.5353,
        0.5373,  0.5393,  0.5413,  0.5433,  0.5453,  0.5473,  0.5493,
        0.5513,  0.5533,  0.5553,  0.5573,  0.5593,  0.5613,  0.5633,
        0.5653,  0.5673,  0.5693,  0.5713,  0.5733,  0.5753,  0.5773,
        0.5793,  0.5813,  0.5833,  0.5853,  0.5873,  0.5893,  0.5913,
        0.5933,  0.5953,  0.5973,  0.5993,  0.6011,  0.6027,  0.6043,
        0.6059,  0.6075,  0.6091,  0.6107,  0.6123,  0.6139,  0.6155,
        0.6171,  0.6187,  0.6203,  0.6219,  0.6235,  0.6251,  0.6267,
        0.6283,  0.6299,  0.6317,  0.6337,  0.6357,  0.6377,  0.6397,
        0.6417,  0.6437,  0.6457,  0.6477,  0.6497,  0.6517,  0.6537,
        0.6557,  0.6577,  0.6597,  0.6617,  0.6637,  0.6657,  0.6677,
        0.6702,  0.6732,  0.6762,  0.6792,  0.6822,  0.6852,  0.6882,
        0.6912,  0.6942,  0.6972,  0.7002,  0.702 ,  0.704 ,  0.706 ,
        0.708 ,  0.71  ,  0.712 ,  0.714 ,  0.716 ,  0.718 ,  0.72  ,
        0.722 ,  0.724 ,  0.726 ,  0.728 ,  0.73  ,  0.732 ,  0.734 ,
        0.736 ,  0.738 ,  0.74  ,  0.742 ,  0.744 ,  0.746 ,  0.748 ,
        0.7505,  0.7535,  0.7565,  0.7595,  0.7625,  0.7655,  0.7685,
        0.7715,  0.7745,  0.7775,  0.781 ,  0.785 ,  0.789 ,  0.793 ,
        0.797 ,  0.8015,  0.8065,  0.8115,  0.8165,  0.822 ,  0.828 ,
        0.835 ,  0.843 ,  0.851 ,  0.859 ,  0.871 ,  0.883 ,  0.894 ,
        0.904 ,  0.914 ,  0.924 ,  0.933 ,  0.941 ,  0.949 ,  0.957 ,
        0.964 ,  0.97  ,  0.976 ,  0.982 ,  0.988 ,  0.994 ,  1.    ,
        1.006 ,  1.012 ,  1.018 ,  1.0235,  1.0285,  1.0335,  1.0385,
        1.0435,  1.0485,  1.0535,  1.0585,  1.0635,  1.0685,  1.0735,
        1.0785,  1.0835,  1.0885,  1.0935,  1.0985,  1.1035,  1.1085,
        1.1135,  1.1185,  1.1235,  1.1285,  1.1335,  1.1385,  1.1435,
        1.1485,  1.1535,  1.1585,  1.1635,  1.1685,  1.1735,  1.1785,
        1.1835,  1.1885,  1.1935,  1.1985,  1.2035,  1.2085,  1.2135,
        1.2185,  1.2235,  1.2285,  1.2335,  1.2385,  1.2435,  1.2485,
        1.2535,  1.2585,  1.2635,  1.2685,  1.2735,  1.2785,  1.2835,
        1.2885,  1.2935,  1.2985,  1.3035,  1.3085,  1.3135,  1.3185,
        1.3235,  1.3285,  1.3335,  1.3385,  1.3435,  1.3485,  1.3535,
        1.3585,  1.3635,  1.3685,  1.3735,  1.3785,  1.3835,  1.3885,
        1.3935,  1.3985,  1.4035,  1.4085,  1.4135,  1.4185,  1.4235,
        1.4285,  1.4335,  1.4385,  1.4435,  1.4485,  1.4535,  1.4585,
        1.4635,  1.4685,  1.4735,  1.4785,  1.4835,  1.4885,  1.4935,
        1.4985,  1.5035,  1.5085,  1.5135,  1.5185,  1.5235,  1.5285,
        1.534 ,  1.54  ,  1.546 ,  1.552 ,  1.558 ,  1.564 ,  1.5705,
        1.5775,  1.5845,  1.5915,  1.5985,  1.6055,  1.6125,  1.6195,
        1.6265,  1.6335,  1.6405,  1.6475,  1.6545,  1.6615,  1.6685,
        1.676 ,  1.684 ,  1.692 ,  1.7   ,  1.708 ,  1.716 ,  1.724 ,
        1.732 ,  1.74  ,  1.748 ,  1.756 ,  1.764 ,  1.772 ,  1.78  ,
        1.788 ,  1.796 ,  1.805 ,  1.815 ,  1.825 ,  1.835 ,  1.845 ,
        1.855 ,  1.865 ,  1.875 ,  1.885 ,  1.895 ,  1.905 ,  1.915 ,
        1.925 ,  1.935 ,  1.945 ,  1.955 ,  1.965 ,  1.975 ,  1.985 ,
        1.995 ,  2.005 ,  2.015 ,  2.025 ,  2.035 ,  2.045 ,  2.055 ,
        2.065 ,  2.075 ,  2.085 ,  2.095 ,  2.105 ,  2.115 ,  2.125 ,
        2.135 ,  2.145 ,  2.155 ,  2.165 ,  2.175 ,  2.185 ,  2.195 ,
        2.205 ,  2.215 ,  2.225 ,  2.235 ,  2.245 ,  2.255 ,  2.265 ,
        2.275 ,  2.285 ,  2.295 ,  2.305 ,  2.315 ,  2.325 ,  2.335 ,
        2.345 ,  2.355 ,  2.365 ,  2.375 ,  2.386 ,  2.4   ,  2.418 ,
        2.44  ,  2.466 ,  2.496 ,  2.528 ,  2.56  ,  2.592 ,  2.624 ,
        2.656 ,  2.688 ,  2.72  ,  2.752 ,  2.784 ,  2.816 ,  2.848 ,
        2.88  ,  2.912 ,  2.944 ,  2.976 ])

    s = numpy.array([ 0.175487,  0.199842,  0.210632,  0.214605,  0.216859,  0.219901,
        0.220581,  0.228739,  0.235611,  0.2439  ,  0.250142,  0.293858,
        0.303571,  0.314905,  0.325072,  0.336394,  0.348118,  0.358257,
        0.368293,  0.374761,  0.382962,  0.38949 ,  0.396072,  0.403249,
        0.410077,  0.42004 ,  0.430907,  0.440927,  0.45009 ,  0.45896 ,
        0.467371,  0.475541,  0.483807,  0.492924,  0.503009,  0.511678,
        0.519139,  0.527199,  0.536459,  0.544787,  0.563038,  0.572452,
        0.580346,  0.591233,  0.600019,  0.60807 ,  0.615383,  0.622056,
        0.630891,  0.635168,  0.643149,  0.647961,  0.65194 ,  0.65613 ,
        0.656292,  0.656409,  0.65592 ,  0.659421,  0.666166,  0.674199,
        0.68147 ,  0.689731,  0.696457,  0.700992,  0.706053,  0.708486,
        0.714182,  0.715856,  0.717481,  0.719798,  0.721314,  0.723759,
        0.724952,  0.728565,  0.729276,  0.73223 ,  0.735045,  0.734666,
        0.737433,  0.738928,  0.740307,  0.743284,  0.743033,  0.745364,
        0.747152,  0.749521,  0.752254,  0.752785,  0.754973,  0.756726,
        0.757975,  0.759228,  0.760903,  0.763103,  0.764964,  0.768285,
        0.768201,  0.770252,  0.772781,  0.775695,  0.776515,  0.778634,
        0.780073,  0.783057,  0.784319,  0.784427,  0.786946,  0.788299,
        0.788186,  0.791469,  0.794575,  0.7931  ,  0.794968,  0.795576,
        0.798378,  0.797726,  0.799348,  0.80434 ,  0.805263,  0.80531 ,
        0.807863,  0.80789 ,  0.808663,  0.809776,  0.810156,  0.811324,
        0.811456,  0.812524,  0.812815,  0.812284,  0.814574,  0.814544,
        0.815058,  0.817125,  0.814996,  0.815799,  0.816577,  0.815699,
        0.815251,  0.816331,  0.816275,  0.817547,  0.817403,  0.817845,
        0.817019,  0.817533,  0.817794,  0.817756,  0.820107,  0.818563,
        0.818718,  0.820525,  0.819284,  0.819418,  0.819053,  0.819605,
        0.81938 ,  0.819282,  0.818436,  0.820432,  0.821691,  0.821319,
        0.821478,  0.823511,  0.822915,  0.824405,  0.823598,  0.823125,
        0.825203,  0.825454,  0.826074,  0.827595,  0.826693,  0.82643 ,
        0.827814,  0.827478,  0.828807,  0.829081,  0.831879,  0.831867,
        0.832884,  0.832143,  0.834062,  0.834012,  0.83737 ,  0.834504,
        0.833153,  0.835788,  0.835031,  0.836323,  0.83659 ,  0.836545,
        0.837659,  0.837402,  0.838109,  0.838332,  0.838735,  0.838091,
        0.839041,  0.840543,  0.840141,  0.840231,  0.840445,  0.84117 ,
        0.840059,  0.841495,  0.842522,  0.841511,  0.842362,  0.842013,
        0.843233,  0.842454,  0.842607,  0.843419,  0.843139,  0.843667,
        0.843887,  0.844846,  0.842354,  0.844614,  0.84387 ,  0.844296,
        0.844494,  0.844739,  0.845463,  0.844845,  0.845878,  0.845822,
        0.845391,  0.846618,  0.844761,  0.845721,  0.845835,  0.843767,
        0.842613,  0.843062,  0.84209 ,  0.842714,  0.842292,  0.840872,
        0.839643,  0.841574,  0.841873,  0.840033,  0.838734,  0.842001,
        0.841105,  0.840876,  0.840971,  0.840055,  0.841497,  0.839599,
        0.83894 ,  0.839281,  0.839616,  0.843554,  0.843911,  0.843482,
        0.844473,  0.844894,  0.845233,  0.84609 ,  0.846248,  0.845538,
        0.845826,  0.846103,  0.846132,  0.844968,  0.84695 ,  0.847395,
        0.84682 ,  0.8461  ,  0.847351,  0.846049,  0.847163,  0.847047,
        0.84843 ,  0.848864,  0.847338,  0.847884,  0.848842,  0.847815,
        0.848134,  0.848   ,  0.849211,  0.848657,  0.848641,  0.84986 ,
        0.849865,  0.850484,  0.846374,  0.848459,  0.846718,  0.846308,
        0.845819,  0.845165,  0.845212,  0.842527,  0.843556,  0.842214,
        0.843363,  0.841444,  0.84122 ,  0.840385,  0.835698,  0.833236,
        0.833052,  0.836644,  0.838917,  0.841435,  0.844154,  0.845773,
        0.844861,  0.844571,  0.84352 ,  0.843387,  0.839507,  0.838166,
        0.836904,  0.836789,  0.834764,  0.836683,  0.838307,  0.83634 ,
        0.837362,  0.839522,  0.838527,  0.838458,  0.838251,  0.837365,
        0.836555,  0.834187,  0.829514,  0.823326,  0.811291,  0.790966,
        0.762365,  0.70855 ,  0.689908,  0.713864,  0.746353,  0.776987,
        0.778937,  0.771977,  0.764882,  0.751689,  0.734808,  0.732019,
        0.712679,  0.66851 ,  0.66482 ,  0.735337,  0.773858,  0.784422,
        0.786852,  0.794285,  0.802121,  0.81296 ,  0.82175 ,  0.823467,
        0.824008,  0.826679,  0.832371,  0.829288,  0.832511,  0.832488,
        0.832443,  0.832628,  0.834785,  0.836164,  0.836175,  0.837039,
        0.837743,  0.837751,  0.837414,  0.836066,  0.8351  ,  0.835076,
        0.830512,  0.830258,  0.82989 ,  0.828115,  0.819911,  0.808711,
        0.790542,  0.769318,  0.748504,  0.726715,  0.714226,  0.703622,
        0.712047,  0.739856,  0.771963,  0.798766,  0.813462,  0.818354,
        0.819104,  0.817473,  0.81323 ,  0.808303,  0.803714,  0.797161,
        0.787529,  0.77767 ,  0.770559,  0.765144,  0.760384,  0.76179 ,
        0.760367,  0.752748,  0.748131,  0.74751 ,  0.737111,  0.724337,
        0.713303,  0.704842,  0.704417,  0.694581,  0.686094,  0.677786,
        0.673157,  0.670261,  0.660806,  0.656096,  0.646192,  0.63837 ,
        0.615541,  0.57907 ,  0.531635,  0.491638,  0.470605,  0.467273,
        0.481941,  0.516372,  0.557522,  0.549052,  0.576136,  0.633218,
        0.691124,  0.713686,  0.711234,  0.712914,  0.707439,  0.688609,
        0.652439,  0.588319,  0.558089,  0.579317,  0.613529,  0.633305,
        0.638946,  0.613712,  0.554899,  0.51062 ,  0.487931,  0.428681,
        0.408526,  0.399651,  0.364699,  0.417503,  0.436489,  0.505513,
        0.532239,  0.434605,  0.35839 ,  0.230827,  0.099473,  0.041393,
        0.016607,  0.035372,  0.030192,  0.032314,  0.057666])

    S = Spectrum(name='alunite_al706.966.asc', wavelength=w, spectrum=s)
    Sres = S.resample(numpy.arange(ceil(S.w.min()), S.w.max(), 1))
    
##    import colour
##
##    colour.filter_warnings(True, False)
##    spd = colour.SpectralPowerDistribution('Sample', Sres.dict())
##    cmfs = colour.STANDARD_OBSERVERS_CMFS['CIE 1931 2 Degree Standard Observer']
##    illuminant = colour.ILLUMINANTS_RELATIVE_SPDS['D50']
##    XYZ = colour.spectral_to_XYZ(spd, cmfs, illuminant)
##    xyY = colour.XYZ_to_xyY(XYZ)
##    print("xyY coordinate", xyY)
##    Lab = colour.XYZ_to_Lab(XYZ)
##    print("Lab coordinate", Lab)

##    mun = colour.xyY_to_munsell_colour(xyY)
