#!/usr/bin/python3
## segmentation.py
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
#import random
import os

import envi2
from envi2.constants import *

import edgy
from quadtree import *
from clusters import *

# some default split & merge levels
SPLIT_LEVEL = 0.04
MERGE_LEVEL = 0.035

def isRough(a, t):
    x0, x1, y0, y1 = t
    return a[y0:y1,x0:x1].any()

def lowThreshold_av(im, t, merge_level, vert=False):
        x0, x1, y0, y1 = t
        sa, n = 0, 0
        if vert:
            for i in range(x0, x1):
                sa = sa + im.distance_measure((i, y0-1), (i, y0))
                n = n+1
        else:
            for j in range(y0, y1):
                sa = sa + im.distance_measure((x0-1, j), (x0, j))
                n = n+1
        return (sa / n) <= merge_level

def lowThreshold_max(im, t, merge_level, vert=False):
        x0, x1, y0, y1 = t
        maxsa = 0
        if vert:
            for i in range(x0, x1):
                maxsa = max(maxsa, im.distance_measure((i, y0-1), (i, y0)))
        else:
            for j in range(y0, y1):
                maxsa = max(maxsa, im.distance_measure((x0-1, j), (x0, j)))
        return maxsa <= merge_level

def lowThreshold(im, t, merge_level, vert=False):
        x0, x1, y0, y1 = t
        maxsa = 0
        if vert:
            for i in range(x0, x1):
                maxsa = max(maxsa, im.distance_measure((i, y0-1), (i, y0)))
        else:
            for j in range(y0, y1):
                maxsa = max(maxsa, im.distance_measure((x0-1, j), (x0, j)))
        return maxsa <= merge_level

def pepper_salt8(ima, imb):
    a, b = ima.data, imb.data
    for j in range(1, ima.lines-1):
        for i in range(1, ima.samples-1):
            v = a[j-1:j+2, i-1:i+2].reshape(9)
            if v[0] and v[1] and v[2] and v[3] and not v[4] and v[5] and v[6] and v[7] and v[8]:
                b[j, i] = 1
            elif not v[0] and not v[1] and not v[2] and not v[3] and v[4] and not v[5] and not v[6] and not v[7] and not v[8]:
                b[j, i] = 0
            else:
                b[j, i] = a[j, i]

def pepper_salt4(ima, imb):
    a, b = ima.data, imb.data
    for j in range(1, ima.lines-1):
        for i in range(1, ima.samples-1):
            v = a[j-1:j+2, i-1:i+2].reshape(9)
            if v[1] and v[3] and not v[4] and v[5] and v[7]:
                b[j, i] = 1
            elif not v[1] and not v[3] and v[4] and not v[5] and not v[7]:
                b[j, i] = 0
            else:
                b[j, i] = a[j, i]

def message(s):
    pass

def segmentation(edgemap, infile,
                 filethres=None,
                 filesalt=None,
                 filequad=None,
                 fileclust=None,
                 sort_wavelengths=False, use_bbl=True,
                 split_level=SPLIT_LEVEL, merge_level=MERGE_LEVEL,
                 distance_measure='SAM',
                 message=message):
    # The original spectrum
    specfile = infile

    # The edge filtered file
##    fileedgy = infile + '_edgy'
    fileedgy = edgemap

    # Thresholded file
    if not filethres:
        filethres = infile + '_thres'

    # Pepper & Salt filtered file
    if not filesalt:
        filesalt = infile + '_salt'

    # The quads
    if not filequad:
        filequad = infile + '_quad'

    # The clusters
    if not fileclust:
        fileclust = infile + '_clust'

    # test to see if we need to create the Edgy file
##    if not os.path.exists(fileedgy):
##        message("Running Edgy...")
##        message("Input: %s" % (specfile,))
##        message("Output: %s" % (fileedgy,))
##        edgy.edgy(specfile, fileedgy, mode='SAM', sort_wavelengths=sort_wavelengths,
##                  use_bbl=use_bbl, message=message)

    message("Starting SPLIT Phase.")
    message("Split level is %f" % (split_level,))

    im = envi2.Open(fileedgy, as_type='d')
    if im.bands > 1:
        message("Edge Map should have one band only!")
        raise ValueError("Edge Map has more than one band")

    # THRESHOLD
    message("Output: %s" % (filethres,))
    im2 = envi2.New(filethres, hdr=im, data_type='u1', band_names=['threshold'])

    message("Threshold...")
    im2[...] = (im[...] > split_level).astype('u1')
    im2.flush()

    del im

    # PEPPER & SALT FILTER
    message("Output: %s" % (filesalt,))
    im3 = envi2.New(filesalt, hdr=im2, data_type='u1', band_names=['pepper & salt filtered'])

    message("Pepper & Salt...")
    pepper_salt4(im2, im3)
    im3.flush()

    del im2

    # BUILD QUADTREE
    q = QuadTree(0, im3.samples, 0, im3.lines)
    q.split_node(isRough, im3.data)

    message("Number of Quads: %d" % (q.count_leafs(),))
    message("Output: %s" % (filequad,))
    
    im4 = envi2.New(filequad, hdr=im3,
                    file_type=ENVI_Classification,
                    classes=256,
                    class_lookup=(numpy.random.random(3*256)*256).astype('i'),
                    bands=1, band_names=['quads'],
                    data_type='u1') # or 'i' depending on attrib

    q.dump_leafs(im4.data, attrib='random')

    del im3

    # MERGE PHASE
    message("Starting MERGE Phase.")
    message("Merge level is %f" % (merge_level,))

    message("Building linear_list...")

    dlist={}
    q.linear_list(d=dlist)

    message("%d elements" % len(dlist))

    message("Building adjacency_list...")

    q.adjacency_list2(dlist, message=message)

    message("Opening spectral image...")
    message("Input: %s" % (specfile,))

    sim = envi2.Open(specfile, as_type='d', sort_wavelengths=sort_wavelengths,
                     use_bbl=use_bbl)

    # set the distance function to use on this image
    if distance_measure=='SAM':
        sim.distance_measure = sim.spectral_angle
    elif distance_measure=='BC':
        sim.distance_measure = sim.bray_curtis_distance
    elif distance_measure=='SID':
        sim.distance_measure = sim.spectral_information_divergence
    elif distance_measure=='ED':
        sim.distance_measure = sim.euclidean_distance
    elif distance_measure=='ID':
        sim.distance_measure = sim.intensity_difference
    else:
        raise ValueError("Unknown distance measure '%s'" % (distance_measure,))

    message("Start clustering...")

    clust = clusters()

    clust.do_cluster(q, dlist, lowThreshold_max, merge_level, sim)

    message("Dumping clusters...")
    message("Output: %s" % (fileclust,))

    cim = envi2.New(fileclust, hdr=im4,
                    file_type=ENVI_Classification,
                    classes=256,
                    class_lookup=(numpy.random.random(3*256)*256).astype('i'),
                    bands=1, band_names=['clusters'],
                    data_type='u1') # or 'i' depending on attrib

    q.dump_leafs(cim.data, attrib='randclust')

    del im4, sim, cim

if __name__ == '__main__':
    print('Run this module using tkSegmentation.py')
