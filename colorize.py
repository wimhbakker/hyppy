#!/usr/bin/python3
## colorize.py
##
## Copyright (C) 2010 Wim Bakker
##    Modified: 20151022 WHB, to match the behavior of wavmap
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
import math
import colorsys
import numpy

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import stretch

##from scipy.stats.stats import nanmean, nanstd
##from numpy import zeros, newaxis, polyfit, poly1d

##from pylab import plot

def message(s):
    pass

def do_stretch(b, min_, max_):
    return (255.99*(b-min_)/(max_-min_)).clip(0, 255).astype('u1')

def spiral2():
    """rainbow plus brightness steps"""
    result = []
    result.append([1.0, 1.0, 1.0])
    for i in range(1, 255):
        h = (0.9 * (1 - i / 255.0) - 0.2) % 1.0
        v = 0.3 + 0.4 * ((i%16)/15.0)
        s = 1 - 0.5 * math.sqrt(i / 255.0)
        r, g, b = colorsys.hls_to_rgb(h, v, s)
        result.append([r, g, b])
    result.append([1.0, 1.0, 1.0])
    return result

def spiral3():
    """rainbow from blue to magenta"""
    result = []
    result.append([1.0, 1.0, 1.0])
    for i in range(1, 255):
        h = (0.9 * (1 - i / 255.0) - 0.22) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
        r = math.pow(r, 0.6)
        g = math.pow(g, 0.6)
        b = math.pow(b, 0.6)
        result.append([r, g, b])
    result.append([1.0, 1.0, 1.0])
    return result

palette_spiral2 = spiral2()
palette_spiral3 = spiral3()

SEPARATORS = ',;:'

def read_color_table(name):
    f = open(name)
    data = f.readlines()
    f.close()
    result = []
    for line in data:
        elems = line.strip().split()
        try:
            r = int(elems[0].rstrip(SEPARATORS)) / 255.0
            g = int(elems[1].rstrip(SEPARATORS)) / 255.0
            b = int(elems[2].rstrip(SEPARATORS)) / 255.0
            result.append([r, g, b])
        except:
            pass
    if len(result)!=256:
        raise ValueError("color table doesn't have 256 entries")
    return result

def hsv_merge(r, g, b, v):
    h, s, v_old = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return r, g, b

def create_legend(palette):
    result = numpy.zeros((256, 256, 3), dtype=numpy.float32)
    for j in range(256):
        for i in range(256):
            r, g, b = palette[i]
            v = j / 255.0
            r, g, b = hsv_merge(r, g, b, v)
            result[j, i, :] = r, g, b
    return result

def save_legend(palette, w0, w1, d0, d1, name,
                xlabel='Color', ylabel='Intensity'):
    l = create_legend(palette)
    plt.imshow(l, origin='lower', extent=(w0, w1, d0, d1), aspect='auto')
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title('HSV merged Color and Intensity')
    plt.savefig(name)

def save_legend_vertical(palette, w0, w1, d0, d1, name):
    d0, d1 = 100*d0, 100*d1
    l = create_legend(palette).transpose((1,0,2))

    plt.rc("xtick", direction="out")
    plt.rc("ytick", direction="out")

    f = plt.figure(figsize=(4.1,6.3))
    plt.imshow(l, origin='lower', extent=(d0, d1, w0, w1), aspect=2.0*(d1-d0)/(w1-w0))

##    ax = plt.gca()
##    for label in ax.get_xticklabels():
##        label.set_fontsize(20)
##    for label in ax.get_yticklabels():
##        label.set_fontsize(20)

    fontsize = 16
    
    yax = f.axes[0].get_yaxis()
##    yax.set_label_position('right')
    for tick in yax.get_major_ticks():
        tick.label1On = False
        tick.label2On = True
        tick.label2.set_fontsize(fontsize)

    xax = f.axes[0].get_xaxis()
    xax.set_label_position('bottom')
    for tick in xax.get_major_ticks():
        tick.label1On = True
        tick.label2On = False
        tick.label1.set_fontsize(fontsize)

    # get around font manager problem for old versions... *sigh*
    if matplotlib.__version__ < '0.99.3':
        plt.ylabel('Wavelength (%s)' % ('micron' if w1<100 else 'nm',),
                   fontsize=20, labelpad=15)
    else:
        plt.ylabel('Wavelength (%s)' % (r'$\mu$m' if w1<100 else 'nm',),
                   fontsize=20, labelpad=15)
        
    plt.xlabel('Depth (%)', fontsize=20)

##    plt.title('Legend', fontsize=32)
    
##    plt.xticks((d0, (d0+d1)/2, d1))
##    plt.yticks((w0, (w0+w1)/2, w1))
    
    plt.savefig(name)

def colorize(fincol, finint, fout,
             band1=0, band2=0,
             stretchcol1=0.0, stretchcol2=255.0,
             stretchint1=0.0, stretchint2=255.0,
             colortable='rainbow', colorfile=None,
             createlegend=False,
             sort_wavelengths=False, use_bbl=False,
             message=message, progress=None):

    imcol = envi2.Open(fincol, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)
    imint = envi2.Open(finint, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

##    if not 'wavelength' in im.band_names[0]:
##        message("No wavelength band found!")
##        return

    im2 = envi2.New(fout, hdr=imcol, interleave='bsq', bands=3, # data_type='u1',
                    band_names=['R', 'G', 'B'], default_bands=[1, 2, 3],
                    wavelength=None, bbl=None,
                    fwhm=None)

    # get interpolated wavelength and depth
    bcol = do_stretch(imcol[band1], stretchcol1, stretchcol2)
    if stretchint2 is None or stretchint2==stretchint1:
        bint, stretchint1, stretchint2 = stretch.percent_percent_stretch(imint[band2], 0.30, 0.95)
        message('Automatic depth stretch: %f, %f' % (stretchint1, stretchint2))
    else:
        bint = do_stretch(imint[band2], stretchint1, stretchint2)

    if colorfile:
        palette = read_color_table(colorfile)
    elif colortable=='rainbow':
        palette = palette_spiral3
    else:
        palette = palette_spiral2

    if progress:
        progress(0.0)
    for j in range(imcol.lines):
        if progress:
            progress(j / float(imcol.lines))
        for i in range(imcol.samples):
            if numpy.isnan(imcol[j, i, band1]) or numpy.isnan(imint[j, i, band2]):
                im2[j, i, 0] = numpy.NaN
                im2[j, i, 1] = numpy.NaN
                im2[j, i, 2] = numpy.NaN
            else:
                r, g, b = palette[bcol[j, i]]
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                v = bint[j, i] / 255.0
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                im2[j, i, 0] = int(255*r)
                im2[j, i, 1] = int(255*g)
                im2[j, i, 2] = int(255*b)

    if progress:
        progress(1.0)

    del imcol, imint, im2

    if createlegend:
##        save_legend(palette, stretchcol1, stretchcol2, stretchint1, stretchint2,
##                    fout + '_legend.png',
##                    xlabel='Color: %s[%d]' % (fincol, band1),
##                    ylabel='Intensity: %s[%d]' % (finint, band2))
        save_legend_vertical(palette, stretchcol1, stretchcol2, stretchint1, stretchint2,
                    fout + '_legend.pdf')
        save_legend_vertical(palette, stretchcol1, stretchcol2, stretchint1, stretchint2,
                    fout + '_legend.png')
        message('Legend saved.')

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='colorize.py',
##        usage='colorize.py -s -b -f -i input1 -j input2 -I band1 -J band2 -o output -w startcol -W endcol -d startint -D endint -c {rainbow|steps} -C colorfile -l',
        description='Make color/intensity map using color table and HSV transform')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input1', help='input file name for color', required=True)
    parser.add_argument('-j', dest='input2', help='input file name for intensity', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-I', dest='band1', type=int, default=0,
                      help='input band for color')
    parser.add_argument('-J', dest='band2', type=int, default=0,
                      help='input band for intensity')

    parser.add_argument('-w', dest='wstart', type=float,
                      help='lower stretch value for color', required=True)
    parser.add_argument('-W', dest='wend', type=float,
                      help='upper stretch value for color', required=True)
    parser.add_argument('-d', dest='dstart', type=float,
                      help='lower stretch value for intensity', required=True)
    parser.add_argument('-D', dest='dend', type=float,
                      help='upper stretch value for intensity', required=True)
    parser.add_argument('-c', dest='colortable', choices=['rainbow', 'steps'], default='rainbow',
                      help='color table: rainbow (default) or steps')
    parser.add_argument('-C', dest='colorfile', help='input color table file')
    parser.add_argument('-l', action='store_true', dest='createlegend',
                      help='save legend in a .png file')

##    parser.set_defaults(force=False, colortable='rainbow',
##                        createlegend=False, band1=0, band2=0,
##                        sort_wavelengths=False, use_bbl=False)

    options = parser.parse_args()

##    assert options.input1, "Option -i input file name required."
##    assert options.input2, "Option -j input file name required."
##    assert options.output, "Option -o output file name required."
##    assert options.wstart is not None, "Option -w starting value required."
##    assert options.wend is not None, "Option -W ending value required."
##    assert options.dstart is not None, "Option -d starting value required."
##    assert options.dend is not None, "Option -D ending value required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    colorize(options.input1, options.input2, options.output,
            band1=options.band1, band2=options.band2,
            stretchcol1=options.wstart, stretchcol2=options.wend,
            stretchint1=options.dstart, stretchint2=options.dend,
            colortable=options.colortable, colorfile=options.colorfile,
            createlegend=options.createlegend,
            sort_wavelengths=options.sort_wavelengths,
            use_bbl=options.use_bbl)
