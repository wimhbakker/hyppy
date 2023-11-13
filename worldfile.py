#!/usr/bin/python3
## worldfile.py
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

## For info on World files see http://en.wikipedia.org/wiki/World_file

import os

def worldfile_name(imname):
    '''Construct World file name by removing the middle character from the
extension and by adding w to the end.'''
    root, ext = os.path.splitext(imname)
    if len(ext)!=4:
        raise ValueError('Unexpected extension: "%s"' % (ext,))
    ext = ext[:2] + ext[3] + 'w'
    return root + ext

def worldfile_name_long(imname):
    '''Construct World file name by simply adding w to the end.'''
    return imname + 'w'

def worldfile_names(imname):
    '''Returns list of potential World file names.'''
    return (worldfile_name(imname), worldfile_name_long(imname))

def worldfile_get(imname):
    '''Returns a 6 tuple containing the info from World file, if any...'''
    for wfile in worldfile_names(imname):
        if os.path.exists(wfile):
            return worldfile_read(wfile)
    return None

def worldfile_read(wfile):
    '''Reads the 6 parameters from the World file:
Line 1: A: pixel size in the x-direction in map units/pixel
Line 2: D: rotation about y-axis
Line 3: B: rotation about x-axis
Line 4: E: pixel size in the y-direction in map units, almost always negative
Line 5: C: x-coordinate of the center of the upper left pixel
Line 6: F: y-coordinate of the center of the upper left pixel

These values are used in a six-parameter affine transformation:
x' = Ax + By + C
y' = Dx + Ey + F
'''
    f = open(wfile, 'r')
    data = f.readlines()
    f.close()
    l = 6 * [0.0]
    try:
        for i in range(6):
            l[i] = float(data[i].strip())
    except:
        return None
    return tuple(l)

def worldfile_create(imname, wtuple):
    '''Create World file for image from 6-tuple. See wordfile_read()'''
    A, D, B, E, C, F = wtuple

    # save world file. Use short format for world file name.
    f = open(worldfile_name(imname), 'w')
    f.write('%.10f\n' % (A,))    
    f.write('%f\n'    % (D,))    
    f.write('%f\n'    % (B,))
    f.write('%.10f\n' % (E,))
    f.write('%.10f\n' % (C,))
    f.write('%.10f\n' % (F,))
    f.close()

if __name__=='__main__':
    pass # 'No CLI for this module!'
