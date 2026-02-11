#!/usr/bin/python3
## stretch.py
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

from numpy import nanmin, nanmax, where, isfinite, fabs
##from scipy.stats.stats import nanmean, nanstd, nanmedian, cumfreq
from numpy import nanmean, nanstd

try:
    from numpy import nanmedian
except ImportError:
    from scipy.stats.stats import nanmedian
    
from scipy.stats import cumfreq

def minmax_stretch(b):
    # note: the flatten is here to avoid a bug in nanmin and nanmax
    # in numpy version 1.6.2
    bf = b.flatten()
    min_ = nanmin(bf)
    return (255.99*(b-min_)/(nanmax(bf)-min_)).astype('u1')

def percent_stretch(b, perc=0.01):
    band = b.flatten()
    # skip the NaN's
    band = band[where(isfinite(band)==True)]
    if len(band) == 0: # all NaN's
        return b.astype('u1')
    else:
        band.sort()
        min_ = float(band[int(perc*len(band))]) # why float??? For unsigned data types!
        max_ = float(band[int((1-perc)*len(band))])
        return (255.99*(b-min_)/float(max_-min_)).clip(0, 255).astype('u1')

def percent_percent_stretch(b, percmin=0.01, percmax=0.99):
    band = b.flatten()
    # skip the NaN's
    band = band[where(isfinite(band)==True)]
    if len(band) == 0: # all NaN's
        return b.astype('u1')
    else:
        band.sort()
        min_ = float(band[int(percmin*len(band))]) # why float???
        max_ = float(band[int(percmax*len(band))])
        return (255.99*(b-min_)/float(max_-min_)).clip(0, 255).astype('u1'), min_, max_

def stddev_stretch(b):
    bf = b.flatten()
    m = nanmean(bf)
    s = nanstd(bf)
    min_ = m - 2*s
    max_ = m + 2*s
    min_ = max(nanmin(bf), min_)
    max_ = min(nanmax(bf), max_)
    return (255.99*(b-min_)/(max_-min_)).clip(0, 255).astype('u1')

# Uses median and 3*MAD
def mad_stretch(b):
    bf = b.flatten()
    m = nanmedian(bf)
    s = nanmedian(fabs(bf - m))
    min_ = m - 3*s
    max_ = m + 3*s
    min_ = max(nanmin(bf), min_)
    max_ = min(nanmax(bf), max_)
    return (255.99*(b-min_)/(max_-min_)).clip(0, 255).astype('u1')

def hist_eq(b):
    bf = b.flatten()
    min_, max_ = nanmin(bf), nanmax(bf)
    cumfreqs, lowlim, binsize, extrapoints = cumfreq(bf, numbins=256, defaultreallimits=(min_, max_))
    cumfreqs = (255.99 * cumfreqs / cumfreqs[-1]).astype('u1')

    result = (255.99*(b-min_)/(max_-min_)).clip(0, 255).astype('u1')
    return cumfreqs[result]

def custom_stretch(b, min_, max_):
    return (255.99*(b-min_)/(max_-min_)).clip(0, 255).astype('u1')

def no_stretch(b):
    return b.clip(0, 255).astype('u1')

# for convenience
fundict = {'NO':no_stretch, 'MM':minmax_stretch, '1P':percent_stretch,
           'SD':stddev_stretch, 'MAD':mad_stretch, 'HEQ':hist_eq}
