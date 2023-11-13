#!/usr/bin/python3
## wmsget.py
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

from owslib.wms import WebMapService

import worldfile
import convert

extdict = {'image/png':'.png', 'image/gif':'.gif', 'image/png; mode=24bit':'.png',
           'image/jpeg':'.jpg', 'image/wbmp':'.bmp', 'image/tiff':'.tif',
           'image/svg+xml':'.svg'}

def message(s):
    print(s)

######### WMS stuff ########

def wms_connect(url):
    try:
        wms = WebMapService(url, version='1.1.1')
        return wms
    except:
        return None

def wms_contents(wms):
    return list(wms.contents.keys())

def wms_layer_styles(wms, layer):
    return list(wms[layer].styles.keys())

def wms_layer_refs(wms, layer):
    return wms.contents[layer].crsOptions

def wms_layer_bbox(wms, layer):
    return wms[layer].boundingBox

def wms_formats(wms):
    return wms.getOperationByName('GetMap').formatOptions

def wmsget(url, layer, srs, center, resolution, imformat, size, output,
           style=None, enviout=False, message=message):
    wms = wms_connect(url)

    if not wms:
        message('Connection failed')
        return

    if not layer in wms_contents(wms):
        message('Layer %s not found' % (layer,))
        return

    if style and not style in wms_layer_styles(wms, layer):
        message('Style %s not found' % (style,))
        return

    if not srs in wms_layer_refs(wms, layer):
        message('SRS %s not found' % (srs,))
        return

    if not imformat in wms_formats(wms):
        message('Format %s not found' % (imformat,))
        return

    cx, cy = center
    sx, sy = size
    x1, x2 = cx - sx * resolution / 2, cx + sx * resolution / 2
    y1, y2 = cy - sy * resolution / 2, cy + sy * resolution / 2

    # bbox is LL + UR
    bbox = (x1, y1, x2, y2)
    
    img = wms.getmap(layers=[layer], styles = [style] if style else None,
                     srs=srs, bbox=bbox, size=size, format=imformat)

    # was an extension given? otherwise, add one
    root, ext = os.path.splitext(output)

    if ext!=extdict[imformat]:
        output = output + extdict[imformat]

    # write out image
    out = open(output, 'wb')
    out.write(img.read())
    out.close()

    # create world file for image. We need UL corner coord's.
    worldfile.worldfile_create(output,
                               (resolution, 0.0, 0.0, -resolution, x1, y2))

    # convert to ENVI?
    if enviout:
        root, ext = os.path.splitext(output)
        convert.image2envi(output, root + '_envi', message=message)

if __name__ == '__main__':
### Example:
##    url = 'http://luchtfoto.services.gbo-provincies.nl/mapserv.cgi?map=nl.map'
##    layer = 'nl2009_25cm'
##    style = None
##    srs = 'EPSG:28992'
##    center = (183386, 333365)
##    resolution = 0.25
##    imformat = 'image/jpeg'
##    size = (2000, 2000)
##    output = '/home/bakker/Desktop/test8.jpg'


    # command line interace
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='wmsget.py',
##        usage='wmsget.py -u url -l layer -s layerstyle -p reference -x centerx -y centery -r resolution -i imageformat -a width -b height -o output -e',
        description='Get image via Web Map Server (WMS).')

    parser.add_argument('-u', dest='url', help='URL of the WMS', required=True)
    parser.add_argument('-l', dest='layer', help='selected layer', required=True)
    parser.add_argument('-s', dest='style', help='selected layer style')
    parser.add_argument('-p', dest='srs', help='selected spatial reference, for instance "EPSG:28992"', required=True)

    parser.add_argument('-x', dest='centerx', type=float,
                      help='selected center x coordinate', required=True)
    parser.add_argument('-y', dest='centery', type=float,
                      help='selected center y coordinate', required=True)
    parser.add_argument('-r', dest='resolution', type=float, default=1.0,
                      help='required resolution')
    
    parser.add_argument('-i', dest='imformat', default='image/jpeg',
                      help='output image format, typically "image/jpeg" etc.',
                      choices=list(extdict.keys()))
    
    parser.add_argument('-a', dest='width', type=int, default=2000,
                      help='output width in pixels')
    parser.add_argument('-b', dest='height', type=int, default=2000,
                      help='output height in pixels')
    
    parser.add_argument('-o', dest='output', help='input file name', required=True)

    parser.add_argument('-e', action='store_true', dest='enviout',
                      help='flag for also generating ENVI format image')

##    parser.set_defaults(imformat='image/jpeg', width=2000, height=2000,
##                        resolution=1.0, enviout=False)

    options = parser.parse_args()

##    assert options.url, "Option -u WMS url required."
##    assert options.output, "Option -o output file name required."
##    assert options.layer, "Option -l layer name required."
##    assert options.srs, "Option -p spatial reference required."
##    assert options.centerx is not None, "Option -x center x-coordinate required."
##    assert options.centery is not None, "Option -y center y-coordinate required."

    center = (options.centerx, options.centery)
    size = (options.width, options.height)
    
    wmsget(options.url, options.layer, options.srs, center,
           options.resolution, options.imformat, size,
           options.output, style=options.style, enviout=options.enviout)
