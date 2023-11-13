#!/usr/bin/python3
## converthdf.py
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

import os, sys

from osgeo import gdal
gdal.UseExceptions()

##sys.path.append('/home/bakker/Python/HypPy3')
import envi2
from envi2.constants import * 

def message(s):
    print(s)

def converthdf(f, baseout, message=message, progress=None):
    ds = gdal.Open(f)

    subs = ds.GetSubDatasets()

    i = 0
    n = float(len(subs))
        
    for fname, fmeta in subs:
        i = i + 1
        if progress:
            progress(i / n)
        
        if 'EOS_SWATH' in fname:
            message(fname)
            message(fmeta)
            fmetasplit = fmeta.split()
            bandname = fmetasplit[1]
            setname = fmetasplit[2]
            fout = '_'.join([baseout, bandname, setname])
            message(fout)
            
            a = gdal.Open(fname).ReadAsArray()
            message(str(a.shape))
            message(str(a.dtype))
            message('\n')
            a.tofile(fout)

            h = envi2.header.Header(
                file_type = ENVI_Standard,
                description = [os.path.basename(f)],
                samples = a.shape[1],
                lines = a.shape[0],
                bands = 1,
                band_names = [bandname],
                data_type = a.dtype,
                interleave = ENVI_BSQ,
                byte_order = 0 if sys.byteorder == 'little' else 1)
            h.write(fout)

##convert_hdf("/data2/data/Aster/AST_L1T_00305112016104003_20160512094027_20237.hdf",
##        "/data2/data/Aster/AST_L1T_00305112016104003_20160512094027_20237")

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='converthdf.py',
        description='Convert OES HDF image to ENVI format.')

    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    options = parser.parse_args()

##    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    converthdf(options.input, options.output)
