#!/usr/bin/python3
## sitformat.py
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

# Try to import from Pillow or PIL
try:
    from PIL import Image
except ImportError as errtext:
    import Image

import os

from stretch import minmax_stretch
from numpy import memmap

##def minmax_stretch(b):
##    min_ = b.min()
##    return (255.99*(b-min_)/(b.max()-min_)).astype('u1')

def is_sit_format(fin):
    f1 = open(fin, 'rb')
    data = f1.read(4)
    f1.close()
    return data == '9100'

def sit_format_TIR(fin):
    BL = 2
    data = memmap(fin, mode='r', dtype='u2', shape=(156168//BL,))
    data = data.newbyteorder()

    image1 = data[1024//BL:1024//BL+320*240]
    image1 = image1.reshape((240,320))

    im = Image.new(mode='I;16', size=(320, 240))

    for j in range(240):
        for i in range(320):
            im.putpixel((i, j), image1[j, i])

    fout = os.path.splitext(fin)[0] + 'TIR.tif'
    im.save(fout)

def sit_format_TIR_jpeg(fin):
    BL = 2
    data = memmap(fin, mode='r', dtype='u2', shape=(156168//BL,))
    data = data.newbyteorder()

    image1 = data[1024//BL:1024//BL+320*240]
    image1 = minmax_stretch(image1.reshape((240,320)))

    im = Image.fromarray(image1)
    fout = os.path.splitext(fin)[0] + 'TIR.jpg'
    im.save(fout)

MAGIC_JPEG_START = '\xff\xd8'
MAGIC_JPEG_END   = '\xff\xd9'

def sit_format_VIS(fin):
    f1 = open(fin, 'rb')
    data = f1.read()
    f1.seek(data.rfind(MAGIC_JPEG_START))

    fout = os.path.splitext(fin)[0] + 'VIS.jpg'
    f2 = open(fout, 'wb')

    f2.write(f1.read())

    f2.close()
    f1.close()
    
if __name__ == '__main__':
    fname = 'SS010043.SIT'
    sit_format_TIR(fname)
    sit_format_TIR_jpeg(fname)
    sit_format_VIS(fname)
