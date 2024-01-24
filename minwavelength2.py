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

BAND_NAMES = ['interpolated min. wav.',   'interpolated depth',
              'interpolated min. wav. 2', 'interpolated depth 2',
              'interpolated min. wav. 3', 'interpolated depth 3',
              'interpolated min. wav. 4', 'interpolated depth 4',
              'interpolated min. wav. 5', 'interpolated depth 5',
              'interpolated min. wav. 6', 'interpolated depth 6',
              'interpolated min. wav. 7', 'interpolated depth 7',
              'interpolated min. wav. 8', 'interpolated depth 8',
              'interpolated min. wav. 9', 'interpolated depth 9'
              ]

def message(s):
    pass

def minwavelength(nameIn, nameOut, maskfile=None, mode='div',
                  startwav=None, endwav=None,
                  message=message, sort_wavelengths=True,
                  use_bbl=True, progress=None, broad=False,
                  numfeatures=1):
    # get ENVI image data
    im = envi2.Open(nameIn, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    lines = im.lines
    samples = im.samples

    mask = None
    if maskfile:
        mask = envi2.Open(maskfile)
        assert mask.lines==lines and mask.samples==samples, "Mask extent must match image extent."

    # set up output ENVI image
    im2 = envi2.New(nameOut, value=numpy.nan,
                     hdr=envi2.Header(hdr=im.header,
                                      bands=numfeatures*2,
                                      data_type='d',
                                     band_names=BAND_NAMES[:numfeatures*2], wavelength=None,
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
            if not mask or mask[j, i, 0]:
                S = spectrum.Spectrum(wavelength=wavs, spectrum=im[j, i, startband:endband])

                minwavs = sorted(S.minwav(numfeatures, mode=mode, broad=broad).tuple(), key=lambda x:x[1], reverse=True)
                for k in range(len(minwavs)):
                    im2[j, i, 2*k]   = minwavs[k][0]
                    im2[j, i, 2*k+1] = minwavs[k][1]

    if progress:
        progress(1.0)

    # destroy resources
    del im2, im

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='minwavelength2.py',
        description='Determine interpolated wavelength of minimum and depth of the deepest absorption features')

    parser.add_argument('--broad', action='store_true', dest='broad', help='use broad feature fitting')
    parser.add_argument('-b', action='store_true', dest='use_bbl', help='use bad band list')
    parser.add_argument('-f', action='store_true', dest='force', help='force overwrite of output file')
    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-o', dest='output', required=True, help='ouput file')
    parser.add_argument('--mask', dest='maskfile', required=False, help='mask file (optional)')
    parser.add_argument('-w', dest='start', type=float, required=True, help='starting wavelength (float)')
    parser.add_argument('-W', dest='end', type=float, required=True, help='ending wavelength (float)')
    parser.add_argument('-m', dest='mode', choices=('div', 'sub', 'none'), default='div', help='mode: division or subtraction (default: div)')
    parser.add_argument('-n', dest='numfeatures', choices=(1, 2, 3, 4, 5, 6, 7, 8, 9), type=int, default=1, help='number of features to match (default: 1)')

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use option -f to overwrite.")

    minwavelength(options.input, options.output,
                  maskfile=options.maskfile,
                  mode=options.mode,
                  startwav=options.start, endwav=options.end,
                  sort_wavelengths=True,
                  use_bbl=options.use_bbl, broad=options.broad,
                  numfeatures=options.numfeatures)

    sys.exit(0)
