#!/usr/bin/python3
######################################################################
##
##  geo_correction.py
##
##      Geo correction using latlon
##      OMEGA Geo Correction using geocube
##
##  Created WHB 20100322
##  Modified 20100324 WHB, bug fix geo_points and negative y-axis
##  Modified 20100329 WHB, added general correction using latlon.
##  Modified 20131115 Jelmer Oosthoek, added mapInfo and 
##                                     coordinate_system_string
##  Modified 20180109 WHB, added Azimuthal Equidistant projection
##                      for polar images
##
##
## Copyright (C) 2010-2018 Wim Bakker
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

import string

import envi2
import envi2.resample

import numpy
import scipy.optimize

from pylab import plot, ion, legend, axis, show, draw
ion()

LAT = 'latitude'
LON = 'longitude'
SWIR1 = 'IR C'
SWIR2 = 'IR L'
VNIR = 'VIS'
CENTERTEXT = ' of the center of the '

NODATA = numpy.nan

# for calculating distances on Mars
MARS_RADIUS = 3396190.0  # average Mars radius in km

def haversine(lon1, lat1, lon2, lat2):
    """
    Calculates the great circle distance between two points
    on the Globe (specified in decimal degrees)

    All args must be of equal shape.    
    """

    lon1, lat1, lon2, lat2 = map(numpy.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = numpy.sin(dlat/2.0)**2 + numpy.cos(lat1) * numpy.cos(lat2) * numpy.sin(dlon/2.0)**2

##    c = 2 * numpy.arcsin(numpy.sqrt(a))
    c = 2 * numpy.arctan2(numpy.sqrt(a), numpy.sqrt(1 - a))
##    km = R * c
##    return km * 1000.0
    return numpy.degrees(c)

# Polar coordinates, Azimuthal Equidistant projection
def ll2polar_north(lon, lat):
    r = 90 - lat
    theta = numpy.radians(lon)
    x = r * numpy.sin(theta)
    y = r * numpy.cos(theta)
    return x, y

def polar2ll_north(x, y):
    r = numpy.sqrt(x**2 + y**2)
    theta = numpy.arctan2(y, x)
    lat = 90 - r
    lon = numpy.degrees(theta)
    return lon, lat

def ll2polar_south(lon, lat):
    r = 90 + lat
    theta = numpy.radians(lon)
    x = r * numpy.sin(theta)
    y = r * numpy.cos(theta)
    return x, y

def polar2ll_south(x, y):
    r = numpy.sqrt(x**2 + y**2)
    theta = numpy.arctan2(y, x)
    lat = r - 90
    lon = numpy.degrees(theta)
    return lon, lat

##def geocube_find_band(gc, latlon, channel):
##    for i in range(len(gc.band_names)):
##        if latlon + CENTERTEXT + channel in gc.band_names[i]:
##            return i
##    return -1

def geocube_find_band(gc, latlon, channel):
    for i in range(len(gc.band_names)):
        if latlon in gc.band_names[i] and channel in gc.band_names[i]:
            return i
    return -1

def latlon_find_band(gc, latlon):
    for i in range(len(gc.band_names)):
        if latlon in gc.band_names[i].lower():
            return i
    return -1

def message(s):
    print(s)

def plot_boundaries(lons, lats, col, label=''):
    xs = numpy.concatenate((lons[0, :], lons[-1, :], lons[:, 0], lons[:, -1]))
    ys = numpy.concatenate((lats[0, :], lats[-1, :], lats[:, 0], lats[:, -1]))
    plot(xs, ys, col, markersize=1, label=label)

# This is probably terribly inefficient, but at least has no Python loops...
def find_nearest_pixel(lons, lats, x, y, tol):
    dist = numpy.hypot(lons - x, lats - y)
    dmin = dist.min()
    if dmin <= tol:
        yx = numpy.where(dist == dmin)
        return yx[0][0], yx[1][0]
    else:
        return None

# better version?
def find_nearest_euclid(lons, lats, x, y, tol):
    dist = numpy.hypot(lons - x, lats - y)
    j, i = numpy.unravel_index(numpy.argmin(dist), dist.shape)
    if dist[j, i] <= tol:
        return j, i
    else:
        return None

# use true distance using Haversine
def find_nearest_pixel_true_dist(lons, lats, x, y, tol):
    dist = haversine(lons, lats, x, y)
    j, i = numpy.unravel_index(numpy.argmin(dist), dist.shape)
    if dist[j, i] <= tol:
        return j, i
    else:
        return None

# Use approximate distance using cosine of latitude
def find_nearest_pixel_approx_dist(lons, lats, x, y, tol):
    dist = numpy.hypot(numpy.cos(numpy.radians(y)) * (lons - x), (lats - y))
    j, i = numpy.unravel_index(numpy.argmin(dist), dist.shape)
    if dist[j, i] <= tol:
        return j, i
    else:
        return None

#### work in progress...
##def find_nearest_pixel_split(lons, lats, x, y, tol):
##    c = numpy.cos(numpy.radians(y))
##    
##    j0 = 0
##    dist = numpy.hypot(c * (lons[j0, :] - x), (lats[j0, :] - y))
##    min0 = dist.min()
##
##    j1 = lons.shape[0]-1
##    dist = numpy.hypot(c * (lons[j1, :] - x), (lats[j1, :] - y))
##    min1 = dist.min()
##
##    j = j1
##    while j0 < j:
##        j = (j0 + j1) // 2
##        dist = numpy.hypot(c * (lons[j, :] - x), (lats[j, :] - y))
##        minmid = dist.min()
##        if j0 < j1:
##            j1 = j
##            min1 = minmid
##        else:
##            j0 = j
##            min0 = minmid
##
##    if minmid <= tol:
##        dist = numpy.hypot(c * (lons[j, :] - x), (lats[j, :] - y))
##        i = numpy.unravel_index(numpy.argmin(dist), dist.shape)
##        return j, i
##    else:
##        return None

# local search first function version....
oldi = 0
oldj = 0

def find_nearest_pixel2fast(lons, lats, x, y, tol):
    global oldi, oldj
    lines, samples = lons.shape
    if (5 <= oldi <= samples-6) and (5 <= oldj <= lines-6): # do a local search first
        dist = numpy.hypot(lons[oldj-5:oldj+5, oldi-5:oldi+5] - x, lats[oldj-5:oldj+5, oldi-5:oldi+5] - y)
        jsub, isub = numpy.unravel_index(numpy.argmin(dist), dist.shape)
        if (-5 < isub < 4) and (-5 < jsub < 4) and dist[jsub, isub] <= tol:
            i, j = oldi + isub - 5, oldj + jsub - 5
            oldi, oldj = i, j
##            message("1 oldi, oldj %d, %d" % (oldi, oldj))
            return j, i
        else: # global search
            dist = numpy.hypot(lons - x, lats - y)
            j, i = numpy.unravel_index(numpy.argmin(dist), dist.shape)
            if dist[j, i] <= tol:
                oldi, oldj = i, j
##                message("2 oldi, oldj %d, %d" % (oldi, oldj))
                return j, i
            else:
                return None
    else: # global search
        dist = numpy.hypot(lons - x, lats - y)
        j, i = numpy.unravel_index(numpy.argmin(dist), dist.shape)
        if dist[j, i] <= tol:
            oldi, oldj = i, j
##            message("3 oldi, oldj %d, %d" % (oldi, oldj))
            return j, i
        else:
            return None

def get_value(lons, parm):
    i, j = parm
    ysize, xsize = lons.shape
    if (0 <= i < xsize) and (0 <= j < ysize):
        return lons[int(j), int(i)]
    else:
        return 1000000

def distance(parm, lons, lats, x, y):
    return numpy.hypot(get_value(lons, parm) - x, get_value(lats, parm) - y)

# best version?
def find_nearest_pixel3(lons, lats, x, y, tol):
    res = scipy.optimize.minimize(distance, numpy.array([20, 20]), args=(lons, lats, x, y),method='Nelder-Mead')
    parm = res.x
    if distance(parm, lons, lats, x, y) <= tol:
        i, j = parm
        return int(i), int(j)
    else:
        return None

def omega_geo_correction(fin, fout,
                     geocube=None,
                     polar=False,
                     sort_wavelengths=False, use_bbl=False,
                             message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=False, use_bbl=False)

    if im.bands != 352:
        message("Input image does not have 352 bands!")
        raise ValueError("Input image does not have 352 bands!")

    gc = envi2.Open(geocube)

##  determine 0 degree meridian crossing
    lons_swir1 = gc[geocube_find_band(gc, LON, SWIR1)] / 10000.0
    crosses0 = max(numpy.abs(lons_swir1[:-1, :] - lons_swir1[1:, :]).max(), numpy.abs(lons_swir1[:, :-1] - lons_swir1[:, 1:]).max()) > 180.0

    if crosses0:
        message('Image crosses 0 degree meridian!')

    if polar:
        lats_swir1 = gc[geocube_find_band(gc, LAT, SWIR1)]/10000.0
        northpole = lats_swir1.mean() > 0
        if northpole:
            message('Using Polar Projection North')
        else:
            message('Using Polar Projection South')

##    message('SWIR1')
    lons_swir1 = (gc[geocube_find_band(gc, LON, SWIR1)]/10000.0 + crosses0 * 180.0) % 360.0 - crosses0 * 180.0
    lats_swir1 = gc[geocube_find_band(gc, LAT, SWIR1)]/10000.0

    if polar:
        if northpole:
            lons_swir1, lats_swir1 = ll2polar_north(lons_swir1, lats_swir1)
        else:
            lons_swir1, lats_swir1 = ll2polar_south(lons_swir1, lats_swir1)

    xmin = lons_swir1.min()
    xmax = lons_swir1.max()
    ymin = lats_swir1.min()
    ymax = lats_swir1.max()

    plot_boundaries(lons_swir1, lats_swir1, 'r.', label='swir 1')

##    message('SWIR2')
    lons_swir2 = (gc[geocube_find_band(gc, LON, SWIR2)]/10000.0 + crosses0 * 180.0) % 360.0 - crosses0 * 180.0
    lats_swir2 = gc[geocube_find_band(gc, LAT, SWIR2)]/10000.0

    if polar:
        if northpole:
            lons_swir2, lats_swir2 = ll2polar_north(lons_swir2, lats_swir2)
        else:
            lons_swir2, lats_swir2 = ll2polar_south(lons_swir2, lats_swir2)

    xmin = min(xmin, lons_swir2.min())
    xmax = max(xmax, lons_swir2.max())
    ymin = min(ymin, lats_swir2.min())
    ymax = max(ymax, lats_swir2.max())

    plot_boundaries(lons_swir2, lats_swir2, 'g.', label='swir 2')

##    message('VNIR')
    lons_vnir = (gc[geocube_find_band(gc, LON, VNIR)]/10000.0  + crosses0 * 180.0) % 360.0 - crosses0 * 180.0
    lats_vnir = gc[geocube_find_band(gc, LAT, VNIR)]/10000.0

    if polar:
        if northpole:
            lons_vnir, lats_vnir = ll2polar_north(lons_vnir, lats_vnir)
        else:
            lons_vnir, lats_vnir = ll2polar_south(lons_vnir, lats_vnir)

    xmin = min(xmin, lons_vnir.min())
    xmax = max(xmax, lons_vnir.max())
    ymin = min(ymin, lats_vnir.min())
    ymax = max(ymax, lats_vnir.max())

    plot_boundaries(lons_vnir, lats_vnir, 'b.', label='vnir')
    legend()
    axis('equal')
    draw()

##  try to determine a sensible sampling for this image...

    lons = (gc[geocube_find_band(gc, LON, VNIR)]/10000.0  + crosses0 * 180.0) % 360.0 - crosses0 * 180.0
    lats = gc[geocube_find_band(gc, LAT, VNIR)]/10000.0

    disty = haversine(lons[:-1, :], lats[:-1, :], lons[1:, :], lats[1:, :])
    distx = haversine(lons[:, :-1], lats[:, :-1], lons[:, 1:], lats[:, 1:])

    message("disty (min, mean, max): %f %f %f" % (disty.min(), disty.mean(), disty.max()))
    message("distx (min, mean, max): %f %f %f" % (distx.min(), distx.mean(), distx.max()))

    dmin = min(disty.min(), distx.min())
    dmax = max(disty.max(), distx.max())
    dmean = (disty.mean() + distx.mean()) / 2.0

    # this is the sampling distance we will use
    delta = dmin

    # tolerance for distance, pixels outside this tolerance get no value
    tol = 1.05 * dmax

    message('Bounding box: ' + str([xmin, xmax, ymin, ymax]))
    message('Delta: ' + str(delta))
    message('Mean sampling distance (m): %f' % (numpy.radians(dmean) * MARS_RADIUS,))
    message('Tolerance: ' + str(tol))

    samples = int((xmax - xmin) // delta) + 1
    lines = int((ymax - ymin) // delta) + 1

    message('samples, lines: ' + str((samples, lines)))

    # set up geo_points for pseudo-geographic coordinates
    # UL, UR, LL, LR
    geo_points = []
    i, j = 0, 0
    x, y = xmin + i * delta, ymax - j * delta
    # NOTE: order x, y, LAT, LON !!!
    geo_points.extend([i + 1.5, j + 1.5, y, x])
    i, j = samples-1, 0
    x, y = xmin + i * delta, ymax - j * delta 
    geo_points.extend([i + 1.5, j + 1.5, y, x])
    i, j = 0, lines-1
    x, y = xmin + i * delta, ymax - j * delta 
    geo_points.extend([i + 1.5, j + 1.5, y, x])
    i, j = samples-1, lines-1
    x, y = xmin + i * delta, ymax - j * delta 
    geo_points.extend([i + 1.5, j + 1.5, y, x])

    # set up map_info and projection system allowing data to be opened in ArcGIS

##/usr/local/exelis/idl85/resource/pedata/predefined/EnviPEGeogcsStrings.txt
##104905 GEOGCS["GCS_Mars_2000",DATUM["D_Mars_2000",SPHEROID["Mars_2000_IAU_IAG",3396190.0,169.8944472236118]],PRIMEM["Reference_Meridian",0.0],UNIT["Degree",0.0174532925199433]]

    # The following is for Geographic, Plate Carree coordinates
    degpixx = (geo_points[15] - geo_points[3]) / (geo_points[4] - geo_points[0])
    degpixy = abs((geo_points[14] - geo_points[2]) / (geo_points[13] - geo_points[1]))

    map_info = ["Geographic Lat/Lon",geo_points[1],geo_points[0],geo_points[3],geo_points[2],degpixx,degpixy,"units=Degrees"]
    
    coordinate_system_string = ['GEOGCS["GCS_Mars_2000_Sphere",DATUM["D_Mars_2000_sphere",SPHEROID["Mars_2000_Sphere",3396190.0,0.0]],PRIMEM["Reference_Meridian",0.0],UNIT["Degree",0.0174532925199433]]']
    
    # set up map_info and projection for polar projection
    if polar:
        sampling_distance = numpy.radians(delta) * MARS_RADIUS
        ulx = numpy.radians(xmin) * MARS_RADIUS
        uly = numpy.radians(ymax) * MARS_RADIUS
        map_info = ["Azimuthal Equidistant", 1, 1, ulx, uly, sampling_distance, sampling_distance, "units=Meters"]
        if northpole:
            coordinate_system_string = ["""PROJCS["Mars_North_Pole_Azimuthal_Equidistant",
GEOGCS["GCS_Mars_2000_Sphere",
    DATUM["D_Mars_2000_Sphere",
        SPHEROID["Mars_2000_Sphere",3396190.0,0.0]],
    PRIMEM["Reference_Meridian",0.0],
    UNIT["Degree",0.0174532925199433]],
PROJECTION["Azimuthal_Equidistant"],
PARAMETER["False_Easting",0],
PARAMETER["False_Northing",0],
PARAMETER["Central_Meridian",0],
PARAMETER["Latitude_Of_Origin",90],
UNIT["Meter",1]]"""]
        else:
            coordinate_system_string = ["""PROJCS["Mars_South_Pole_Azimuthal_Equidistant",
GEOGCS["GCS_Mars_2000_Sphere",
    DATUM["D_Mars_2000_Sphere",
        SPHEROID["Mars_2000_Sphere",3396190.0,0.0]],
    PRIMEM["Reference_Meridian",0.0],
    UNIT["Degree",0.0174532925199433]],
PROJECTION["Azimuthal_Equidistant"],
PARAMETER["False_Easting",0],
PARAMETER["False_Northing",0],
PARAMETER["Central_Meridian",0],
PARAMETER["Latitude_Of_Origin",-90],
UNIT["Meter",1]]"""]

        im2 = envi2.New(fout, hdr=im, samples=samples, lines=lines,
                        map_info=map_info, 
                        coordinate_system_string=coordinate_system_string)
    else:
        im2 = envi2.New(fout, hdr=im, samples=samples, lines=lines,
                        geo_points=geo_points, map_info=map_info, 
                        coordinate_system_string=coordinate_system_string)

    # Calculate output
    if progress:
        progress(0.0)

    for j in range(im2.lines):
        if progress:
            progress(j / float(im2.lines))

        y = ymax - j * delta
        for i in range(im2.samples):
            x = xmin + i * delta
            # SWIR1
            if polar:
                jjii = find_nearest_euclid(lons_swir1, lats_swir1, x, y, tol)
            else:
                jjii = find_nearest_pixel_approx_dist(lons_swir1, lats_swir1, x, y, tol)
            if jjii:
                jj, ii = jjii
                im2[j, i, 0:128] = im[jj, ii, 0:128]
            else:
                im2[j, i, 0:128] = NODATA
            # SWIR2
            if polar:
                jjii = find_nearest_euclid(lons_swir2, lats_swir2, x, y, tol)
            else:
                jjii = find_nearest_pixel_approx_dist(lons_swir2, lats_swir2, x, y, tol)
            if jjii:
                jj, ii = jjii
                im2[j, i, 128:256] = im[jj, ii, 128:256]
            else:
                im2[j, i, 128:256] = NODATA
            # VNIR
            if polar:
                jjii = find_nearest_euclid(lons_vnir, lats_vnir, x, y, tol)
            else:
                jjii = find_nearest_pixel_approx_dist(lons_vnir, lats_vnir, x, y, tol)
            if jjii:
                jj, ii = jjii
                im2[j, i, 256:352] = im[jj, ii, 256:352]
            else:
                im2[j, i, 256:352] = NODATA

    del im, im2

def latlon_geo_correction(fin, fout,
                     geocube=None,
                     sort_wavelengths=False, use_bbl=False,
                             message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    gc = envi2.Open(geocube)

    lons = gc[latlon_find_band(gc, LON)]
    lats = gc[latlon_find_band(gc, LAT)]

    xmin = lons.min()
    xmax = lons.max()
    ymin = lats.min()
    ymax = lats.max()

    plot_boundaries(lons, lats, 'b.', label='footprint')
    legend()
    axis('equal')
    draw()

    diff = numpy.abs(lons[:, -1] - lons[:, 0])
    dxmin = diff.min() / gc.samples
    dxmax = diff.max() / gc.samples

    diff = numpy.abs(lats[-1, :] - lats[0, :])
    dymin = diff.min() / gc.lines
    dymax = diff.max() / gc.lines

    delta = min(dxmin, dymin)
    tol = 1.05 * numpy.hypot(dxmax, dymax) / 2.0

    message('Bounding box: ' + str([xmin, xmax, ymin, ymax]))
    message('Delta: ' + str(delta))
    message('Tolerance: ' + str(tol))

    samples = int((xmax - xmin) // delta) + 1
    lines = int((ymax - ymin) // delta) + 1

    # set up geo_points for pseudo-geographic coordinates
    # UL, UR, LL, LR
    geo_points = []
    i, j = 0, 0
    x, y = xmin + i * delta, ymax - j * delta
    # NOTE: order x, y, LAT, LON !!!
    geo_points.extend([i + 1.5, j + 1.5, y, x])
    i, j = samples-1, 0
    x, y = xmin + i * delta, ymax - j * delta 
    geo_points.extend([i + 1.5, j + 1.5, y, x])
    i, j = 0, lines-1
    x, y = xmin + i * delta, ymax - j * delta 
    geo_points.extend([i + 1.5, j + 1.5, y, x])
    i, j = samples-1, lines-1
    x, y = xmin + i * delta, ymax - j * delta 
    geo_points.extend([i + 1.5, j + 1.5, y, x])
    
    # set up map_info allowing data to be opened in ArcGIS
    degpixx = (geo_points[15] - geo_points[3]) / (geo_points[4] - geo_points[0])
    degpixy = abs((geo_points[14] - geo_points[2]) / (geo_points[13] - geo_points[1]))
    map_info = ["Geographic Lat/Lon",geo_points[1],geo_points[0],geo_points[3],geo_points[2],degpixx,degpixy,"units=Degrees"]

    coordinate_system_string = 'GEOGCS["GCS_Mars_2000_Sphere",DATUM["D_Mars_2000_sphere",SPHEROID["Mars_2000_Sphere",3396190.0,0.0]],PRIMEM["Reference_Meridian",0.0],UNIT["Degree",0.0174532925199433]]'
    
    message('samples, lines: ' + str((samples, lines)))

    # create output
    im2 = envi2.New(fout, hdr=im, samples=samples, lines=lines,
                    geo_points=geo_points, map_info=map_info, 
                    coordinate_system_string=coordinate_system_string)

    if progress:
        progress(0.0)
    for j in range(im2.lines):
        if progress:
            progress(j / float(im2.lines))
        y = ymax - j * delta
        for i in range(im2.samples):
            x = xmin + i * delta
            jjii = find_nearest_pixel_approx_dist(lons, lats, x, y, tol)
            if jjii:
                jj, ii = jjii
                im2[j, i] = im[jj, ii]
            else:
                im2[j, i] = NODATA

    if progress:
        progress(1.0)

    del im, im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='geo_correction.py',
        description="""Geocorrection using latlon or geocube file.
OMEGA files should have 352 bands in the original order.""")

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-p', action='store_true', dest='plot',
                      help='plot geographic extent')
    parser.add_argument('-g', dest='geocube', help='input latlon or geocube file name', required=True)
    parser.add_argument('-m', dest='mode', choices=['latlon', 'omega'], default='latlon',
                      help='mode: latlon (use latitude/longitude file, default), omega (use geocube)')
    parser.add_argument('-a', action='store_true', dest='polar',
                      help='Use polar Azimuthal Equidistant projection (default false)')


    options = parser.parse_args()

    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.mode=='latlon':
        latlon_geo_correction(options.input, options.output,
                              geocube=options.geocube,
                              sort_wavelengths=options.sort_wavelengths,
                              use_bbl=options.use_bbl)
    else:
        omega_geo_correction(options.input, options.output,
                             geocube=options.geocube,
                             polar=options.polar,
                             sort_wavelengths=options.sort_wavelengths,
                             use_bbl=options.use_bbl)

    if options.plot:
        show()
