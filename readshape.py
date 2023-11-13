#!/usr/bin/python3
## readshape.py
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

import os

import shapelib
import dbflib

from pylab import *
ion()

MAX_OBJECTS = 25000

POINT_TYPES = [shapelib.SHPT_POINT, shapelib.SHPT_POINTZ, shapelib.SHPT_POINTM]
LINE_TYPES = [shapelib.SHPT_ARC, shapelib.SHPT_ARCM, shapelib.SHPT_ARCZ]
POLYGON_TYPES = [shapelib.SHPT_POLYGON, shapelib.SHPT_POLYGONZ, shapelib.SHPT_POLYGONM]

def center_extents(o):
    e = o.extents()
    ((llx, lly, dummy, dummy), (urx, ury, dummy, dummy)) = e
    return ((llx+urx)/2.0), ((lly+ury)/2.0)

def plot_polygons(s, db, label=None):
    count, stype, ll, ur = s.info()

    if not stype in POLYGON_TYPES:
        raise ValueError("Wrong shape type '%s'" % (stype,))

    for i in range(min(count, MAX_OBJECTS)):
        o = s.read_object(i)
        rec = db.read_record(i)

        j = 0
        for v in o.vertices():
            v = list(zip(*v))
            if j==0:
                fill(v[0], v[1], color='g', alpha=0.5)
            else:
                fill(v[0], v[1], color='r', alpha=0.5)

            j = j + 1

        if label:
            c = center_extents(o)
            text(c[0], c[1], rec[label], size=6, ha='center')

def plot_arcs(s, db, label=None):
    count, stype, ll, ur = s.info()

    if not stype in LINE_TYPES:
        raise ValueError("Wrong shape type '%s'" % (stype,))

    for i in range(min(count, MAX_OBJECTS)):
        o = s.read_object(i)
        rec = db.read_record(i)

        if label:
            j = 0
            xs, ys = [], []
            for v in o.vertices():
                v = list(zip(*v))
                x, y = v[0], v[1]
                xs.extend(x)
                ys.extend(y)
                if j==0:
                    plot(x, y, color='b')
                else:
                    plot(x, y, color='r')
                j = j + 1
            text(xs[len(xs)//2], ys[len(ys)//2], rec[label], size=6)
        else:
            j = 0
            for v in o.vertices():
                v = list(zip(*v))
                if j==0:
                    plot(v[0], v[1], color='b', alpha=0.5)
                else:
                    plot(v[0], v[1], color='r', alpha=0.5)
                j = j + 1

def plot_points(s, db, label=None):
    count, stype, ll, ur = s.info()

    if not stype in POINT_TYPES:
        raise ValueError("Wrong shape type '%s'" % (stype,))

    for i in range(min(count, MAX_OBJECTS)):
        o = s.read_object(i)
        rec = db.read_record(i)

        j = 0
        for v in o.vertices():
            if j==0:
                plot([v[0]], [v[1]], color='r', marker='o', mec='k')
            else:
                plot([v[0]], [v[1]], color='r', marker='o', mec='k')

            j = j + 1

        if label:
            text(v[0], v[1], rec[label], size=6, ha='center')

def plot_shapefile(sname, label=None):
    s = shapelib.open(sname)
    db = dbflib.open(sname)

    count, stype, ll, ur = s.info()

    if stype in POINT_TYPES:
        plot_points(s, db, label=label)
    elif stype in LINE_TYPES:
        plot_arcs(s, db, label=label)
    elif stype in POLYGON_TYPES:
        plot_polygons(s, db, label=label)
    elif stype == shapelib.SHPT_MULTIPATCH:
        raise ValueError('Multipatch shapefile not supported')
    elif stype == shapelib.SHPT_NULL:
        raise ValueError('NULL shapefile not supported')
    else:
        raise ValueError("Unknown shapefile type '%d'" % (stype,))

    db.close()
    s.close()

def list_attributes(sname):
    db = dbflib.open(sname)
    result = []
    for i in range(db.field_count()):
        result.append(db.field_info(i)[1])

    db.close()
    return result

def find_shapefiles(d):
    for f in os.listdir(d):
        fullpath = os.path.join(d, f)
        if os.path.isdir(fullpath):
            find_shapefiles(fullpath)
        elif f.endswith('.shp'):
            try:
                s = shapelib.open(fullpath)
            except IOError:
                print('Bad shapefile', fullpath)
                continue
            count, stype, ll, ur = s.info()
            if not stype in [1, 3, 5]:
                print("%s %d\n" % (fullpath, stype))


if __name__ == '__main__':
##    plot_shapefile('/data/Data/Nederland/wijk_2006_gen', 'BU_NAAM')
##
    print(list_attributes('/data/Data/overijssel/overijssel elevation points/ov_elevation_10m'))
    plot_shapefile('/data/Data/overijssel/overijssel elevation points/ov_elevation_10m', 'CONTOUR')
##
##    plot_shapefile('/data/Data/overijssel/overijssel elevation points/ov_elevation')
##
##    find_shapefiles('/data/Data')
        
        
