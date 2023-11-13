#!/usr/bin/python3
## meteosat.py
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

# import standard modules
import os
import glob
import sys

# Try to import from Pillow or PIL
try:
    from PIL import Image
except ImportError as errtext:
    import Image

# import array support
import numpy

# the envi2 module for writing ENVI format images
import envi2
import envi2.constants

# local modules
import gregorian
import timestr
import calibration

def message(s):
    print(s)

def convert_meteosat(pattern, output, message=message):
    # figure out input files from the pattern

    fnames = sorted(glob.glob(pattern))

    bands = len(fnames)

    message("Found %d files" % (bands,))

    if not bands:
        return

    # open one image to get info
    im = Image.open(fnames[0])

    samples, lines = im.size

    # assuming 16-bit data
    if im.mode == 'I;16':
        data_type = 'H' # 'h' is signed, 'H' is unsigned 16 bit
        message("Data type: 2-byte")
        is_calibrated = True
    elif im.mode.startswith('F'):
        data_type = 'single'
        message("Data type: 4-byte single float")
        is_calibrated = True
    else:
        data_type = 'u1' # cross your fingers here...
        message("Data type: assuming 1-byte")
        is_calibrated = False
    ##    raise ValueError('Unsupported image mode')

    # figure out byte order of the machine
    if sys.byteorder == 'little':
        byte_order = 0
    else:
        byte_order = 1

    try:
        # map info obtained from GeoTIFF tags (don't ask!)
        map_info = ['Arbitrary', 1.0, 1.0, im.ifd[33922][3], im.ifd[33922][4],
                    im.ifd[33550][0], im.ifd[33550][1], 0, 'units=Degrees']
    except KeyError:
        map_info = None
        
    message("Map info: %s" % (str(map_info),))

    del im

    # loop over file names to get time stamps of images
    wavelength = []
    band_names = []
    for fname in fnames:
        base = os.path.basename(fname)
        message("Inspecting '%s'" % (base,))

        year, month, day, hour, minute = timestr.time_from_string(base)
        band_names.append("%4d%02d%02d%02d%02d" % (year, month, day, hour, minute))

        ltime = gregorian.to_linear_time(year, month, day, hour, minute)
        message("Linear time: %f" % (ltime,))
##        print gregorian.from_linear_time(ltime)
        
        # add linear time to the list of 'wavelengths'
        wavelength.append(ltime)

    # open the output image
    im2 = envi2.New(output, file_type=envi2.constants.ENVI_Standard,
                    data_type='single', interleave='bsq', byte_order=byte_order,
                    lines=lines, samples=samples, bands=bands,
                    wavelength=wavelength, descripion=['GeoTIFF to ENVI stacker'],
                    wavelength_units='Gregorian day', z_plot_titles=['time', 'value'],
                    map_info=map_info, band_names=band_names)

    # and here we go...
    band = 0
    for fname in fnames:
        try:
            im = Image.open(fname)
        except Exception as errtext:
            raise ValueError('%s on file %s band %d' % (errtext, fname, band))

        base = os.path.basename(fname)

        if is_calibrated:
            message("Convering: %s" % (base,))
            message('Calibration SKIPPED')
            
            im.load()
            # again, DON'T ASK!!!
            BT = numpy.array(im.getdata()).reshape(im.size[::-1])
        else:
            year, month, day, hour, minute = timestr.time_from_string(base)
            calib = calibration.get_coeffs(year, month, day, hour, minute)

            alpha = calib[-2]
            space_count = calib[-1]

            message("Calibrating: %s" % (base,))
            message('Calibration data: %f %f' % (alpha, space_count))
            
            im.load()
            # again, DON'T ASK!!!
            data = numpy.array(im.getdata()).reshape(im.size[::-1])

            # convert to radiance
            radiance = alpha * (data - space_count)

            # convert to brightness temperature
            A = 6.7348
            B = -1272.2
            BT = B / (numpy.log(radiance) - A)

        message("Average scene brightness temperature: %.1f Kelvin" % (BT.mean()))
        
        im2[band] = BT

        del im
        band = band + 1

    del im2

if __name__=='__main__':
    pattern = r'/data/Data/Nadira/format1/*.tif'
    output = r'/data/Data/Nadira/format1/stack'

    convert_meteosat(pattern, output)
