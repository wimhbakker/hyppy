#!/usr/bin/python3
## otherindices.py
##
## Created: WHB, 20171005
##
## Copyright (C) 2017 Wim Bakker
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

##
## Indices from Frank van Ruitenbeek
## Albedo1650: R1650
##
## Drop ferrous Fe: R1600/R1310
##
## Cryst illite: D_Al-OH/D-H20 : D~2200/D~1900
##
## Cryst kaolinite: (R2160/R2177)-((R2184/R2190)-(R2160/R2177))
##
## Ililte/kaolinite: R2164/R2180
##
## Smectite: D-H20/(D-deepest feature between 2100 and 2400)
##
## R = reflectance value
##
## D = feature depth
##

import envi2
from numpy import array, sqrt, zeros, polyfit

logfile = None

def message(s):
    global logfile
    if logfile:
        f = open(logfile, 'a')
        f.write(s)
        if len(s) > 1:
            f.write('\n')
        f.close()
        
## Band Depths
band_depth_dict = {
'BD0530_2' : (0.440, 0.530, 0.614),
'BD0640_2' : (0.600, 0.624, 0.760),
'BD0860_2' : (0.755, 0.860, 0.977),
'BD920_2' : (0.807, 0.920, 0.984),
'BD1300' : (1.080, 1.320, 1.750),
'BD1400' : (1.330, 1.395, 1.467),
'BD1435' : (1.370, 1.435, 1.470),
'BD1500_2' : (1.367, 1.525, 1.808),
'BD1750_2' : (1.690, 1.750, 1.815),
'BD2100_2' : (1.930, 2.132, 2.250),
'BD2165' : (2.120, 2.165, 2.230),
'BD2190' : (2.120, 2.185, 2.250),
'BD2210_2' : (2.165, 2.210, 2.250),
'BD2230' : (2.210, 2.235, 2.252),
'BD2250' : (2.120, 2.245, 2.340),
'BD2265' : (2.210, 2.265, 2.340),
'BD2290' : (2.250, 2.290, 2.350),
'BD2355' : (2.300, 2.355, 2.450),
'BD2500_2' : (2.364, 2.480, 2.570),
'BD2600' : (2.530, 2.600, 2.630),
'BD3100' : (3.000, 3.120, 3.250),
'BD3200' : (3.250, 3.320, 3.390),
'BD3400_2' : (3.250, 3.42, 3.630)
}

def _band_depth(ref, BD, message=message, reverse=False):
### For instance BD1750:
##    wshort = 1.660
##    wcenter = 1.750
##    wlong = 1.815

    wshort, wcenter, wlong = BD

    ishort = ref.wavelength2index(wshort)
    icenter = ref.wavelength2index(wcenter)
    ilong = ref.wavelength2index(wlong)

    # these wavelengths are actually used
    xshort = ref.index2wavelength(ishort)
    xcenter = ref.index2wavelength(icenter)
    xlong = ref.index2wavelength(ilong)

    message(" Asked for %g, got %g" % (wshort ,xshort))
    message(" Asked for %g, got %g" % (wcenter ,xcenter))
    message(" Asked for %g, got %g" % (wlong ,xlong))

    Rshort = ref.get_band(ishort)
    Rcenter = ref.get_band(icenter)
    Rlong = ref.get_band(ilong)

    # should we change this to wcenter?
#    b = (xcenter - xshort) / (xlong - xshort)

    try:
        b = (xcenter - xshort) / (xlong - xshort)
        a = 1 - b

        if reverse:
            return 1-((a*Rshort + b*Rlong) / Rcenter)
        else:
            return 1-(Rcenter / (a*Rshort + b*Rlong))
    except ZeroDivisionError:
        return 0 * Rcenter

def band_depth(ref, BD, message=message):
    return _band_depth(ref, BD, message=message, reverse=False)

def shoulder_height(ref, BD, message=message):
    return _band_depth(ref, BD, message=message, reverse=True)

## Other indices

def image_get_band(ref, wavelength, message=message):
    i = ref.wavelength2index(wavelength)
    x = ref.index2wavelength(i)
    message(" Asked for %g, got %g" % (wavelength ,x))
    return ref.get_band(i)

## Albedo1650: R1650

def ALBEDO1650(ref, message=message):
    R1650 = image_get_band(ref, 1.650, message)
    return R1650

## Drop ferrous Fe: R1600/R1310

def DROPFERROUS(ref, message=message):
    R1600 = image_get_band(ref, 1.600, message)
    R1310 = image_get_band(ref, 1.310, message)
    return (R1600 / R1310)

## Cryst kaolinite: (R2160/R2177)-((R2184/R2190)-(R2160/R2177))

def CRYSTKAOL(ref, message=message):
    R2160 = image_get_band(ref, 2.160, message)
    R2177 = image_get_band(ref, 2.177, message)
    R2184 = image_get_band(ref, 2.184, message)
    R2190 = image_get_band(ref, 2.190, message)
    return ((R2160 / R2177) - ((R2184 / R2190) - (R2160 / R2177)))

## Ilite/kaolinite: R2164/R2180

def ILITKAOL(ref, message=message):
    R2164 = image_get_band(ref, 2.164, message)
    R2180 = image_get_band(ref, 2.180, message)
    return (R2164/R2180)


######################################################################
##
## Summary Products from Frank van Ruitenbeek, 2017
##

def products(fin, fout, sort_wavelengths=False, use_bbl=True,
             message=message, wavelength_units=None, progress=None):

    ref = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if wavelength_units=='Nanometers' or wavelength_units=='nan':
        ref.wavelength = array(ref.wavelength) / 1000.0

    im2 = envi2.New(fout, 
                          hdr=ref, interleave='bsq', bbl=None,
                          bands=4, band_names=None,
                          wavelength=None,
                          data_type='d')

    i = 0
    band_name_list = list()

## what follows are a number of indices requested by Frank van Ruitenbeek, 2017

## Albedo 1650
    
    band_name = 'ALBEDO1650'
    message(band_name)
    im2[:,:,i] = ALBEDO1650(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## DROP ferrous Fe
    
    band_name = 'DROPFERROUS'
    message(band_name)
    im2[:,:,i] = DROPFERROUS(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## CRYSTKAOL
    
    band_name = 'CRYSTKAOL'
    message(band_name)
    im2[:,:,i] = CRYSTKAOL(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## ILITKAOL
    
    band_name = 'ILITKAOL'
    message(band_name)
    im2[:,:,i] = ILITKAOL(ref, message)
    band_name_list.append(band_name)

    i = i + 1

    # update header with band names
    header = envi2.header.Header(hdr=im2, band_names=band_name_list)
    header.write(fout)

    del ref,im2, header

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='otherindices.py',
##        usage='summary_products.py -s -b -f -l -i input -c continuumremoved -o output -u {mic|nan}',
        description='Summary Products, mineral and other indices.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output files')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)
    
    parser.add_argument('-u', dest='units', choices=['mic', 'nan'], default='mic',
                      help='input wavelength units: mic (default, micrometers) or nan (nanometers)')

    parser.add_argument('-l', action='store_true', dest='makelog',
                      help='create a logfile')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        units='mic', makelog=False)

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.cr, "Option -c input continuum removed file name required."
##    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.makelog:
        logfile = options.output + '.log'
        f = open(logfile, 'w')  # destroys old log file if it exists
        f.write('Log file created by command line version\n')
        f.close()

    products(options.input, options.output,
             wavelength_units=options.units,
             sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
