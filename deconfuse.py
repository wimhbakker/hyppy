#!/usr/bin/python3
## deconfuse.py
##
## Copyright (C) 2021 Wim Bakker
##  Modified: 20211013 WHB created
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

import glob, os
import sys

import envi2

def print_list(l, out):
    for i, e in enumerate(l):
        if isinstance(e, float):
            e = "%.6f" % e
        if i==0:
            print(e, end='', file=out)
        else:
            print(',', e, end='', file=out)
    print(file=out)

def make_table(thedir):
    if not os.path.isdir(thedir):
        raise ValueError('Expected a directory')
    first = True
    thetable = os.path.dirname(os.path.join(thedir, '.')) + '_table.csv'
    out = open(thetable, 'w')
    for therule in sorted(glob.glob(os.path.join(thedir, '*_rule'))):
        theerror = therule.replace("_envlib_rule", "_error")
        imrule = envi2.Open(therule)
        imerror = envi2.Open(theerror)
        spectra_names = imrule.header.spectra_names
        band_names = imrule.band_names
        for line, spectra_name in enumerate(spectra_names):
            header = list()
            record = list()
            header.append("image")
            record.append(os.path.basename(therule).rsplit('_', 4)[0])
            header.append("class")
            record.append(os.path.splitext(spectra_name)[0])
            header.append("error")
            record.append(imerror[line, 0, 0])
            for band, band_name in enumerate(band_names):
                header.append(os.path.splitext(band_name)[0])
                record.append(imrule[line, 0, band])
            if first:
                print_list(header, out)
                first = False
            print_list(record, out)
        del imrule, imerror
    out.close()

# TEST
#make_table('/home/spectr/data/tobefixed/unmixed/processed_K18-06-4_200um_sub3/')
#make_table('/home/spectr/data/tobefixed/unmixed/processed_L16-14-13_200um/')

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='deconfuse.py',
        description='Get confusion matrix')

    parser.add_argument('directory', metavar='directory', type=str, nargs=1,
                        help='input directory')

    options = parser.parse_args()

    make_table(options.directory[0])
