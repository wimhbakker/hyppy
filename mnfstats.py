#!/usr/bin/python3
## mnfstats.py
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
import numpy

##direct = r'D:\Data\Mars\data\test\Planetary geology course\MEX-M-OMEGA-2-EDR-FLIGHT-V1.0\DATA\ORB04'
##fin = 'ORB0422_4_jdat_rat1_mnfstats.txt'
##
##fname = direct + '\\' + fin

statlist = ['Covariance', 'Correlation', 'Eigenvector']

def find_text(data, s):
    i = 0
    while not s in data[i]:
        i += 1
    return i

def text2array(data, s):
    start = find_text(data, s)

    line = start
    l = data[line].strip()
    elems = l.split()
    try:
        n = int(elems[-1])
    except ValueError:
        return None

    a = numpy.zeros((n, n))
    line += 1
    l = data[line].strip()
    j = 0
    while l:
        elems = l.split()[2:]
        i = 0
        for e in elems:
            try:
                a[j, i] = e
            except ValueError:
                a[j, i] = numpy.nan
            i += 1
        line += 1
        try:
            l = data[line].strip()
        except IndexError:
            l = None
        j += 1
    return a

def message(s):
    print(s)

def mnfstats(fname, fout, message=message):
    f = open(fname)

    data = f.readlines()

    f.close()

    nstats = len(statlist)
    a = nstats * [None]
    for i in range(nstats):
        message('Reading %s...' % statlist[i])
        a[i] = text2array(data, statlist[i])
        if a[i]!=None:
            lines, samples = a[i].shape
        else:
            message('Failed to read %s!' % (statlist[i],))

    message('Creating image %s' % (fout,))
    imout = envi2.New(fout,
                          hdr=envi2.Header(samples=samples, lines=lines, bands=3),
                          interleave='bsq', band_names=statlist,
                          data_type='d')

    for i in range(nstats):
        if a[i]!=None:
            message('Writing %s...' % (statlist[i],))
            imout[:,:,i] = a[i][:,:]

    del imout

#mnfstats(fname)


