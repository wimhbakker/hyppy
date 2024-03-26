#!/usr/bin/python3
## scatterplot.py
##
## Copyright (C) 2011 Wim Bakker
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
from pylab import *
ion()

def message(s):
    pass

def scatterplot(fin, xband, yband, yfin=None,
                fout=None,
                xmin=None, xmax=None, ymin=None, ymax=None,
                markersize=1,
          sort_wavelengths=True, use_bbl=True,
           message=message):
    if fout:
        import matplotlib
        matplotlib.use('Agg')

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    if yfin:
        yim = envi2.Open(yfin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    else:
        yim = im

    xtext = "band %d" % (xband,)
    ytext = "band %d" % (yband,)

    if hasattr(im, 'band_names'):
        xtext = str(im.band_names[xband])
        ytext = str(yim.band_names[yband])

    if hasattr(im, 'wavelength'):
        xtext = 'wavelength %.4f $\\mu$m' % (im.wavelength[xband],)
        ytext = 'wavelength %.4f $\\mu$m' % (yim.wavelength[yband],)

    x = im[xband]
    y = yim[yband]

    figure(figsize=(8, 8))
    plot(x, y, '.', color='grey', markersize=markersize)

    xlabel(xtext)
    ylabel(ytext)
    if yfin:
        title('Scatterplot: X=%s, Y=%s' % (os.path.basename(fin), os.path.basename(yfin)))
    else:
        title('Scatterplot: %s' % (os.path.basename(fin),))
##    legend(loc=0)
    if xmin and xmax and ymin and ymax:
        axis([float(xmin), float(xmax), float(ymin), float(ymax)])
    else:
        axis('equal')
    draw()

    if fout:
        savefig(fout)
        message("Scatterplot saved to %s\n" % (fout,))
        
    message('\n')

    del im

if __name__ == '__main__':
##    splot('/data/tmp/4604/ORB4604_5_jdat_Scor', '/data/tmp/4604/ORB4604_5_mola')
##    splot('/data/tmp/0422/ORB0422_4_jdat_Scor', 137, 157)
##    splot('/data/tmp/0422/ORB0422_4_jdat_Gcor_sub_Scor_Acor_lr_med_wav', 1, 2)
    # command line version
    import optparse
    import os

    parser = optparse.OptionParser(
        usage='scatterplot.py -s -b -i input -x x-axis -y y-axis',
        description='Make scatterplot.')

    parser.add_option('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_option('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_option('-i', dest='input', help='x-axis input file name')
    parser.add_option('-j', dest='yinput', help='y-axis input file name')
    parser.add_option('-o', dest='output', help='output file name (add .pdf .png ...)')

    parser.add_option('-x', dest='xband', type='int',
                      help='band for x-axis (starts at 0)')
    parser.add_option('-y', dest='yband', type='int',
                      help='band for y-axis (starts at 0)')

    parser.set_defaults(sort_wavelengths=False, use_bbl=False)

    (options, args) = parser.parse_args()

    assert options.input, "Option -i input file name required."
    assert options.xband is not None, "Option -x band for x-axis required."
    assert options.yband is not None, "Option -y band for y-axis required."

    scatterplot(options.input, options.xband, options.yband,
                yfin=options.yinput,
                fout=options.output,
              sort_wavelengths=options.sort_wavelengths,
              use_bbl=options.use_bbl)

    #show()
