#!/usr/bin/python3
## classstats.py
##
## Copyright (C) 2018 Wim Bakker
##      Created: WHB 20181004
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
import envi2.constants

import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import ascspeclib
import warnings

# for testing...
def main():
    pass

def classstats(inname=None, classname=None, output=None, speclib=None, report=None,
               TeXreport=None,
               sort_wavelengths=False, use_bbl=False):
    imclass = envi2.Open(classname, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    if hasattr(imclass.header, 'spectra_names'):
        f = open(classname+'_specclass', 'w')
        for j in range(imclass.lines):
            print("\"%s\" \"%s\"" % (imclass.header.spectra_names[j], imclass.header.class_names[imclass[j,0,0]]), file=f)
        f.close()

    f = open(classname+'_classcount', 'w')                                                   
    classcount = dict()
    for c in range(imclass.header.classes):
        isthisclass = imclass[0]==c
        count = isthisclass.sum()
        myclassname = imclass.header.class_names[c]
        myclassname = myclassname if myclassname else 'Unclassified'

        if count:
            classcount[myclassname] = count
            print("\"%s\"" % (myclassname,), count, end='', file=f)

            if hasattr(imclass.header, 'spectra_names'):
                y, x = isthisclass.nonzero()
                for spectra_name in np.array(imclass.header.spectra_names)[y]:
                    print(" \"%s\"" % (spectra_name,), end='', file=f)                
            print(file=f)
    f.close()

    if inname:
        im = envi2.Open(inname, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
        imcopy = im[...].copy()

        f = plt.figure(figsize=(12, 9))

        speclist = list()
        for c in range(imclass.header.classes):
            isthisclass = imclass[0]==c
            count = isthisclass.sum()
            myclassname = imclass.header.class_names[c]
            myclassname = myclassname if myclassname else 'Unclassified'

            if count:
                color = (imclass.header.class_lookup[3*c+0]/255, imclass.header.class_lookup[3*c+1]/255, imclass.header.class_lookup[3*c+2]/255)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", category=RuntimeWarning)
                    avspec = np.nanmean(np.where(isthisclass[:,:,np.newaxis], imcopy, np.nan), axis=(0, 1))
                plt.plot(im.wavelength, avspec, label=myclassname, color=color)
                speclist.append(ascspeclib.Spectrum(name=myclassname, wavelength=im.wavelength,
                                         spectrum=avspec, description='Average class spectrum'))

        plt.legend(fontsize=8, loc=2)
        plt.title('Mean spectrum per class')
        plt.xlabel('wavelength')
        plt.ylabel('value')
        xmin, xmax, ymin, ymax = plt.axis()
        plt.axis([xmin, xmax, max(0, ymin), min(1, ymax)]) # keep y-axis between 0 and 1...
        
        if output:
            plt.savefig(output)
            print('Plot "%s" generated' % (output,))

        if speclib:
            thelib = ascspeclib.AscSpeclib(speclist)
            # make sure the directory is there...
            os.makedirs(speclib, exist_ok=True)
            thelib.save(speclib)
            print('Spectral library "%s" generated' % (speclib,))

    if report:
        f = open(report, 'w')
        if inname:
            f.write('# image file: %s\n' % (inname,))
        f.write('# class file: %s\n' % (classname,))
        f.write('# originally: %d classes\n' % (imclass.header.classes,))
        f.write('#  remaining: %d classes\n' % (len(classcount),))
        f.write('# %18s %10s %6s\n' % ('class', 'count', 'pct'))
        for cname, ccount in sorted(classcount.items(), key=lambda x:x[1], reverse=True):
            f.write("%20s %10d %5.1f%%\n" % (cname, ccount, 100*ccount/(imclass.samples*imclass.lines),))
        f.close()
        print('Text report "%s" generated' % (report,))

    if TeXreport:
        f = open(TeXreport, 'w')
        f.write('\\documentclass[10pt]{article}\n')
        f.write('\\begin{document}\n')
        f.write('\\section*{Class report}\n')

        trans = str.maketrans({'_':'\\_'})
        if inname:
            f.write('\\# image file: %s\n\n' % (inname.translate(trans),))
        f.write('\\noindent\n\\# class file: %s\n\n' % (classname.translate(trans),))
        f.write('\\noindent\n\\# originally: %d classes\n\n' % (imclass.header.classes,))
        f.write('\\noindent\n\\#  remaining: %d classes\n\n' % (len(classcount),))
        f.write('\\noindent\n\\begin{tabular}{lrr}\n')
        f.write('\\# %18s & %10s & %6s \\\\\n' % ('class', 'count', 'pct'))
        for cname, ccount in sorted(classcount.items(), key=lambda x:x[1], reverse=True):
            f.write("%20s & %10d & %5.1f\\%% \\\\\n" % (cname.translate(trans), ccount, 100*ccount/(imclass.samples*imclass.lines),))
        f.write('\\end{tabular}\n')
        f.write('\\end{document}\n')
        f.close()
        print('LaTeX report "%s" generated' % (TeXreport,))
    
if __name__=='__main__':
##    main()
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='classstats.py',
        description='Get class statistics.')

    parser.add_argument('-c', dest='classname', help='input ENVI classification file', required=True)
    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-i', dest='input', help='input ENVI image', required=False)
    parser.add_argument('-o', dest='output', help='output plot file (.png or .pdf)', required=False)
    parser.add_argument('-l', dest='speclib', help='output directory for ascii spectral library', required=False)
    parser.add_argument('-r', dest='report', help='output report (text file)', required=False)
    parser.add_argument('-t', dest='TeXreport', help='output report (LaTeX file)', required=False)

    options = parser.parse_args()

    classstats(inname=options.input, classname=options.classname,
               output=options.output,
               speclib=options.speclib, report=options.report,
               TeXreport=options.TeXreport,
               sort_wavelengths=options.sort_wavelengths,
               use_bbl=options.use_bbl)
