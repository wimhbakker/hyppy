#!/usr/bin/python3
## quickhull2d.py
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

link = lambda a,b: numpy.concatenate((a,b[1:]))
edge = lambda a,b: numpy.concatenate(([a],[b]))

def qhull(sample):
    def dome(sample,base): 
        h, t = base
        dists = numpy.dot(sample-h, numpy.dot(((0,-1),(1,0)),(t-h)))
        outer = numpy.repeat(sample, dists>0, axis=0)
        
        if len(outer):
            pivot = sample[numpy.argmax(dists)]
            return link(dome(outer, edge(h, pivot)),
                        dome(outer, edge(pivot, t)))
        else:
            return base

    if len(sample) > 2:
        axis = sample[:,0]
        base = numpy.take(sample, [numpy.argmin(axis), numpy.argmax(axis)], axis=0)
        return link(dome(sample, base),
                    dome(sample, base[::-1]))
    else:
        return sample

def qhulltop(sample):
    def dome(sample,base): 
        h, t = base
        dists = numpy.dot(sample-h, numpy.dot(((0,-1),(1,0)),(t-h)))
        outer = numpy.repeat(sample, dists>0, axis=0)
        
        if len(outer):
            pivot = sample[numpy.argmax(dists)]
            return link(dome(outer, edge(h, pivot)),
                        dome(outer, edge(pivot, t)))
        else:
            return base

    if len(sample) > 2:
        axis = sample[:,0]
        base = numpy.take(sample, [numpy.argmin(axis), numpy.argmax(axis)], axis=0)
        return dome(sample, base)
    else:
        return sample

def resample(hull, sample):
    xs = sample[:, 0].copy()
    xs.sort()
    ys = numpy.zeros(xs.shape)
    xhull = hull[:, 0]
    yhull = hull[:, 1]
    for i in range(len(xs)):
        i_hull = xhull.searchsorted(xs[i])
        if i_hull == 0:
            ys[i] = yhull[0]
        elif i_hull == len(hull):
            ys[i] = yhull[-1]
        elif xs[i] == xhull[i_hull]:
            ys[i] = yhull[i_hull]
        else:
            i_left = i_hull - 1
            i_right = i_hull
            ys[i] = (xs[i] - xhull[i_left]) / (xhull[i_right] - xhull[i_left]) * (yhull[i_right] - yhull[i_left]) + yhull[i_left]

    return numpy.vstack((xs, ys)).T

def hull_resampled(sample):
    return resample(qhulltop(sample), sample)


# MAIN
if __name__ == "__main__":
    from pylab import plot

    clf()
    
    sample = 100*numpy.random.random((32,2))
    hull = qhulltop(sample)
     
    for s in sample:
        plot([s[0]], [s[1]], 'b.')

    i = 0
    while i < len(hull)-1:
        plot([hull[i][0], hull[i+1][0]], [hull[i][1], hull[i+1][1]], color='k')
        i = i + 1

    #plot([hull[-1][0], hull[0][0]], [hull[-1][1], hull[0][1]], color='k')
    
    rhull = resample(hull, sample)

    for x, y in rhull:
        plot([x], [y], 'ro')
