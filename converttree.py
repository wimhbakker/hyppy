#!/usr/bin/python3
## converttree.py
##
## Copyright (C) 2021 Wim Bakker
##  Created:  20210304 WHB
##  Modified: 
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

import decisiontree as dt

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='converttree.py',
        description='Convert ENVI or ASCII Decision Tree to ASCII Decision Tree or dot graph')

    parser.add_argument('-f', action='store_true', dest='force', help='force overwrite of output file')
    parser.add_argument('-d', action='store_true', dest='dot', help='convert tree to dot graph')
    parser.add_argument('-i', dest='input', required=True, help='input tree')
    parser.add_argument('-o', dest='output', required=True, help='ouput tree')

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use option -f to overwrite.")

    dt.converttree(options.input, options.output, dot=options.dot)

    sys.exit(0)
