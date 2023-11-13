#!/usr/bin/python3
## tokml.py
##
## Copyright (C) 2010 Wim Bakker
##     Modified 20221107 WHB, added support for map_info
##              Supported are: utm wgs84, utm ed50 and geographic wgs84
##              Does a datum transform from utm ed50 to utm wgs84
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
import envi2
import envi2.constants

# Try to import from Pillow or PIL
try:
    from PIL import Image
except ImportError as errtext:
    import Image

import numpy

import stretch

TARGET_MARS = "mars"
TARGET_EARTH = "earth"
TARGET_MOON = "moon"
TARGET_SKY = "sky"

TARGETS = (TARGET_EARTH, TARGET_MOON, TARGET_MARS, TARGET_SKY)


def message(s):
    print(s)


def get_bounding_box(im):
    """Bounding box. Returns (north, west, south, east)"""
    try:
        return (
            im.header.geo_points[2],
            im.header.geo_points[3],
            im.header.geo_points[14],
            im.header.geo_points[15],
        )
    except AttributeError:
        pass

    try:
        if im.header.map_info[0] in ("Arbitrary", "Geographic Lat/Lon", "UTM"):
            x, y, resx, resy = im.header.map_info[3:7]
            return (y, x, y - resy * im.lines, x + resx * im.samples)
    except AttributeError:
        pass

    return None


def create_worldfile(worldfile, im):
    North, West, South, East = get_bounding_box(im)

    # figure out pixel size of this image
    xpixsize = (East - West) / (im.samples - 1)
    ypixsize = -(North - South) / (im.lines - 1)

    # save world file
    f = open(worldfile, "w")
    f.write("%.10f\n" % (xpixsize,))
    f.write("%f\n" % (0.0,))
    f.write("%f\n" % (0.0,))
    f.write("%.10f\n" % (ypixsize,))
    f.write("%.10f\n" % (West,))
    f.write("%.10f\n" % (North,))
    f.close()


def create_kml(fbase, im, target=TARGET_MARS):
    kmlname = fbase + ".kml"
    name = os.path.basename(fbase)

    north, west, south, east = get_bounding_box(im)

    f = open(kmlname, "w")

    f.write(
        """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" hint="target=%s">
  <GroundOverlay>
    <name>%s</name>
    <Icon>
      <href>%s</href>
    </Icon>
    <LatLonBox>
      <north>%f</north>
      <south>%f</south>
      <east>%f</east>
      <west>%f</west>
      <rotation>0.0</rotation>
    </LatLonBox>
  </GroundOverlay>
</kml>
"""
        % (target, name, name + ".png", north, south, east, west)
    )
    # """ % (target, name, fbase + '.png', north, south, east, west)) # absolute path

    f.close()


def create_kml_quad_from_map_info_utm(fbase, png, im, target=TARGET_MARS):
    import pyproj

    kmlname = fbase + ".kml"
    name = os.path.basename(fbase)

    # upper left corner
    if len(im.header.map_info) == 11:
        proj, x0, y0, X0, Y0, Xdelta, Ydelta, zone, hemisphere, ellps, units = (
            im.header.map_info
        )
    elif len(im.header.map_info) == 10:
        proj, x0, y0, X0, Y0, Xdelta, Ydelta, zone, hemisphere, units = (
            im.header.map_info
        )
        ellps = "WGS84"  # cross fingers here...
    else:
        message("Unsupported map info size from ENVI header")
        return

    if "WGS" in ellps:
        ellps = "WGS84"
        if hemisphere.lower() == "north":
            p = pyproj.Proj(proj="utm", zone=zone, north=True, ellps=ellps, units="m")
        else:
            p = pyproj.Proj(proj="utm", zone=zone, south=True, ellps=ellps, units="m")
    elif "European 1950" in ellps:
        ellps = "intl"
        p = pyproj.Proj("EPSG:23030")
    else:
        message("Unsupported ellipse %s" % (ellps,))

    pgoal = pyproj.Proj("EPSG:4326")

    # lower left
    X1, Y1 = X0 + Xdelta, Y0 - im.lines * Ydelta

    # lower right
    X2, Y2 = X0 + im.samples * Xdelta, Y0 - im.lines * Ydelta

    # upper right
    X3, Y3 = X0 + im.samples * Xdelta, Y0

    ##    # inverse projection from UTM to geographic
    ##    lon0, lat0 = p(X0, Y0, inverse=True)
    ##    lon1, lat1 = p(X1, Y1, inverse=True)
    ##    lon2, lat2 = p(X2, Y2, inverse=True)
    ##    lon3, lat3 = p(X3, Y3, inverse=True)

    # inverse projection from UTM x, y to geographic lat, lon
    lat0, lon0 = pyproj.transform(p, pgoal, X0, Y0)
    lat1, lon1 = pyproj.transform(p, pgoal, X1, Y1)
    lat2, lon2 = pyproj.transform(p, pgoal, X2, Y2)
    lat3, lon3 = pyproj.transform(p, pgoal, X3, Y3)

    write_kml_quad(
        kmlname, target, name, png, lon1, lat1, lon2, lat2, lon3, lat3, lon0, lat0
    )


def create_kml_quad_from_map_info_geographic(fbase, png, im, target=TARGET_MARS):
    kmlname = fbase + ".kml"
    name = os.path.basename(fbase)

    # upper left corner
    proj, x0, y0, X0, Y0, Xdelta, Ydelta, ellps, units = im.header.map_info

    if "WGS" in ellps:
        ellps = "WGS84"
    elif "European 1950" in ellps:
        ellps = "intl"
    else:
        message("Unsupported ellipse %s" % (ellps,))

    # lower left
    X1, Y1 = X0 + Xdelta, Y0 - im.lines * Ydelta

    # lower right
    X2, Y2 = X0 + im.samples * Xdelta, Y0 - im.lines * Ydelta

    # upper right
    X3, Y3 = X0 + im.samples * Xdelta, Y0

    write_kml_quad(kmlname, target, name, png, X1, Y1, X2, Y2, X3, Y3, X0, Y0)


def create_kml_quad_from_geo_points(fbase, png, im, target=TARGET_MARS):
    kmlname = fbase + ".kml"
    name = os.path.basename(fbase)

    # get corners
    _, _, lat0, lon0, _, _, lat3, lon3, _, _, lat1, lon1, _, _, lat2, lon2 = (
        im.header.geo_points
    )

    write_kml_quad(
        kmlname, target, name, png, lon1, lat1, lon2, lat2, lon3, lat3, lon0, lat0
    )


def write_kml_quad(
    kmlname, target, name, png, lon1, lat1, lon2, lat2, lon3, lat3, lon0, lat0
):
    with open(kmlname, "w") as f:
        # LatLonQuad: ll, lr, ur, ul
        f.write(
            """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" hint="target=%s">
  <GroundOverlay>
    <name>%s</name>
    <Icon>
      <href>%s</href>
    </Icon>
    <gx:LatLonQuad>
      <coordinates> %f,%f %f,%f %f,%f %f,%f </coordinates>
    </gx:LatLonQuad>
  </GroundOverlay>
</kml>
"""
            % (target, name, png, lon1, lat1, lon2, lat2, lon3, lat3, lon0, lat0)
        )
        # """ % (target, name, fbase + '.png', north, south, east, west)) # absolute path


# convert ENVI clissified image to PIL image...
def class2image(imclass):
    # the .copy() is a workaround for the PIL tobytes/tostring bug in v1.1.7
    im = Image.fromarray(imclass[...].copy())
    palette = imclass.header.class_lookup
    palette = palette + (3 * 256 - len(palette)) * [0]
    im.putpalette(palette)
    return im


def tokml(
    fin,
    red=None,
    green=None,
    blue=None,
    stretch_mode=None,
    strip_edges=False,
    strip_zeros=False,
    sort_wavelengths=False,
    use_bbl=False,
    target=TARGET_MARS,
    message=message,
    force=False,
    fbase=None,
):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if not fbase:
        fbase = os.path.splitext(fin)[0]

    if im.header.file_type == envi2.constants.ENVI_Classification:
        rgba = class2image(im)
    else:
        # Stretch, this could be a dict...
        if stretch_mode == "NO":
            stretch_fun = stretch.no_stretch
        elif stretch_mode == "MM":
            stretch_fun = stretch.minmax_stretch
        elif stretch_mode == "1P":
            stretch_fun = stretch.percent_stretch
        elif stretch_mode == "SD":
            stretch_fun = stretch.stddev_stretch
        else:
            raise ValueError

        if hasattr(im, "wavelength"):
            i = im.wavelength2index(red)
        else:
            i = int(red)
        message("Red band=%d" % (i,))

        r = im.get_band(i).astype("float64")
        ar = numpy.isnan(r)

        if hasattr(im, "wavelength"):
            i = im.wavelength2index(green)
        else:
            i = int(green)
        message("Green band=%d" % (i,))

        g = im.get_band(i).astype("float64")
        ag = numpy.isnan(g)

        if hasattr(im, "wavelength"):
            i = im.wavelength2index(blue)
        else:
            i = int(blue)
        message("Blue band=%d" % (i,))

        b = im.get_band(i).astype("float64")
        ab = numpy.isnan(b)

        r = stretch_fun(r)
        g = stretch_fun(g)
        b = stretch_fun(b)

        if strip_edges:
            alpha_raw = ((~(ar | ag | ab)) * 255).astype("u1")
        else:
            alpha_raw = ((~(ar & ag & ab)) * 255).astype("u1")

        if strip_zeros:
            alpha_raw = (
                (
                    alpha_raw.astype(bool)
                    & (r.astype(bool) | g.astype(bool) | b.astype(bool))
                )
                * 255
            ).astype("u1")

        r = Image.fromarray(r)
        g = Image.fromarray(g)
        b = Image.fromarray(b)
        alpha = Image.fromarray(alpha_raw)

        rgba = Image.merge("RGBA", (r, g, b, alpha))

    ##    rgb.save(fbase + '.jpg', 'JPEG', quality=100)
    png = fbase + ".png"
    pgw = fbase + ".pgw"

    if force or not os.path.exists(png):
        message("Creating PNG image")
        rgba.save(png, "PNG")
    else:
        message("PNG image exists. Skipped.")

    try:
        if hasattr(im.header, "geo_points"):
            create_kml_quad_from_geo_points(fbase, png, im, target=target)
            message("KML file created from geo points")

        if hasattr(im.header, "map_info"):
            proj = im.header.map_info[0].lower()
            if "utm" in proj:
                create_kml_quad_from_map_info_utm(
                    fbase + "_map_info", png, im, target=target
                )
                message("KML file created from map info (utm)")
            elif "geographic" in proj:
                create_kml_quad_from_map_info_geographic(
                    fbase + "_map_info", png, im, target=target
                )
                message("KML file created from map info (geographic)")

    except:
        message("Skipping KML file.")

    try:
        if force or not os.path.exists(pgw):
            create_worldfile(pgw, im)
            message("World file created")
        else:
            message("PGW exists. Skipped.")
    except:
        message("Skipping World File.")

    del im


if __name__ == "__main__":
    ##    print "Run this module using tkToKML!"
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(
        prog="tokml.py",
        ##        usage='tokml.py -f -s -b -e -z -i input -R red -G green -B blue -m {NO|MM|1P|SD} -t target',
        description="Convert data to .png, .pgw and .kml in one go",
    )

    parser.add_argument(
        "-f", action="store_true", dest="force", help="force overwrite of output files"
    )
    parser.add_argument(
        "-s",
        action="store_true",
        dest="sort_wavelengths",
        help="sort bands on wavelength",
    )
    parser.add_argument(
        "-b",
        action="store_true",
        dest="use_bbl",
        help="use bad band list from the header",
    )
    ##    parser.add_argument('-f', action='store_true', dest='force',
    ##                      help='force overwrite on existing output file')
    parser.add_argument("-i", dest="input", help="input file name", required=True)
    parser.add_argument("-o", dest="output", help="output file names (basename)")

    parser.add_argument(
        "-e", action="store_true", dest="strip_edges", help="strip edges"
    )
    parser.add_argument(
        "-z", action="store_true", dest="strip_zeros", help="strip zeros"
    )
    parser.add_argument(
        "-R",
        dest="red",
        type=float,
        help="red band, wavelength or band number (default 0)",
        required=False,
        default=0,
    )
    parser.add_argument(
        "-G",
        dest="green",
        type=float,
        help="green band (default 1)",
        required=False,
        default=1,
    )
    parser.add_argument(
        "-B",
        dest="blue",
        type=float,
        help="blue band (default 2)",
        required=False,
        default=2,
    )
    parser.add_argument(
        "-m",
        dest="mode",
        choices=("NO", "MM", "1P", "SD"),
        default="1P",
        help="stretch mode: NO (none), MM (min-max), 1P (1 percent, default), SD (2 standard deviation)",
    )
    parser.add_argument(
        "-t",
        dest="target",
        choices=TARGETS,
        default=TARGET_MARS,
        help="target: earth, moon, mars (default), sky",
    )

    ##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
    ##                        strip_edges=False, strip_zeros=False,
    ##                        mode='1P', target=TARGET_MARS, output=None)

    options = parser.parse_args()

    ##    assert options.input, "Option -i input file name required."
    ##    assert options.output, "Option -o output file name required."
    ##    assert options.red is not None, "Option -R red band required."
    ##    assert options.green is not None, "Option -G green band required."
    ##    assert options.blue is not None, "Option -B blue band required."
    ##    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    tokml(
        options.input,
        red=options.red,
        green=options.green,
        blue=options.blue,
        stretch_mode=options.mode,
        strip_edges=options.strip_edges,
        strip_zeros=options.strip_zeros,
        sort_wavelengths=options.sort_wavelengths,
        use_bbl=options.use_bbl,
        target=options.target,
        force=options.force,
        fbase=options.output,
    )
