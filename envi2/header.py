#########################################################################
#
# header.py
#
# read / write module for ENVI header files
#
# Modified WHB 20090513, refactoring
# Modified WHB 20121212, fixed bug reading file name ''
# Modified WHB 20160226, changed header attribute names to lower case
# Modified WHB 20210316, added support for ENVI Speclibs as images
#
#
# ENVI header file info:
# data type - parameter identifying the type of data representation,
# where 1=8 bit byte;
# 2=16-bit signed integer;
# 3=32-bit signed long integer;
# 4=32-bit floating point;
# 5=64-bit double precision floating point;
# 6=2x32-bit complex, real-imaginary pair of double precision;
# 9=2x64-bit double precision complex, real-imaginary pair of double precision;
# 12=16-bit unsigned integer;
# 13=32-bit unsigned long integer;
# 14=64-bit signed long integer;
# and 15=64-bit unsigned long integer.
#
# byte order -describes the order of the bytes in integer, long integer,
# 64-bit integer, unsigned 64-bit integer, floating point, double precision,
# and complex data types; Byte order=0 is Least Significant Byte First (LSF)
# data (DEC and MS-DOS systems) and byte order=1 is Most Significant Byte
# First (MSF) data (all others - SUN, SGI, IBM, HP, DG). 
#
# interleave - refers to whether the data are band sequential (BSQ),
# band interleaved by pixel (BIP), or band interleaved by line (BIL).
#
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

import os
import numpy
import copy
from . import envilist
from . import constants
#import time
##import collections

######################################################################
#
# Definition of the envi_header class
#
# The envi_header object contains the original information from the
# ENVI header file (plus a bit more).
#
# Some of the information may change because of sorting wavelengths
# and using a bad band list and therefore the current information
# should be obtained from the image object itself NOT from its
# associated envi_header object!
#

class Header:
    # datatypedict translates envi data types to numpy data types
    datatypedict = {1:'u1', 2:'h', 3:'i', 4:'f', 5:'d',
                    6:'F', 9:'D', 12:'H', 13:'I', 14:'l', 15:'L'}
    # and back...
    # some redundancy here...
    revdatatypedict = {'u1':1, 'B':1, 'h':2, 'i':3, 'f':4, 'd':5,
                       'F':6, 'D':9, 'H':12, 'I':13, 'l':14, 'L':15,
                       numpy.dtype('uint8'):1,
                       numpy.dtype('int16'):2,
                       numpy.dtype('int32'):3,
                       numpy.dtype('float32'):4,
                       numpy.dtype('float64'):5,
                       numpy.dtype('complex64'):6,
                       numpy.dtype('complex128'):9,
                       numpy.dtype('uint16'):12,
                       numpy.dtype('uint32'):13,
                       numpy.dtype('int64'):14,
                       numpy.dtype('uint64'):15,
                       'uint8':1,
                       'int16':2,
                       'int32':3,
                       'float32':4,
                       'float64':5,
                       'complex64':6,
                       'complex128':9,
                       'uint16':12,
                       'uint32':13,
                       'int64':14,
                       'uint64':15
                       }

# hdr can be envi_header or envi_image object

    def __init__(h, fname=None, hdr=None, sort_wavelengths=True, use_bbl=True, **keys):
##                 lines=0, samples=0, bands=0,
##                 interleave='', datatype=0, byteorder=0):
        h.attrlist = []
        
        # STEP 1: construct header from file
        if fname is not None: 
            h.read(fname)
            
        # STEP 2: overwrite with supplied header or header from image
        if hdr:
            # header from image object?
            if not isinstance(hdr, Header):  
                hdr = hdr.header

            # copy attributes from supplied header
            for attr in hdr.attrlist:
                setattr(h, attr, getattr(hdr, attr))
                h.to_attrlist(attr)

            # fix the virtual stuff
            if hasattr(hdr, 'itoi'):
                h.setbands(len(hdr.itoi))
                
                # fix all the lists with length equal to the real number of bands
                for attr in h.attrlist:
                    value = getattr(h, attr)
                    if attr in ['wavelength', 'bbl', 'fwhm', 'band_names', 'data_gain_values'] and \
                       (type(value)==list or isinstance(value, numpy.ndarray)) and len(value)==hdr.getbands():
                        setattr(h, attr, numpy.array(getattr(hdr, attr))[hdr.itoi])
            
        # STEP 3: copy envi atributes to object attributes
        if 'file_type' in keys: # file_type must be retrieved first...
            h.file_type = keys['file_type']
            
        for attr, value in list(keys.items()):
            # In an ENVI Speclib the bands and samples are swapped...
            if h.file_type==constants.ENVI_Speclib and attr=='bands':
                h.samples = value
                h.to_attrlist('samples')
            elif h.file_type==constants.ENVI_Speclib and attr=='samples':
                h.bands = value
                h.to_attrlist('bands')
                if h.bands!=1:
                    raise ValueError('ENVI Speclib header should have bands=1, not %d' % (h.bands,))
            else:
                setattr(h, attr, value)
                h.to_attrlist(attr)

        # STEP 4: set up virtual bands, if needed
        if fname and (sort_wavelengths or use_bbl):
            # look at wavelengths
            if hasattr(h, 'wavelength'):
                w = h.wavelength
            else:
                w = list(range(h.getbands()))
                
            i = list(range(len(w)))
            # create list of (wavelength, band) pairs
            wavband = list(zip(w, i))

            # look at bad band list, throw out bad bands
            if use_bbl and hasattr(h, 'bbl'):
                wavband = numpy.array(wavband)[numpy.where(numpy.array(h.bbl))]
            
            # sort remaining channels
            if sort_wavelengths:
                # kludge to go back from array to list and sort
                wavband = sorted([(x[0], x[1]) for x in wavband])

            # create the index to index list in the header    
            h.itoi = numpy.array([int(x[1]) for x in wavband])
            h.goodbands = len(h.itoi)
            
    def to_attrlist(self, attr):
        if attr not in self.attrlist:
            self.attrlist.append(attr)

    def __str__(h):
        s = ''
        for attr in h.attrlist:
            v = getattr(h, attr, '<not set>')
            s = s + '%s = %s\n' % (attr, str(v))
        return s

    def write(h, fname):
        if fname.split('.')[-1] == 'hdr':
            f = open(fname, 'w')
        else: # must have extension .hdr
            f = open(fname+'.hdr', 'w')

        f.write('%s\n' % getattr(h, 'magic', 'ENVI'))

        for attr in h.attrlist:
            enviattr = ' '.join(attr.split('_'))
            value = getattr(h, attr)
##            if attr=='description':
##                f.write(('description = { header generated by envi.py [%s] }\n')
##                        % (time.asctime(time.localtime(time.time())),))
            if isinstance(value, list) or isinstance(value, tuple) or (isinstance(value, numpy.ndarray) and value.shape):
                if hasattr(h, 'itoi') and len(value)==h.getbands():
                    value = numpy.array(value)[h.itoi]
                f.write(('%s = %s\n') % (enviattr, envilist.to_envi_list(value)))
            elif attr == 'data_type':
##                f.write(('%s = %s\n') % (enviattr, h.revdatatypedict[value]))
                f.write(('%s = %s\n') % (enviattr, h.revdatatypedict[numpy.dtype(value)]))
            elif value is None: # attribute was reset, don't write!
                pass
            elif not h.file_type==constants.ENVI_Speclib and attr == 'bands':
                if hasattr(h, 'itoi'):
                    value = len(h.itoi) # or h.goodbands
                f.write(('%s = %s\n') % (enviattr, str(value)))
            elif h.file_type==constants.ENVI_Speclib and attr == 'samples':
                if hasattr(h, 'itoi'):
                    value = len(h.itoi) # or h.goodbands
                f.write(('%s = %s\n') % (enviattr, str(value)))
            else:
                f.write(('%s = %s\n') % (enviattr, str(value)))

        # force writing to disk!
        f.flush()
        os.fsync(f.fileno())
        
        f.close()

    def read(h, fname):
        base, ext = os.path.splitext(fname)
        if ext.lower() == '.hdr':
            f = open(fname, 'r')
        elif os.path.exists(fname + '.hdr'):
            f = open(fname + '.hdr', 'r')
        elif os.path.exists(fname + '.HDR'):
            f = open(fname + '.HDR', 'r')
        elif os.path.exists(base + '.hdr'):
            f = open(base + '.hdr', 'r')
        elif os.path.exists(base + '.HDR'):
            f = open(base + '.HDR', 'r')
        else:
            raise ValueError('%s: header file not found' % (fname,))
                
##        try: # where's the header file?
##            f = open(fname+'.hdr', 'r')
##        except IOError:
##            try:
##                f = open('.'.join(fname.split('.')[:-1])+'.hdr', 'r')
##            except IOError:
##                f = open(fname, 'r')
                
        t = f.readlines()
        f.close()
        curattr = 'magic'
        setattr(h, 'magic', '')
        for i in range(len(t)):
            l = t[i].strip()
            if l == '':         # Empty line
                pass
            elif l[0] == ';':   # Comment
                pass
            elif '=' in l:      # Variable
                s = l.split('=', 1)
                # replace spaces from attribute names by underscores
                enviattr = s[0].strip()
                curattr = '_'.join(enviattr.split(' '))
                curattr = curattr.lower()
                h.attrlist.append(curattr)
                try: # try conversion to integer
                    setattr(h, curattr, int(s[1].strip()))
                except ValueError:
                    setattr(h, curattr, s[1].strip())
            else:               # Variable continued...
                setattr(h, curattr, getattr(h, curattr, '') + l)

        # convert envi data type to Python data type
        if hasattr(h, 'data_type'):
            h.data_type = h.datatypedict[h.data_type]

        # convert envi lists to Python lists
        for attr in h.attrlist:
            value = getattr(h, attr)
            if type(value)==str and value and value[0]=='{':
                setattr(h, attr, envilist.to_python_list(value))
        
    def copy(h):
        return copy.copy(h)

    #### These functions are for ENVI Speclib support, getters and setters ####

    def getlines(h):
        return h.lines

    def getbands(h):
        return h.samples if h.file_type==constants.ENVI_Speclib else h.bands

    def getsamples(h):
        return h.bands if h.file_type==constants.ENVI_Speclib else h.samples
    
    def setlines(h, v):
        h.lines = v

    def setbands(h,v):
        if h.file_type==constants.ENVI_Speclib:
            h.samples =v
        else:
            h.bands = v

    def setsamples(h, v):
        if h.file_type==constants.ENVI_Speclib:
            h.bands =v
        else:
            h.samples = v
    
