#!/usr/bin/python3
##
##      destripe3d.py
##
##   Created:  WHB 20160304
##   Modified: WHB 20240312, added corrections for dark reference and white reference.
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
from envi2.constants import *

import numpy as np
np.seterr(all='ignore')

average_function = np.nanmean
##average_function = np.median

datatypes = ('uint8', 'int16', 'int32', 'float32', 'float64',
             'complex64', 'complex128', 'uint16', 'uint32',
             'int64', 'uint64')

def message(s):
    pass

def darkwhiteref(fin, fdark, fwhite, fout,
                 datatype='float32',
                 robust=True,
                 correct_dark=False,
                 correct_white=False,
                 message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=False, use_bbl=False)
    im2 = envi2.New(fout, hdr=im, interleave=ENVI_bsq, data_type=datatype)

    message("Reading dark image...")
    imdark = envi2.Open(fdark, sort_wavelengths=False, use_bbl=False)
    dark = average_function(imdark[...], axis=0)

    darkbias = 0

    if correct_white:
        whitepanel = 0.98 # 98% reflecting
    else:
        whitepanel = 1.00 # 100% reflecting
    message(f"White panel: {100 * whitepanel}%")

    if progress:
        progress(0.0)

    if fwhite:
        message("Reading white image...")
        imwhite = envi2.Open(fwhite, sort_wavelengths=False, use_bbl=False)

        if robust:
            message("Determine whitest 50% of white reference...")
            white = average_function(np.sort(imwhite[...], axis=0)[imwhite.lines//2:, :, :], axis=0)
        else:
            white = average_function(imwhite[...], axis=0)

        diff = white - dark

        if correct_dark:
            darkbias = diff.min()
            message(f"Dark reference bias: {darkbias}")
            
##        message("Determining target bias...")
##        if correct_dark:
##            for band in range(im.bands):
##                if progress:
##                    progress(band / float(im.bands))
##                im2[band] = im[band] - dark[np.newaxis, :, band]
##                darkbias = min(darkbias, im2[band].min())
##
##            message(f"Target bias: {darkbias}")

        message("Dark & White reference correction...")
##        im2[...] = 10000.0 * (im[...] - dark[np.newaxis, :, :]) / diff[np.newaxis, :, :]
        for band in range(im.bands):
            if progress:
                progress(band / float(im.bands))
            if 'int' in datatype:
                im2[band] = whitepanel * 10000.0 * (im[band] - dark[np.newaxis, :, band] - darkbias) / (diff[np.newaxis, :, band] - darkbias)
            else:
                im2[band] = whitepanel * (im[band] - dark[np.newaxis, :, band] - darkbias) / (diff[np.newaxis, :, band] - darkbias)

        del imwhite
    else:
        message("Dark reference correction...")
##        im2[...] = im[...] - dark[np.newaxis, :, :]
        for band in range(im.bands):
            if progress:
                progress(band / float(im.bands))
            im2[band] = im[band] - dark[np.newaxis, :, band]

            if correct_dark:
                darkbias = min(darkbias, im2[band].min())

        if correct_dark:
            message(f"Correcting target bias: {darkbias}...")
            for band in range(im.bands):
                if progress:
                    progress(band / float(im.bands))
                im2[band] = im2[band] - darkbias

    if progress:
        progress(0.0)

    del im, imdark, im2
    
if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import specim
    import sys

    parser = argparse.ArgumentParser(
        prog='darkwhiteref.py',
        description='Dark & white reference correction')

    parser.add_argument('-f', action='store_true', dest='force',
                        default=False,
                        help='force overwrite on existing output file')
    parser.add_argument('-m', dest='manifest', help='manifest xml file name')
    parser.add_argument('-i', dest='input', help='input file name')
    parser.add_argument('-d', dest='darkref', help='dark reference file name')
    parser.add_argument('-w', dest='whiteref', help='white reference file name')
    parser.add_argument('-o', dest='output', help='output file name')
    parser.add_argument('-t', dest='datatype', help='output data type (default float32)',
                        choices=datatypes, default='float32')
    parser.add_argument('-r', action='store_true', dest='robust',
                        default=True,
                        help='robust white reference')

    ns = parser.parse_args()

    assert ns.manifest or (ns.input and ns.output), "Requires either manifest, or input and output"

    if ns.manifest:
        inputdir = os.path.dirname(ns.manifest)

        manifest = specim.get_manifest(ns.manifest)
        darkref = getattr(manifest, 'darkref', '')
        whiteref = getattr(manifest, 'whiteref', '')
        capture = getattr(manifest, 'capture', '')

        if capture:
            capture = os.path.join(inputdir, capture)
        if darkref:
            darkref = os.path.join(inputdir, darkref)
        if whiteref:
            whiteref = os.path.join(inputdir, whiteref)

        output = os.path.join(inputdir, os.path.splitext(os.path.basename(capture))[0] + '_refl.dat')

        # check for overriding options...
        if ns.input:
            capture = ns.input
        if ns.darkref:
            darkref = ns.darkref
        if ns.whiteref:
            whiteref = ns.whiteref
        if ns.output:
            output = ns.output

        assert ns.force or not os.path.exists(output), "Output file exists. Use -f to overwrite."
        darkwhiteref(capture, darkref, whiteref, output, robust=ns.robust, datatype=ns.datatype)
    else:
        assert ns.force or not os.path.exists(ns.output), "Output file exists. Use -f to overwrite."
        darkwhiteref(ns.input, ns.darkref, ns.whiteref, ns.output, robust=ns.robust, datatype=ns.datatype)

    sys.exit(0)
