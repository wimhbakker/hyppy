#!/usr/bin/python3
## deconfuse_plot.py
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

# Each speclib contains three spectra:
#/home/spectr/data/tobefixed/unmixed/processed_K18-06-4_200um_sub3/K18-06-4_200um_sub3_albedo_class_speclib_estimate
#/home/spectr/data/tobefixed/processed_K18-06-4_200um_sub3/K18-06-4_200um_sub3_albedo_class_speclib/

import glob, os

import envi2
import ascspeclib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pylab as plt

def make_plot(s1, s2, theplot):
    plt.plot(s1.wavelength, s1.spectrum, label="original")
    plt.plot(s2.wavelength, s2.spectrum, label="estimate")
    plt.xlabel("wavelength")
    plt.ylabel("spectrum")
    plt.title(os.path.splitext(s1.name)[0])
    plt.legend()
    plt.savefig(theplot)
    plt.clf()

def make_plots(thedir):
    if not os.path.isdir(thedir):
        raise ValueError('Expected a directory')
    
    thedir = os.path.dirname(os.path.join(thedir, '.'))
    theplots = os.path.join(thedir, "plots")
    if not os.path.exists(theplots):
#        print("creating:", theplots)
        os.mkdir(theplots)

    for theimage in sorted(glob.glob(os.path.join(thedir, 'processed_*'))):
        theimagebase = os.path.basename(theimage)
#        print(theimage)
        for theclasssl in sorted(glob.glob(os.path.join(theimage, '*_class_speclib'))):
            theclassslbase = os.path.basename(theclasssl)
#            print(theclasssl)
            classsl = ascspeclib.AscSpeclib(theclasssl)
            theestimate = os.path.join(thedir, "unmixed", theimagebase, theclassslbase) + '_estimate'
#            print(theestimate)
            estimatesl = ascspeclib.AscSpeclib(theestimate)
            for class_spec in classsl:
                thespecname = class_spec.name
#                print(thespecname)
                # find corresponding estimate...
                estimate_spec = estimatesl[thespecname]
                theplot = os.path.join(theplots, theimagebase + "_" + theclassslbase + "_" + os.path.splitext(thespecname)[0] + ".jpg")
#                print(theplot)
                make_plot(class_spec, estimate_spec, theplot)
                
#make_plots('/home/spectr/data/tobefixed/')

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='deconfuse_plot.py',
        description='Get plots')

    parser.add_argument('directory', metavar='directory', type=str, nargs=1,
                        help='input directory')

    options = parser.parse_args()

    make_plots(options.directory[0])
