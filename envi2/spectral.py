#########################################################################
#
# spectral.py
#
# Spectral measures
#
# Modified WHB 20090513, refactoring
# Modified WHB 20160310, added nan-safe functions
#
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

import math
import numpy

######################################################################
#
#  Some spectral distance measures.
#    input: two spectra
#    output: the distance
#

#
# SAM, Spectral Angle
#

def spectral_angle(s1, s2):
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    s1 = s1 / numpy.linalg.norm(s1)
    s2 = s2 / numpy.linalg.norm(s2)
    try:
        result = math.acos(numpy.add.reduce(s1*s2))
    except ValueError:
        result = 0.0
    return result

def nan_spectral_angle(s1, s2):
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    i = numpy.where(numpy.isfinite(s1) & numpy.isfinite(s2))
    s1 = s1[i]
    s2 = s2[i]
    s1 = s1 / numpy.linalg.norm(s1)
    s2 = s2 / numpy.linalg.norm(s2)
    try:
        result = math.acos(numpy.add.reduce(s1*s2))
    except ValueError:
        result = 0.0
    return result

#
# Euclidean distance
#

def euclidean_distance(s1, s2):
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    ds = s2 - s1
    return math.sqrt(numpy.add.reduce(ds*ds))

def nan_euclidean_distance(s1, s2):
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    ds = s2 - s1
    ds = ds[numpy.where(numpy.isfinite(ds))]
    return math.sqrt(numpy.add.reduce(ds*ds))

#
# Intensity difference
#

def intensity_difference(s1, s2):
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    i1 = math.sqrt(numpy.add.reduce(s1*s1))
    i2 = math.sqrt(numpy.add.reduce(s2*s2))
    return numpy.fabs(i2 - i1)

def nan_intensity_difference(s1, s2):
    s1 = s1.astype('d')
    s2 = s2.astype('d')
    i = numpy.where(numpy.isfinite(s1) & numpy.isfinite(s2))
    s1 = s1[i]
    s2 = s2[i]
    i1 = math.sqrt(numpy.add.reduce(s1*s1))
    i2 = math.sqrt(numpy.add.reduce(s2*s2))
    return numpy.fabs(i2 - i1)

#
# SID, Spectral Information Divergence
#

def spectral_information_divergence(s1, s2):
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

def nan_spectral_information_divergence(s1, s2):
    v = s1.astype('d')
    w = s2.astype('d')
    i = numpy.where(numpy.isfinite(v) & numpy.isfinite(w))
    v = v[i]
    w = w[i]
    r1 = v / numpy.add.reduce(v)
    r2 = w / numpy.add.reduce(w)
    tmp1 = r1 * numpy.log(r1 / r2)
    tmp1[numpy.where(numpy.isnan(tmp1) | numpy.isinf(tmp1))] = 0
    tmp2 = r2 * numpy.log(r2 / r1)
    tmp2[numpy.where(numpy.isnan(tmp2) | numpy.isinf(tmp2))] = 0
    D1 = numpy.add.reduce(tmp1)
    D2 = numpy.add.reduce(tmp2)
    return D1 + D2

#
# Bray Curtis distance
#

def bray_curtis_distance(s1, s2):
    v = s1.astype('d')
    w = s2.astype('d')
    try:
        return numpy.add.reduce(numpy.fabs(v-w)) / (numpy.add.reduce(v) + numpy.add.reduce(w))
    except:
        return 0.0

def nan_bray_curtis_distance(s1, s2):
    v = s1.astype('d')
    w = s2.astype('d')
    i = numpy.where(numpy.isfinite(v) & numpy.isfinite(w))
    v = v[i]
    w = w[i]
    try:
        return numpy.add.reduce(numpy.fabs(v-w)) / (numpy.add.reduce(v) + numpy.add.reduce(w))
    except:
        return 0.0


