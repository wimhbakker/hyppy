#!/usr/bin/python3
## minwavelength.py
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

# load support for ENVI images
import envi2
from quickhull2d import hull_resampled
from numpy import array, nanmin, nanmax, where, isnan, seterr, isfinite, nan

##from scipy.stats.stats import nanmean, nanstd
from numpy import nanmean, nanstd
from scipy.optimize import leastsq

INTERPOLATE_ALL = True

if INTERPOLATE_ALL:
    BAND_NAMES = ['minimum wavelength',
                  'interpolated min. wav.', 'interpolated depth', 'interpolated narrowness',
                  'wavelength of 1st local min', 'depth of 1st local min',
                  'int wav of local min 1', 'int depth of local min 1', 'int narrowness of local min 1',
                  'wavelength of 2nd local min', 'depth of 2nd local min',
                  'int wav of local min 2', 'int depth of local min 2', 'int narrowness of local min 2',
                  'wavelength of 3rd local min', 'depth of 3rd local min',
                  'int wav of local min 3', 'int depth of local min 3', 'int narrowness of local min 3'
                  ]
else:
    BAND_NAMES = ['minimum wavelength', 'interpolated min. wav.', 'interpolated depth',
                  'interpolated narrowness',
                  'wavelength of 1st local min', 'depth of 1st local min',
                  'wavelength of 2nd local min', 'depth of 2nd local min',
                  'wavelength of 3rd local min', 'depth of 3rd local min']

def model(params, x):
    a, b, c = params
    return a*x*x+b*x+c

def residuals(p, y, x):
    return y - model(p, x)

def fit_parabola(x, y):
    params = leastsq(residuals, [1, 1, 1], args=(y, x))[0]
    a, b, c = params
    
    zx = -b / (2*a)
    zy = model(params, zx)

    depth = zy

    return ((zx, zy), (a, b, c))

def localminima(y, x, band):
    result = []
    for i in range(1, len(y)-1):
        if y[i] < y[i-1] and y[i] < y[i+1]:
            result.append((y[i], x[i], band[i]))
    return sorted(result)

def message(s):
    pass

def minwavelength(nameIn, nameOut, maskfile=None, mode='div',
                  startwav=None, endwav=None,
                  message=message, sort_wavelengths=True,
                  use_bbl=True, progress=None):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples

    mask = None
    if maskfile:
        mask = envi2.Open(maskfile)
        assert mask.lines==lines and mask.samples==samples, "Mask extent must match image extent."

    # set up output ENVI image
    im2 = envi2.New(nameOut, value=nan,
                     hdr=envi2.Header(hdr=im.header, bands=len(BAND_NAMES),
                                      data_type='d',
                                     band_names=BAND_NAMES, wavelength=None,
                                     fwhm=None, bbl=None))

    # set mode
#    mode_is_div = mode.lower() == 'div'

    startband = im.wavelength2index(startwav)
    endband = im.wavelength2index(endwav) + 1 # modified to include the endwav
    wavs = im.wavelength[startband:endband]

    oldsettings = seterr(all='ignore')

    # go for it!
    if progress:
        progress(0.0)
    for j in range(lines):
        if progress:
            progress(j / float(lines))
        for i in range(samples):
          if not mask or mask[j, i, 0]:
            spec = im[j, i][startband:endband]
            if isfinite(spec).all():
                spec_hull = hull_resampled(array(list(zip(wavs, spec))))[:,1]
                if mode.lower()=='div':
                    hull_removed = spec / spec_hull
                elif mode.lower()=='sub':
                    hull_removed = 1 + (spec - spec_hull)
                else:
                    hull_removed = spec

                # find minimum and store wavelength of minimum
                miny, minx, minband = sorted(zip(hull_removed, wavs, list(range(len(wavs)))))[0]
                im2[j,i,0] = minx

                # fit parabola and retrieve useful parameters
                if minband==0 or minband==len(wavs)-1:
                    zx, zy = minx, miny
                    a = 0
                else:
                    x = array([wavs[minband-1] , minx, wavs[minband+1]])
                    y = array([hull_removed[minband-1] , miny, hull_removed[minband+1]])
                    (zx, zy), (a, b, c) = fit_parabola(x, y)

                im2[j, i, 1] = zx
                im2[j, i, 2] = 1-zy
                im2[j, i, 3] = a

                nextband = 4

                # determine wavelength and depth of the first three local minima...
                for y1, x1, b1 in localminima(hull_removed, wavs, list(range(len(wavs))))[:3]:
                    im2[j, i, nextband] = x1
                    nextband = nextband + 1
                    im2[j, i, nextband] = 1 - y1
                    nextband = nextband + 1
                    if INTERPOLATE_ALL:
                        x = array([wavs[b1-1] , x1, wavs[b1+1]])
                        y = array([hull_removed[b1-1] , y1, hull_removed[b1+1]])
                        (zx, zy), (a, b, c) = fit_parabola(x, y)

                        im2[j, i, nextband] = zx
                        nextband = nextband + 1
                        im2[j, i, nextband] = 1-zy
                        nextband = nextband + 1
                        im2[j, i, nextband] = a
                        nextband = nextband + 1

    if progress:
        progress(1.0)

    seterr(**oldsettings)

    # destroy resources
    del im2, im

if __name__ == '__main__':
##    print "Run this module using tkMinWavelength!"
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='minwavelength.py',
##        usage='minwavelength.py -b -f -i input -o output -m {div|sub|none} -w startwav -W endwav',
        description='Determine wavelength of minimum, depth narrowness plus interpolation of deepest three features')

##    parser.add_argument('-s', action='store_true', dest='sort_wavelengths')
    parser.add_argument('-b', action='store_true', dest='use_bbl', help='use bad band list')
    parser.add_argument('-f', action='store_true', dest='force', help='force overwrite of output file')
    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-o', dest='output', required=True, help='ouput file')
    parser.add_argument('-w', dest='start', type=float, required=True, help='starting wavelength (float)')
    parser.add_argument('-W', dest='end', type=float, required=True, help='ending wavelength (float)')
    parser.add_argument('-m', dest='mode', choices=('div', 'sub', 'none'), default='div', help='mode: division or subtraction')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
##                        mode='div')

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
##    assert options.start is not None, "Option -w starting wavelength required."
##    assert options.end is not None, "Option -W ending wavelength required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    minwavelength(options.input, options.output,
                  mode=options.mode,
                  startwav=options.start, endwav=options.end,
                  sort_wavelengths=True,
                  use_bbl=options.use_bbl)
