#!/usr/bin/python3
## split.py
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
import envi2

# Try to import from Pillow or PIL
try:
    from PIL import Image
except ImportError as errtext:
    import Image

import stretch

FILE_EXT = '.jpg'

def message(s):
    pass

def split(fin, choice='JPEG', sort_wavelengths=False, use_bbl=False,
           message=message, progress=None):
    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    fbase = os.path.splitext(fin)[0]

    if progress:
        progress(0.0)
    for i in range(im.bands):
        if progress:
            progress(i / float(im.bands))
        fout = fbase + '%03d' % (i+1,) #+ FILE_EXT

        one = im.get_band(i).astype('float64')
        imout = Image.fromarray(stretch.stddev_stretch(one))
        if choice=='JPEG':
            imout.save(fout + '.jpg', 'JPEG', quality=100)
        elif choice=='TIFF':
            imout.save(fout + '.tif', 'TIFF')
        elif choice=='PNG':
            imout.save(fout + '.png', 'PNG')
        elif choice=='ENVI':
            wavelength = None
            if hasattr(im, 'wavelength'):
                wavelength = [im.wavelength[i]]

            band_names = None
            if hasattr(im, 'band_names'):
                band_names = [im.band_names[i]]

            fwhm = None
            if hasattr(im, 'fwhm'):
                fwhm = [im.fwhm[i]]

            im2 = envi2.New(fout, hdr=im, bands=1, bbl=None,
                            band_names=band_names,
                            wavelength=wavelength,
                            fwhm=fwhm, default_bands=None)
            im2[:,:,0] = im[i]
            del im2

    if progress:
        progress(1.0)

    del im

if __name__ == '__main__':
##    print "Run this module using tkSplit!"

    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='split.py',
##        usage='split.py -s -b -i input -m {ENVI|JPEG|TIFF|PNG}',
        description='Split into separate bands.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
##    parser.add_argument('-f', action='store_true', dest='force',
##                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
##    parser.add_argument('-o', dest='output', help='output file name')

    parser.add_argument('-m', dest='mode', choices=('ENVI', 'JPEG', 'TIFF', 'PNG'),
                      help='output format: ENVI, JPEG (default), TIFF, PNG', default='JPEG')

##    parser.set_defaults(sort_wavelengths=False, use_bbl=False,
##                        mode='JPEG')

    options = parser.parse_args()

##    assert options.input, "Option -i input file name required."
##    assert options.output, "Option -o output file name required."
##    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    split(options.input,
          choice=options.mode,
          sort_wavelengths=options.sort_wavelengths,
          use_bbl=options.use_bbl)
