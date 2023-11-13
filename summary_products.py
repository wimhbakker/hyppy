#!/usr/bin/python3
## summary_products.py
##
## MODIFIED 20131115, Jelmer Oosthoek, added OLINDEX2 and D2300
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
band_depths = {
'BD0530' : (0.440, 0.530, 0.648),
'BD0640' : (0.600, 0.648, 0.680),
'BD0860' : (0.800, 0.860, 0.920),
'BD1435' : (1.370, 1.430, 1.470),
'BD1500' : (1.300, 1.510, 1.695),
'BD1750' : (1.660, 1.750, 1.815),
'BD2210' : (2.140, 2.210, 2.250),
'BD2290' : (2.250, 2.290, 2.350),
'BD3100' : (3.000, 3.120, 3.250),
'BD3200' : (3.250, 3.320, 3.390),
'BD2000CO2' : (1.815, 2.010, 2.170),
'BD2600' : (2.530, 2.600, 2.630)}

band_names = sorted(band_depths.keys())

def band_depth(ref, BD, message=message):
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
        b = (wcenter - xshort) / (xlong - xshort)
        a = 1 - b

        return 1-(Rcenter / (a*Rshort + b*Rlong))
    except ZeroDivisionError:
        return 0 * Rcenter

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

band_names = band_names + ['OLINDEX']

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

band_names = band_names + ['OLINDEX2']

## LCPINDEX

def LCPINDEX(ref, message=message):
    R1330 = image_get_band(ref, 1.330, message)
    R1050 = image_get_band(ref, 1.050, message)
    R1815 = image_get_band(ref, 1.815, message)
    return ((R1330 - R1050) / (R1330 + R1050)) * ((R1330 - R1815) / ( R1330 + R1815))

band_names = band_names + ['LCPINDEX']

## HCPINDEX

def HCPINDEX(ref, message=message):
    R1470 = image_get_band(ref, 1.470, message)
    R1050 = image_get_band(ref, 1.050, message)
    R2067 = image_get_band(ref, 2.067, message)
    return ((R1470 - R1050) / (R1470 + R1050)) * ((R1470 - R2067) / ( R1470 + R2067))

band_names = band_names + ['HCPINDEX']

## ISLOPE1

def ISLOPE1(ref, message=message):
    R1815 = image_get_band(ref, 1.815, message)
    R2530 = image_get_band(ref, 2.530, message)
    return (R1815 - R2530) / (2530-1815) # ?

band_names = band_names + ['ISLOPE1']

## DROP2300

def DROP2300(cr, message=message):
    CR2290 = image_get_band(cr, 2.290, message)
    CR2320 = image_get_band(cr, 2.320, message)
    CR2330 = image_get_band(cr, 2.330, message)
    CR2140 = image_get_band(cr, 2.140, message)
    CR2170 = image_get_band(cr, 2.170, message)
    CR2210 = image_get_band(cr, 2.210, message)
    return 1 - ((CR2290 + CR2320 + CR2330) / (CR2140 + CR2170 + CR2210))

band_names = band_names + ['DROP2300']

## DROP2400

def DROP2400(cr, message=message):
    CR2390 = image_get_band(cr, 2.390, message)
    CR2430 = image_get_band(cr, 2.430, message)
    CR2290 = image_get_band(cr, 2.290, message)
    CR2320 = image_get_band(cr, 2.320, message)
    return 1 - ((CR2390 + CR2430) / (CR2290 + CR2320))

band_names = band_names + ['DROP2400']

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

band_names = band_names + ['BD3400']

## CINDEX

def CINDEX(ref, message=message):
    R3750 = image_get_band(ref, 3.750, message)
    R3630 = image_get_band(ref, 3.630, message)
    R3950 = image_get_band(ref, 3.950, message)
    return (R3750 + (R3750 - R3630) / (3.750-3.630) * (3.950-3.750)) / R3950 - 1

band_names = band_names + ['CINDEX']

## RBR

def RBR(ref, message=message):
    R0770 = image_get_band(ref, 0.770, message)
    R0440 = image_get_band(ref, 0.440, message)
    return R0770 / R0440

band_names = band_names + ['RBR']

## SH600

def SH600(ref, message=message):
    R0530 = image_get_band(ref, 0.530, message)
    R0600 = image_get_band(ref, 0.600, message)
    R0680 = image_get_band(ref, 0.680, message)
    b = (0.600-0.530) / (0.680-0.530)
    a = 1 - b
    return R0600 / (a*R0530 + b*R0680)

band_names = band_names + ['SH600']

## ICER1

def ICER1(ref, message=message):
    R1430 = image_get_band(ref, 1.430, message)
    R1510 = image_get_band(ref, 1.510, message)
    return R1510 / R1430

band_names = band_names + ['ICER1']

## BD1900

def BD1900(ref, message=message):
    R1930 = image_get_band(ref, 1.930, message)
    R1985 = image_get_band(ref, 1.985, message)
    R1857 = image_get_band(ref, 1.875, message)
    R2067 = image_get_band(ref, 2.067, message)
    b = (1.958-1.857) / (2.067-1.857)
    a = 1 - b
    return 1 - (((R1930 + R1985) * 0.5) / (a*R1857 + b*R2067))

band_names = band_names + ['BD1900']

## BD2100

def BD2100(ref, message=message):
    R2120 = image_get_band(ref, 2.120, message)
    R2140 = image_get_band(ref, 2.140, message)
    R1930 = image_get_band(ref, 1.930, message)
    R2250 = image_get_band(ref, 2.250, message)
    b = (2.130-1.930) / (2.250-1.930)
    a = 1 - b
    return 1 - (((R2120 + R2140) * 0.5) / (a*R1930 + b*R2250))

band_names = band_names + ['BD2100']

## ICER2

def ICER2(ref, message=message):
    R2530 = image_get_band(ref, 2.530, message)
    R2600 = image_get_band(ref, 2.600, message)
    return R2530 / R2600

band_names = band_names + ['ICER2']

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

band_names = band_names + ['BDCARB']

## R410

def R410(ref, message=message):
    R0410 = image_get_band(ref, 0.410, message)
    return R0410

band_names = band_names + ['R410(=510!)']

## R770

def R770(ref, message=message):
    R0770 = image_get_band(ref, 0.770, message)
    return R0770

band_names = band_names + ['R770']

## IRA

def IRA(ref, message=message):
    R1330 = image_get_band(ref, 1.330, message)
    return R1330

band_names = band_names + ['IRA']

## IRR1

def IRR1(ref, message=message):
    R0800 = image_get_band(ref, 0.800, message)
    R1020 = image_get_band(ref, 1.020, message)
    return R0800 / R1020

band_names = band_names + ['IRR1']

## IRR2

def IRR2(ref, message=message):
    R2530 = image_get_band(ref, 2.530, message)
    R2210 = image_get_band(ref, 2.210, message)
    return R2530 / R2210

band_names = band_names + ['IRR2']

## IRR3

def IRR3(ref, message=message):
    R3750 = image_get_band(ref, 3.750, message)
    R3500 = image_get_band(ref, 3.500, message)
    return R3750 / R3500

band_names = band_names + ['IRR3']

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

band_names = band_names + ['BD1270O2']

## BD3000

def BD3000(ref, message=message):
    R3000 = image_get_band(ref, 3.000, message)
    R2530 = image_get_band(ref, 2.530, message)
    R2210 = image_get_band(ref, 2.210, message)

    return 1 - (R3000 / (R2530 * (R2530 / R2210)))

band_names = band_names + ['BD3000']

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

band_names = band_names + ['BD1400H2O']

## R2700

def R2700(ref, message=message):
    R2700 = image_get_band(ref, 2.700, message)
    return R2700

band_names = band_names + ['R2700']

## BD2700

def BD2700(ref, message=message):
    R2700 = image_get_band(ref, 2.700, message)
    R2530 = image_get_band(ref, 2.530, message)
    R2350 = image_get_band(ref, 2.350, message)

    return 1 - (R2700 / (R2530 * (R2530 / R2350)))

band_names = band_names + ['BD2700']

## D2300, Jelmer Oosthoek

def D2300(ref, message=message):
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

band_names = band_names + ['D2300']

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

band_names = band_names + ['VAR']


######################################################################
##
## Summary Products
##

def products(fin, fhull, fout, sort_wavelengths=False, use_bbl=True,
             message=message, wavelength_units=None, progress=None):

    ref = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    cr = envi2.Open(fhull, sort_wavelengths=False, use_bbl=False)

    if wavelength_units == 'Nanometers':
        ref.wavelength = array(ref.wavelength) / 1000.0
        cr.wavelength = array(cr.wavelength) / 1000.0

    im2 = envi2.New(fout, 
                          hdr=ref, interleave='bsq', bbl=None,
                          bands=len(band_names), band_names=band_names,
                          wavelength=None,
                          data_type='d')

    # Band Depths
    for i in range(len(band_depths)):
        message(band_names[i])
        im2[:,:,i] = band_depth(ref, band_depths[band_names[i]], message)

    # Olivine index
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = OLINDEX(ref, message)
    
    # Olivine index 2, Jelmer oosthoek
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = OLINDEX2(ref, message)
    
    # LCP pyroxene index
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = LCPINDEX(ref, message)

    # HCP pyroxene index
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = HCPINDEX(ref, message)

    # ISLOPE1, ferric coating on dark rock
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = ISLOPE1(ref, message)

    # DROP2300, hydrated min. particularly phyllosilicates
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = DROP2300(cr, message)

    # DROP2400, hydrated min. particularly phyllosilicates
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = DROP2400(cr, message)

    # BD3400, carbonates, organics
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BD3400(ref, message)

    # CINDEX, carbonates
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = CINDEX(ref, message)

    # RBR, rock / dust
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = RBR(ref, message)

    # SH600, select ferric minerals
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = SH600(ref, message)

    # ICER1, CO2, H2O ice mixtures
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = ICER1(ref, message)

    # BD1900, H2O
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BD1900(ref, message)

    # BD2100, monohydrated minerals
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BD2100(ref, message)

    # ICER2, CO2 ice will be >>1, H2O ice and soil will be ~1
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = ICER2(ref, message)

    # BDCARB, carbonate overtones, 2.33 and 2.53 band depth
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BDCARB(ref, message)

    # R410, clouds/haze
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = R410(ref, message)

    # R770, rock/dust
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = R770(ref, message)

    # IRA, IR albedo
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = IRA(ref, message)

    # IRR1, clouds / dust
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = IRR1(ref, message)

    # IRR2, clouds / dust
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = IRR2(ref, message)

    # IRR3, clouds / dust
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = IRR3(ref, message)

    # BD1270O2, O2 emission, inversely correlated with high altitude water, signature of ozone
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BD1270O2(ref, message)

    # BD3000
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BD3000(ref, message)

    # BD1400H2O
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BD1400H2O(ref, message)

    # R2700
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = R2700(ref, message)

    # BD2700
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = BD2700(ref, message)
    
    # D2300, Jelmer Oosthoek
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = D2300(ref, message)
    
    # VAR, keep this last!
    i = i + 1
    message(band_names[i])
    im2[:,:,i] = VAR(ref, message, progress=progress)

    del ref, cr, im2

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='summary_products.py',
##        usage='summary_products.py -s -b -f -l -i input -c continuumremoved -o output -u {mic|nan}',
        description='Summary Products, mineral and other indices.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output files')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-c', dest='cr', help='input continuum removed file name', required=True)
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

    products(options.input, options.cr, options.output,
             wavelength_units=options.units,
             sort_wavelengths=options.sort_wavelengths,
             use_bbl=options.use_bbl)
