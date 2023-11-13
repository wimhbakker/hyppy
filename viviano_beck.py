#!/usr/bin/python3
## viviano_beck.py
##
## Created: WHB, 20160315
##
## Copyright (C) 2016 Wim Bakker
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

## OLINDEX

def OLINDEX(ref, message=message):
    R1695 = image_get_band(ref, 1.695, message)
    R1050 = image_get_band(ref, 1.050, message)
    R1210 = image_get_band(ref, 1.210, message)
    R1330 = image_get_band(ref, 1.330, message)
    R1470 = image_get_band(ref, 1.470, message)
    return (R1695 / (0.1 * R1050 + 0.1 * R1210 + 0.4 * R1330 + 0.4 * R1470)) - 1

## OLINDEX2, Jelmer Oosthoek

def OLINDEX2(ref, message=message):
    R2404 = image_get_band(ref, 2.404, message)
    R2397 = image_get_band(ref, 2.397, message)
    R2410 = image_get_band(ref, 2.410, message)

    R1750 = image_get_band(ref, 1.750, message)
    R1744 = image_get_band(ref, 1.744, message)
    R1757 = image_get_band(ref, 1.757, message)

    R1054 = image_get_band(ref, 1.054, message)
    R1047 = image_get_band(ref, 1.047, message)
    R1060 = image_get_band(ref, 1.060, message)

    R1211 = image_get_band(ref, 1.211, message)
    R1204 = image_get_band(ref, 1.204, message)
    R1218 = image_get_band(ref, 1.218, message)

    R1329 = image_get_band(ref, 1.329, message)
    R1326 = image_get_band(ref, 1.326, message)
    R1336 = image_get_band(ref, 1.336, message)

    R1474 = image_get_band(ref, 1.474, message)
    R1467 = image_get_band(ref, 1.467, message)
    R1480 = image_get_band(ref, 1.480, message)

    AVG2404 = ((R2404 + R2397 + R2410) / 3)
    AVG1750 = ((R1750 + R1744 + R1757) / 3)
    AVG1054 = ((R1054 + R1047 + R1060) / 3)
    AVG1211 = ((R1211 + R1204 + R1218) / 3)
    AVG1329 = ((R1329 + R1326 + R1336) / 3)
    AVG1474 = ((R1474 + R1467 + R1480) / 3)

    #Slope of the continuum
    contm = ((AVG2404 - AVG1750) / (2.404 - 1.750))

    #y-intercept of the continuum
    yint = (AVG2404 - (2.404 * contm))

    #Expected values at 1.054, 1.211, 1.329, and 1.474 microns, respectively
    ex1054 = ((contm * 1.054) + yint)
    ex1211 = ((contm * 1.211) + yint)
    ex1329 = ((contm * 1.329) + yint)
    ex1474 = ((contm * 1.474) + yint)

    #Calculated band depths at 1.054, 1.211, 1.329, and 1.474 microns, respectively, with weights
    return (((ex1054 - AVG1054) / ex1054) * 0.1) + (((ex1211 - AVG1211) / ex1211) * 0.1) + (((ex1329 - AVG1329) / ex1329) * 0.4) + (((ex1474 - AVG1474) / ex1474) * 0.4)

def OLINDEX3(ref, message):
    bd1080 = band_depth(ref, (1.750, 1.080, 2.400), message)
    bd1152 = band_depth(ref, (1.750, 1.152, 2.400), message)
    bd1210 = band_depth(ref, (1.750, 1.210, 2.400), message)
    bd1250 = band_depth(ref, (1.750, 1.250, 2.400), message)
    bd1263 = band_depth(ref, (1.750, 1.263, 2.400), message)
    bd1276 = band_depth(ref, (1.750, 1.276, 2.400), message)
    bd1330 = band_depth(ref, (1.750, 1.330, 2.400), message)
    bd1368 = band_depth(ref, (1.750, 1.368, 2.400), message)
    bd1395 = band_depth(ref, (1.750, 1.395, 2.400), message)
    bd1427 = band_depth(ref, (1.750, 1.427, 2.400), message)
    bd1470 = band_depth(ref, (1.750, 1.470, 2.400), message)
    return 0.03*bd1080 + 0.03*bd1152 + 0.03*bd1210 + \
           0.03*bd1250 + 0.07*bd1263 + 0.07*bd1276 + \
           0.12*bd1330 + 0.12*bd1368 + 0.14*bd1395 + \
           0.18*bd1427 + 0.18*bd1470

## LCPINDEX

def LCPINDEX(ref, message=message):
    R1330 = image_get_band(ref, 1.330, message)
    R1050 = image_get_band(ref, 1.050, message)
    R1815 = image_get_band(ref, 1.815, message)
    return ((R1330 - R1050) / (R1330 + R1050)) * ((R1330 - R1815) / ( R1330 + R1815))

def LCPINDEX2(ref, message):
    bd1690 = band_depth(ref, (1.560, 1.690, 2.450), message)
    bd1750 = band_depth(ref, (1.560, 1.750, 2.450), message)
    bd1810 = band_depth(ref, (1.560, 1.810, 2.450), message)
    bd1870 = band_depth(ref, (1.560, 1.870, 2.450), message)
    return 0.2*bd1690 + 0.2*bd1750 + 0.3*bd1810 + 0.3*bd1870

## HCPINDEX

def HCPINDEX(ref, message=message):
    R1470 = image_get_band(ref, 1.470, message)
    R1050 = image_get_band(ref, 1.050, message)
    R2067 = image_get_band(ref, 2.067, message)
    return ((R1470 - R1050) / (R1470 + R1050)) * ((R1470 - R2067) / ( R1470 + R2067))

def HCPINDEX2(ref, message):
    bd2120 = band_depth(ref, (1.690, 2.120, 2.530), message)
    bd2140 = band_depth(ref, (1.690, 2.140, 2.530), message)
    bd2230 = band_depth(ref, (1.690, 2.230, 2.530), message)
    bd2250 = band_depth(ref, (1.690, 2.250, 2.530), message)
    bd2430 = band_depth(ref, (1.690, 2.430, 2.530), message)
    bd2460 = band_depth(ref, (1.690, 2.460, 2.530), message)
    return 0.1*bd2120 + 0.1*bd2140 + 0.15*bd2230 + \
           0.3*bd2250 + 0.2*bd2430 + 0.15*bd2460

## ISLOPE1

def ISLOPE1(ref, message=message):
    R1815 = image_get_band(ref, 1.815, message)
    R2530 = image_get_band(ref, 2.530, message)
    return (R1815 - R2530) / (2530-1815) # ?

## DROP2300

def DROP2300(cr, message=message):
    CR2290 = image_get_band(cr, 2.290, message)
    CR2320 = image_get_band(cr, 2.320, message)
    CR2330 = image_get_band(cr, 2.330, message)
    CR2140 = image_get_band(cr, 2.140, message)
    CR2170 = image_get_band(cr, 2.170, message)
    CR2210 = image_get_band(cr, 2.210, message)
    return 1 - ((CR2290 + CR2320 + CR2330) / (CR2140 + CR2170 + CR2210))

## DROP2400

def DROP2400(cr, message=message):
    CR2390 = image_get_band(cr, 2.390, message)
    CR2430 = image_get_band(cr, 2.430, message)
    CR2290 = image_get_band(cr, 2.290, message)
    CR2320 = image_get_band(cr, 2.320, message)
    return 1 - ((CR2390 + CR2430) / (CR2290 + CR2320))

## BD3400

def BD3400(ref, message=message):
    R3390 = image_get_band(ref, 3.390, message)
    R3500 = image_get_band(ref, 3.500, message)
    R3250 = image_get_band(ref, 3.250, message)
    R3630 = image_get_band(ref, 3.630, message)
    a = 0.909
    b = 1 - a
    c = 0.605
    d = 1 - c
    return 1 - ((a*R3390 + b*R3500) / (c*R3250 + d*R3630))

## CINDEX2

def CINDEX2(ref, message=message):
    R3450 = image_get_band(ref, 3.450, message)
    R3610 = image_get_band(ref, 3.610, message)
    R3875 = image_get_band(ref, 3.875, message)
##  b = (center - short) / (long - short)
##  a = 1 - b
    b = (3.610 - 3.450) / (3.875 - 3.450)
    a = 1 - b
    return 1 - ((a*R3450 + b*R3875) / R3610)

## RBR

def RBR(ref, message=message):
    R0770 = image_get_band(ref, 0.770, message)
    R0440 = image_get_band(ref, 0.440, message)
    return R0770 / R0440

## SH600_2

##def SH600_2(ref, message=message):
##    R0533 = image_get_band(ref, 0.533, message)
##    R0600 = image_get_band(ref, 0.600, message)
##    R0716 = image_get_band(ref, 0.716, message)
##    b = (0.600-0.533) / (0.716-0.533)
##    a = 1 - b
##    return R0600 / (a*R0530 + b*R0680)

## ICER1_2

def ICER1_2(ref, message=message):
    bd1435   = band_depth(ref, band_depth_dict['BD1435'], message)
    bd1500_2 = band_depth(ref, band_depth_dict['BD1500_2'], message)
    return 1 - ((1 - bd1435) / (1 - bd1500_2))

## BD1900

def BD1900(ref, message=message):
    R1930 = image_get_band(ref, 1.930, message)
    R1985 = image_get_band(ref, 1.985, message)
    R1857 = image_get_band(ref, 1.875, message)
    R2067 = image_get_band(ref, 2.067, message)
    b = (1.958-1.857) / (2.067-1.857)
    a = 1 - b
    return 1 - (((R1930 + R1985) * 0.5) / (a*R1857 + b*R2067))

def BD1900_2(ref, message=message):
    return (band_depth(ref, (1.850, 1.930, 2.067), message) + \
            band_depth(ref, (1.850, 1.985, 2.067), message)) / 2.0

## BD1900r2

def BD1900r2(ref, message=message):
    R1908 = image_get_band(ref, 1.908, message)
    R1914 = image_get_band(ref, 1.914, message)
    R1921 = image_get_band(ref, 1.921, message)
    R1928 = image_get_band(ref, 1.928, message)
    R1934 = image_get_band(ref, 1.934, message)
    R1941 = image_get_band(ref, 1.941, message)
    R1862 = image_get_band(ref, 1.862, message)
    R1869 = image_get_band(ref, 1.869, message)
    R1875 = image_get_band(ref, 1.875, message)
    R2112 = image_get_band(ref, 2.112, message)
    R2120 = image_get_band(ref, 2.120, message)
    R2126 = image_get_band(ref, 2.126, message)

    RC1908 = band_depth(ref, (1.850, 1.908, 2.060), message)
    RC1914 = band_depth(ref, (1.850, 1.914, 2.060), message)
    RC1921 = band_depth(ref, (1.850, 1.921, 2.060), message)
    RC1928 = band_depth(ref, (1.850, 1.928, 2.060), message)
    RC1934 = band_depth(ref, (1.850, 1.934, 2.060), message)
    RC1941 = band_depth(ref, (1.850, 1.941, 2.060), message)
    RC1862 = band_depth(ref, (1.850, 1.862, 2.060), message)
    RC1869 = band_depth(ref, (1.850, 1.869, 2.060), message)
    RC1875 = band_depth(ref, (1.850, 1.875, 2.060), message)
    RC2112 = band_depth(ref, (1.850, 2.112, 2.060), message)
    RC2120 = band_depth(ref, (1.850, 2.120, 2.060), message)
    RC2126 = band_depth(ref, (1.850, 2.126, 2.060), message)

    try:
        return 1 - ((R1908/RC1908 + R1914/RC1914 + R1921/RC1921 + \
                     R1928/RC1928 + R1934/RC1934 + R1941/RC1941) / \
                    (R1862/RC1862 + R1869/RC1869 + R1875/RC1875 + \
                     R2112/RC2112 + R2120/RC2120 + R2126/RC2126))
    except:
        return 0

## D2200

def D2200(ref, message=message):
    R2165 = image_get_band(ref, 2.165, message)
    R2210 = image_get_band(ref, 2.210, message)
    R2230 = image_get_band(ref, 2.230, message)

    RC2165 = band_depth(ref, (1.815, 2.165, 2.430), message)
    RC2210 = band_depth(ref, (1.815, 2.210, 2.430), message)
    RC2230 = band_depth(ref, (1.815, 2.230, 2.430), message)

    return 1 - ((R2210/RC2210 + R2230/RC2230) / (2*R2165/RC2165))

## D2300

def D2300(ref, message=message):
    R2120 = image_get_band(ref, 2.120, message)
    R2170 = image_get_band(ref, 2.170, message)
    R2210 = image_get_band(ref, 2.210, message)
    R2290 = image_get_band(ref, 2.290, message)
    R2320 = image_get_band(ref, 2.320, message)
    R2330 = image_get_band(ref, 2.330, message)

    RC2120 = band_depth(ref, (1.815, 2.120, 2.530), message)
    RC2170 = band_depth(ref, (1.815, 2.170, 2.530), message)
    RC2210 = band_depth(ref, (1.815, 2.210, 2.530), message)
    RC2290 = band_depth(ref, (1.815, 2.290, 2.530), message)
    RC2320 = band_depth(ref, (1.815, 2.320, 2.530), message)
    RC2330 = band_depth(ref, (1.815, 2.330, 2.530), message)

    return 1 - ((R2290/RC2290 + R2320/RC2320 + R2330/RC2330) / \
                (R2120/RC2120 + R2170/RC2170 + R2210/RC2210))

## BD2100

def BD2100(ref, message=message):
    R2120 = image_get_band(ref, 2.120, message)
    R2140 = image_get_band(ref, 2.140, message)
    R1930 = image_get_band(ref, 1.930, message)
    R2250 = image_get_band(ref, 2.250, message)
    b = (2.130-1.930) / (2.250-1.930)
    a = 1 - b
    return 1 - (((R2120 + R2140) * 0.5) / (a*R1930 + b*R2250))

## MIN2200

def MIN2200(ref, message=message):
    bd2165 = band_depth(ref, (2.120, 2.165, 2.350), message)
    bd2210 = band_depth(ref, (2.120, 2.210, 2.350), message)
    return array((bd2165, bd2210)).min(axis=0)

## MIN2250

def MIN2250(ref, message=message):
    bd2210 = band_depth(ref, (2.165, 2.210, 2.350), message)
    bd2265 = band_depth(ref, (2.165, 2.265, 2.350), message)
    return array((bd2210, bd2265)).min(axis=0)

## MIN2295_2480

def MIN2295_2480(ref, message=message):
    bd2295 = band_depth(ref, (2.165, 2.295, 2.364), message)
    bd2480 = band_depth(ref, (2.364, 2.480, 2.570), message)
    return array((bd2295, bd2480)).min(axis=0)

## MIN2345_2537

def MIN2345_2537(ref, message=message):
    bd2345 = band_depth(ref, (2.250, 2.345, 2.430), message)
    bd2537 = band_depth(ref, (2.430, 2.537, 2.602), message)
    return array((bd2345, bd2537)).min(axis=0)

## ICER2

def ICER2(ref, message=message):
    R2530 = image_get_band(ref, 2.530, message)
    R2600 = image_get_band(ref, 2.600, message)
    return R2530 / R2600

## BDCARB

def BDCARB(ref, message=message):
    R2330 = image_get_band(ref, 2.330, message)
    R2230 = image_get_band(ref, 2.230, message)
    R2390 = image_get_band(ref, 2.390, message)
    b = (2.330-2.230) / (2.390-2.230)
    a = 1 - b
    res1 = R2330 / (a*R2230 + b*R2390)

    R2530 = image_get_band(ref, 2.530, message)
#    R2390 = image_get_band(ref, 2.390, message)
    R2600 = image_get_band(ref, 2.600, message)
    b = (2.530-2.390) / (2.600-2.390)
    a = 1 - b
    res2 = R2530 / (a*R2390 + b*R2600)

    return 1 - (sqrt(res1 * res2))

## R410

def R410(ref, message=message):
    R0410 = image_get_band(ref, 0.410, message)
    return R0410

## R770

def R770(ref, message=message):
    R0770 = image_get_band(ref, 0.770, message)
    return R0770

## IRA

def IRA(ref, message=message):
    R1330 = image_get_band(ref, 1.330, message)
    return R1330

## IRR1

def IRR1(ref, message=message):
    R0800 = image_get_band(ref, 0.800, message)
    R0997 = image_get_band(ref, 0.997, message)
    return R0800 / R0997

## IRR2

def IRR2(ref, message=message):
    R2530 = image_get_band(ref, 2.530, message)
    R2210 = image_get_band(ref, 2.210, message)
    return R2530 / R2210

## IRR3

def IRR3(ref, message=message):
    R3390 = image_get_band(ref, 3.390, message)
    R3500 = image_get_band(ref, 3.500, message)
    return R3500 / R3390

## BD1270O2

def BD1270O2(ref, message=message):
    R1261 = image_get_band(ref, 1.261, message)
    R1268 = image_get_band(ref, 1.268, message)
    R1250 = image_get_band(ref, 1.250, message)
    R1280 = image_get_band(ref, 1.280, message)
    b = (1.265 - 1.261) / (1.268 - 1.261)
    a = 1 - b
    d = (1.265 - 1.250) / (1.280 - 1.250)
    c = 1 - d
    return 1 - ((a*R1261 + b*R1268) / (c*R1250 + d*R1280))

## BD3000

def BD3000(ref, message=message):
    R3000 = image_get_band(ref, 3.000, message)
    R2530 = image_get_band(ref, 2.530, message)
    R2210 = image_get_band(ref, 2.210, message)

    return 1 - (R3000 / (R2530 * (R2530 / R2210)))

## BD1400H2O

def BD1400H2O(ref, message=message):
    R1370 = image_get_band(ref, 1.370, message)
    R1400 = image_get_band(ref, 1.400, message)
    R1330 = image_get_band(ref, 1.330, message)
    R1510 = image_get_band(ref, 1.510, message)
    b = (1.380 - 1.370) / (1.400 - 1.370)
    a = 1 - b
    d = (1.380 - 1.330) / (1.510 - 1.330)
    c = 1 - d
    return 1 - ((a*R1370 + b*R1400) / (c*R1330 + d*R1510))

## R2700

def R2700(ref, message=message):
    R2700 = image_get_band(ref, 2.700, message)
    return R2700

## BD2700

def BD2700(ref, message=message):
    R2700 = image_get_band(ref, 2.700, message)
    R2530 = image_get_band(ref, 2.530, message)
    R2350 = image_get_band(ref, 2.350, message)

    return 1 - (R2700 / (R2530 * (R2530 / R2350)))

## D2300, Jelmer Oosthoek

def D2300_old(ref, message=message):
    R1815 = image_get_band(ref, 1.815, message)
    R2530 = image_get_band(ref, 2.530, message)
    R2320 = image_get_band(ref, 2.320, message)
    W2320 = ref.index2wavelength(ref.wavelength2index(2.320))
    R2170 = image_get_band(ref, 2.170, message)
    W2170 = ref.index2wavelength(ref.wavelength2index(2.170))
    R2120 = image_get_band(ref, 2.120, message)
    R2290 = image_get_band(ref, 2.290, message)
    R2350 = image_get_band(ref, 2.350, message)
    R2330 = image_get_band(ref, 2.330, message)
    R2210 = image_get_band(ref, 2.210, message)
    a2300 = ref.index2wavelength(ref.wavelength2index(2.530))
    b2300 = ref.index2wavelength(ref.wavelength2index(1.815))
    slope = ((R2530 - R1815) / (a2300 - b2300))
    CR2290 = (R1815 + slope * (ref.index2wavelength(ref.wavelength2index(2.290)) - b2300))
    CR2320 = (R1815 + slope * (ref.index2wavelength(ref.wavelength2index(2.320)) - b2300))
    CR2330 = (R1815 + slope * (ref.index2wavelength(ref.wavelength2index(2.330)) - b2300))
    CR2120 = (R1815 + slope * (ref.index2wavelength(ref.wavelength2index(2.120)) - b2300))
    CR2170 = (R1815 + slope * (ref.index2wavelength(ref.wavelength2index(2.170)) - b2300))
    CR2210 = (R1815 + slope * (ref.index2wavelength(ref.wavelength2index(2.210)) - b2300))
    return (1 - ( ((R2290 / CR2290) + (R2320 / CR2320) + (R2330 / CR2330)) / ((R2120 / CR2120) + (R2170 / CR2170) + (R2210 / CR2210)) ))

## VAR

def VAR(ref, message=message, progress=None):
    arr = zeros((ref.lines, ref.samples))
    i_first = ref.wavelength2index(1.0)
    i_last = ref.wavelength2index(2.3) + 1

    if progress:
        progress(0.0)

    for j in range(ref.lines):
        if progress:
            progress(j / float(ref.lines))
        for i in range(ref.samples):
            x = array(ref.wavelength[i_first:i_last])
            y = ref.get_spectrum(j, i)[i_first:i_last]

            a, b = polyfit(x, y, 1)
            arr[j, i] = (y - (a*x+b)).var()

    if progress:
        progress(1.0)
    
    return arr


######################################################################
##
## Summary Products according to Viviano-Beck, 2014
##

def products(fin, fout, sort_wavelengths=False, use_bbl=True,
             message=message, wavelength_units=None, progress=None):

    ref = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if wavelength_units == 'Nanometers':
        ref.wavelength = array(ref.wavelength) / 1000.0

    im2 = envi2.New(fout, 
                          hdr=ref, interleave='bsq', bbl=None,
                          bands=60, band_names=None,
                          wavelength=None,
                          data_type='d')

    i = 0
    band_name_list = list()

## what follows are the 60 indices mentioned in Viviano-Beck, 2014

## Viviano-Beck # 1, 0.77 micron reflectance
    
    band_name = 'R770'
    message(band_name)
    im2[:,:,i] = R770(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 2, red/blue ratio
    
    band_name = 'RBR'
    message(band_name)
    im2[:,:,i] = RBR(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 3, 0.53 micron band depth
    
    band_name = 'BD0530_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 4, 0.6 micron shoulder heigth
    
    band_name = 'SH600_2'
    message(band_name)
    im2[:,:,i] = shoulder_height(ref, (0.533, 0.600, 0.716), message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 5, 0.77 micron shoulder height
    
    band_name = 'SH770'
    message(band_name)
    im2[:,:,i] = shoulder_height(ref, (0.716, 0.775, 0.860), message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 6, 0.64 micron band depth
    
    band_name = 'BD0640_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 7, 0.86 micron band depth
    
    band_name = 'BD0860_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 8, 0.92 micron band depth
    
    band_name = 'BD920_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 9, reflectance peak 1
    
    band_name = 'RPEAK1'
    message(band_name)
    message("not implemented")
    im2[:,:,i] = 0
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 10, 1 micron integrated band depth, VNIR wavelengths
    
    band_name = 'BDI1000VIS'
    message(band_name)
    message("not implemented")
    im2[:,:,i] = 0
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 11, 1 micron integrated band depth, IR wavelengths
    
    band_name = 'BDI1000IR'
    message(band_name)
    message("not implemented")
    im2[:,:,i] = 0
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 12, IR albedo
    
    band_name = 'R1330'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 1.330, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 13, 1.3 micron absorption associated with Fe2+ substitution
##                      in plagioclase
    
    band_name = 'BD1300'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 14, detect broad absorption centered at 1 micron
    
    band_name = 'OLINDEX3'
    message(band_name)
    im2[:,:,i] = OLINDEX3(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 15, detect broad absorption centered at 1.81 micron
    
    band_name = 'LCPINDEX2'
    message(band_name)
    im2[:,:,i] = LCPINDEX2(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 16, detect broad absorption centered at 2.12 micron
    
    band_name = 'HCPINDEX2'
    message(band_name)
    im2[:,:,i] = HCPINDEX2(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 17, 1.0-2.3 micron spectral variance
    
    band_name = 'VAR'
    message(band_name)
    im2[:,:,i] = VAR(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 18, spectral slope 1
    
    band_name = 'ISLOPE1'
    message(band_name)
    im2[:,:,i] = ISLOPE1(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 19, 1.4 micron H2O and -OH band depth
    
    band_name = 'BD1400'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 20, 1.435 micron CO2 ice band depth
    
    band_name = 'BD1435'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 21, 1.5 micron H2O ice band depth
    
    band_name = 'BD1500_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 22, CO2 and H2O ice band depth ratio
    
    band_name = 'ICER1_2'
    message(band_name)
    im2[:,:,i] = ICER1_2(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 23, 1.7 micron H2O band depth
    
    band_name = 'BD1750_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 24, 1.9 micron H2O band depth
    
    band_name = 'BD1900_2'
    message(band_name)
    im2[:,:,i] = BD1900_2(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 25, 1.9 micron H2O band depth
    
    band_name = 'BD1900r2'
    message(band_name)
    message("not implemented")
    im2[:,:,i] = 0
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 26, 2 micron integrated band depth
    
    band_name = 'BDI2000'
    message(band_name)
    message("not implemented")
    im2[:,:,i] = 0
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 27, 2.1 micron shifted H2O band depth
    
    band_name = 'BD2100_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 28, 2.165 mciron Al-OH band depth
    
    band_name = 'BD2165'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 29, 2.190 mciron Al-OH band depth
    
    band_name = 'BD2190'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 30, 2.16 micron Si-OH band depth and 2.21 micron H-bound
##                 Si-OH band depth (doublet)
    
    band_name = 'MIN2200'
    message(band_name)
    im2[:,:,i] = MIN2200(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 31, 2.21 micron Al-OH band depth
    
    band_name = 'BD2210_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 32, 2.2 micron dropoff
    
    band_name = 'D2200'
    message(band_name)
    im2[:,:,i] = D2200(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 33, 2.23 micron band depth
    
    band_name = 'BD2230'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 34, 2.25 micron broad Al-OH and Si-OH band depth
    
    band_name = 'BD2250'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 35, 2.21 micron Si-OH band depth and 2.26 micron
##      H-bound Si-OH band depth
    
    band_name = 'MIN2250'
    message(band_name)
    im2[:,:,i] = MIN2250(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 36, 2.265 micron band depth
    
    band_name = 'BD2265'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 37, 2.3 micron Mg,Fe-OH band depth / 2.292 micron
##                 CO2 ice band depth
    
    band_name = 'BD2290'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 38, 2.3 micron dropoff
    
    band_name = 'D2300'
    message(band_name)
    im2[:,:,i] = D2300(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 39, 2.35 micron band depth
    
    band_name = 'BD2355'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 40, inverse lever rule to detect convexity at 2.29 micron
##          due to 2.1 micron and 2.4 micron absorptions
    
    band_name = 'SINDEX2'
    message(band_name)
    im2[:,:,i] = shoulder_height(ref, (2.120, 2.290, 2.400), message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 41, 2.7 micron CO2 ice band
    
    band_name = 'ICER2_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, (2.456, 2.600, 2.530), message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 42, Mg carbonate overtone band depth and metal-OH band
    
    band_name = 'MIN2295_2480'
    message(band_name)
    im2[:,:,i] = MIN2295_2480(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 43, Ca/Fe carbonate overtone band depth and metal-OH band
    
    band_name = 'MIN2345_2537'
    message(band_name)
    im2[:,:,i] = MIN2345_2537(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 44, Mg carbonate overtone band depth
    
    band_name = 'BD2500_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 45, 3 micron H2O band depth
    
    band_name = 'BD3000'
    message(band_name)
    im2[:,:,i] = BD3000(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 46, 3.1 micron H2O ice band depth
    
    band_name = 'BD3100'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 47, 3.2 micron CO2 ice band depth
    
    band_name = 'BD3200'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 48, 3.4 carbonate band depth
    
    band_name = 'BD3400_2'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 49, inverse lever rule to detect convexity at 3.6 micron
##        due to 3.4 micron and 3.9 micron absorptions
    
    band_name = 'CINDEX2'
    message(band_name)
    im2[:,:,i] = shoulder_height(ref, (3.450, 3.610, 3.875), message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 50, 0.44 micron reflectance
    
    band_name = 'R440'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 0.440, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 51, 0.53 micron reflectance
    
    band_name = 'R530'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 0.530, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 52, 0.60 micron reflectance
    
    band_name = 'R600'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 0.600, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 53, IR ratio 1
    
    band_name = 'IRR1'
    message(band_name)
    im2[:,:,i] = IRR1(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 54, 1.08 micron reflectance
    
    band_name = 'R1080'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 1.080, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 55, 1.51 micron reflectance
    
    band_name = 'R1506'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 1.506, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 56, 2.53 micron reflectance
    
    band_name = 'R2529'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 2.529, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 57, 2.6 micron H2O band depth
    
    band_name = 'BD2600'
    message(band_name)
    im2[:,:,i] = band_depth(ref, band_depth_dict[band_name], message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 58, IR ratio 2
    
    band_name = 'IRR2'
    message(band_name)
    im2[:,:,i] = IRR2(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 59, IR ratio 3
    
    band_name = 'IRR3'
    message(band_name)
    im2[:,:,i] = IRR3(ref, message)
    band_name_list.append(band_name)

    i = i + 1

## Viviano-Beck # 60, 3.92 micron reflectance
    
    band_name = 'R3920'
    message(band_name)
    im2[:,:,i] = image_get_band(ref, 3.920, message)
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

    parser = argparse.ArgumentParser(prog='viviano_beck.py',
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
