#!/usr/bin/python3
## wavemap.py
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

# band numbers of interpolated wavelength and depth in minimum wavelength file
INTERPOLATED_WAVELENGTH = 1
INTERPOLATED_DEPTH = 2

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
        r = math.pow(r, 0.7)
        g = math.pow(g, 0.7)
        b = math.pow(b, 0.7)
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
        raise IOError("color table doesn't have 256 entries")
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

def save_legend(palette, w0, w1, d0, d1, name):
    l = create_legend(palette)
    plt.imshow(l, origin='lower', extent=(w0, w1, d0, d1), aspect='auto')
    plt.xlabel('Wavelength')
    plt.ylabel('Depth')
    plt.title('Legend: HSV fused Wavelength and Depth')
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
    yax.set_label_position('left')
    for tick in yax.get_major_ticks():
        if matplotlib.__version__ < '3.1.0':
            tick.label1On = False    # deprecated
            tick.label2On = True
        tick.label2.set_visible(True)
        tick.label1.set_visible(False)
        tick.tick1line.set_visible(False)
        tick.tick2line.set_visible(True)
        tick.label2.set_fontsize(fontsize)

    xax = f.axes[0].get_xaxis()
    xax.set_label_position('bottom')
    for tick in xax.get_major_ticks():
        if matplotlib.__version__ < '3.1.0':
            tick.label1On = True    # deprecated
            tick.label2On = False
        tick.label1.set_visible(True)
        tick.label2.set_visible(False)
        tick.label1.set_fontsize(fontsize)

    # get around font manager problem for old versions... *sigh*
    if matplotlib.__version__ < '0.99.3':
        plt.ylabel('Wavelength (%s)' % ('micron' if w1<100 else 'nm',),
                   fontsize=20, labelpad=15)
    else:
        plt.ylabel('Wavelength (%s)' % ('$\mu$m' if w1<100 else 'nm',),
                   fontsize=20, labelpad=15)
        
    plt.xlabel('Depth (%)', fontsize=20)

##    plt.title('Legend', fontsize=32)
    
##    plt.xticks((d0, (d0+d1)/2, d1))
##    plt.yticks((w0, (w0+w1)/2, w1))
    
    plt.savefig(name)

def wavemap(fin, fout,
             stretchwav1=2100.0, stretchwav2=2350,
             stretchdepth1=0.0, stretchdepth2=0.2,
            colortable='rainbow', colorfile=None,
            createlegend=False,
             sort_wavelengths=False, use_bbl=False,
             message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

##    if not 'wavelength' in im.band_names[0]:
##        message("No wavelength band found!")
##        return

    try:
        INTERPOLATED_WAVELENGTH = im.band_names.index('interpolated min. wav.')
        INTERPOLATED_DEPTH = im.band_names.index('interpolated depth')
    except ValueError:
        message("No wavelength and/or depth found!")
        return

    im2 = envi2.New(fout, hdr=im, interleave='bsq', bands=3, data_type='u1',
                    band_names=['R', 'G', 'B'], default_bands=[1, 2, 3],
                    wavelength=None, bbl=None,
                    fwhm=None,
                    default_stretch='0 255 linear')

    # get interpolated wavelength and depth
    bwavelength = do_stretch(im[INTERPOLATED_WAVELENGTH], stretchwav1, stretchwav2)
    if stretchdepth2 is None or stretchdepth2==stretchdepth1:
        bdepth, stretchdepth1, stretchdepth2 = stretch.percent_percent_stretch(im[INTERPOLATED_DEPTH], 0.30, 0.95)
        message('Automatic depth stretch: %f, %f' % (stretchdepth1, stretchdepth2))
    else:
        bdepth = do_stretch(im[INTERPOLATED_DEPTH], stretchdepth1, stretchdepth2)

    if colorfile:
        palette = read_color_table(colorfile)
    elif colortable=='rainbow':
        palette = palette_spiral3
    else:
        palette = palette_spiral2

    if progress:
        progress(0.0)
    for j in range(im.lines):
        if progress:
            progress(j / float(im.lines))
        for i in range(im.samples):
            if numpy.isnan(im[j, i, INTERPOLATED_WAVELENGTH]) or numpy.isnan(im[j, i, INTERPOLATED_DEPTH]):
##                im2[j, i, 0] = numpy.NaN
##                im2[j, i, 1] = numpy.NaN
##                im2[j, i, 2] = numpy.NaN
                im2[j, i, 0] = 0
                im2[j, i, 1] = 0
                im2[j, i, 2] = 0
            elif im[j, i, INTERPOLATED_DEPTH]==0:
                im2[j, i, 0] = 0
                im2[j, i, 1] = 0
                im2[j, i, 2] = 0
            else:
                r, g, b = palette[bwavelength[j, i]]
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                v = bdepth[j, i] / 255.0
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                im2[j, i, 0] = 1 + int(254*r)
                im2[j, i, 1] = 1 + int(254*g)
                im2[j, i, 2] = 1 + int(254*b)

    if progress:
        progress(1.0)

    del im, im2

    if createlegend:
        save_legend_vertical(palette, stretchwav1, stretchwav2, stretchdepth1, stretchdepth2,
                    fout + '_legend.pdf')
        save_legend_vertical(palette, stretchwav1, stretchwav2, stretchdepth1, stretchdepth2,
                    fout + '_legend.png')
        message('Legend saved')

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='wavemap.py',
        description='Make wavelength/depth map using color table and HSV transform')

    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
    parser.add_argument('-o', dest='output', help='output file name', required=True)

    parser.add_argument('-w', dest='wstart', type=float,
                      help='lower wavelength', required=True)
    parser.add_argument('-W', dest='wend', type=float,
                      help='upper wavelength', required=True)
    parser.add_argument('-d', dest='dstart', type=float, default=0.0,
                      help='lower depth value (default 0.0)')
    parser.add_argument('-D', dest='dend', type=float,
                      help='upper depth value')
    parser.add_argument('-c', dest='colortable', choices=['rainbow', 'steps'], default='rainbow',
                      help='color table: rainbow (default) or steps')
    parser.add_argument('-C', dest='colorfile', help='input color table file')
    parser.add_argument('-l', action='store_true', dest='createlegend',
                      help='save legend in a .png file')

    options = parser.parse_args()

    if not options.force and os.path.exists(options.output):
        sys.exit("Output file exists. Use option -f to overwrite.")

    wavemap(options.input, options.output,
            stretchwav1=options.wstart, stretchwav2=options.wend,
            stretchdepth1=options.dstart, stretchdepth2=options.dend,
            colortable=options.colortable, colorfile=options.colorfile,
            createlegend=options.createlegend)

    sys.exit(0)
