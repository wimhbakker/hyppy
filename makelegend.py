#!/usr/bin/python3
## makelegend.py
##
## Copyright (C) 2020 Wim Bakker
##  Modified: 20200910 WHB added -u for suppressing Unclassified entries
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

# load support for ENVI images
import envi2
from envi2.constants import *

# Pillow module
from PIL import Image, ImageDraw, ImageFont

UNCLASSIFIED = 'Unclassified'

def message(s):
    pass

def makelegend(nameIn, suppress=False):
    # get ENVI image data
    im = envi2.Open(nameIn)

    if not im.header.file_type == ENVI_Classification:
        raise ValueError("Expected an ENVI Classification image")

    lines = im.lines
    samples = im.samples

    lookup = im.header.class_lookup
    names = im.header.class_names

    ## PASS 1, get list of valid legend entries
    unc_count = 0
    entries = list()
    for i in range(len(names)):
        classvalue = i
        classname = names[i]
        classrgb = tuple(lookup[3*i:3*i+3])
        if suppress and unc_count>0 and classname==UNCLASSIFIED:
            pass
        else:
            entries.append((classvalue, classname, classrgb))
        if classname==UNCLASSIFIED:
            unc_count = unc_count + 1

    ## PASS 2, draw legend entries
    leg = Image.new('RGB', (512, 70 + len(entries) * 30), color=(255, 255, 255))

    fnt = ImageFont.truetype("Pillow/Tests/fonts/LiberationMono-Regular.ttf", 40)
    fntsmall = ImageFont.truetype("Pillow/Tests/fonts/LiberationMono-Regular.ttf", 16)

    # get a drawing context
    d = ImageDraw.Draw(leg)

    # draw text, half opacity
    d.text((10,10), "Legend", font=fnt, fill=(0, 0, 0))

    maxtextsize = 0
    for i in range(len(entries)):
        classvalue, classname, classrgb = entries[i]
        x0, y0 = (10, 60 + 30*i)
        x1, y1 = x0 + 50, y0 + 20
        d.rectangle((x0, y0, x1, y1), fill=classrgb)
#        print(names[i])
        d.text((x1 + 10, y0), classname, font=fntsmall, fill=(0, 0, 0))
        textsize = d.textsize(classname, font=fntsmall)[0]
        if textsize > maxtextsize:
            maxtextsize = textsize

    maxy = min(512, maxtextsize+80)
    leg = leg.crop((0, 0, maxy, leg.height))
    
#    leg.show()
    leg.save(nameIn + '_legend.png')
    leg.save(nameIn + '_legend.pdf')

    # destroy resources
    del im

if __name__ == '__main__':
    # command line version
    import argparse
    import os
    import sys

    parser = argparse.ArgumentParser(prog='makelegend.py',
        description='Create a legend for ENVI Classification image')

    parser.add_argument('-i', dest='input', required=True, help='input file')
    parser.add_argument('-u', action='store_true', dest='suppress_unclassified',
                      help='Suppress multiple unclassified legend entries')

    options = parser.parse_args()

    makelegend(options.input, suppress=options.suppress_unclassified)

    sys.exit(0)
