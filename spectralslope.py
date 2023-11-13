#!/usr/bin/python3
## minwavelength2.py
##
## Copyright (C) 2018 Wim Bakker
##  Modified: 201804.. WHB major revision
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
import spectrum

import numpy

BAND_NAMES = ['curvature', 'slope', 'offset']

def message(s):
    pass

def spectralslope(nameIn, nameOut, startwav=None, endwav=None,
                  message=message, sort_wavelengths=True,
                  use_bbl=True, progress=None,
                  fitorder=1):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples

    # set up output ENVI image
    im2 = envi2.New(nameOut, value=numpy.nan,
                     hdr=envi2.Header(hdr=im.header,
                                      bands=fitorder+1,
                                      data_type='d',
                                     band_names=BAND_NAMES[2-fitorder:], wavelength=None,
                                     fwhm=None, bbl=None))

    startband = im.wavelength2index(startwav)
    endband = im.wavelength2index(endwav) + 1 # modified to include the endwav
    wavs = im.wavelength[startband:endband]

##    # create a spectral subset view on the image
##    imsub = im[:, :, startband:endband]

    # go for it!
    if progress:
        progress(0.0)
    for j in range(lines):
        if progress:
            progress(j / float(lines))
        for i in range(samples):
            S = spectrum.Spectrum(wavelength=wavs, spectrum=im[j, i, startband:endband])

            c = numpy.polyfit(S.w, S.s, fitorder)

            im2[j, i, 0] = c[0]
            im2[j, i, 1] = c[1]
            if fitorder==2:
                im2[j, i, 2] = c[2]
                

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='spectralslope.py',
        description='Determine Spectral slope between start and end wavelength')

    parser.add_argument('-b', action='store_true', dest='use_bbl', help='use bad band list')
    parser.add_argument('-f', action='store_true', dest='force', help='force overwrite of output file')
    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-o', dest='output', required=True, help='ouput file')
    parser.add_argument('-w', dest='start', type=float, required=True, help='starting wavelength (float)')
    parser.add_argument('-W', dest='end', type=float, required=True, help='ending wavelength (float)')
    parser.add_argument('-n', dest='fitorder', choices=(1, 2), type=int, default=1, help='fitting order (1, 2)')

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use option -f to overwrite.")

    spectralslope(options.input, options.output,
                  startwav=options.start, endwav=options.end,
                  sort_wavelengths=True,
                  use_bbl=options.use_bbl,
                  fitorder=options.fitorder)

    sys.exit(0)
