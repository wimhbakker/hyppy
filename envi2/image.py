#########################################################################
#
# image.py
#
# read / write module for ENVI images
#
# Modified WHB 20090513, refactoring
# Modified WHB 20090528, make all data look like BIP data
# Modified WHB 20090615, added ellipsis to image indexing
# Modified WHB 20091120, ignore band index on 1-band images
# Modified WHB 20100518, treat 1-band images as 3D data w/ band dimension 1
# Modified WHB 20111216, added __call__() for im(wavelength)
# Modified WHB 20201008, added hints for wavelength2index
# Modified WHB 20210315, added support for ENVI spectral libraries as images
# Modified WHB 20230315, added fwhm to Image class
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

import numpy
import sys

from . import header
from . import spectral
from .constants import *

######################################################################
#
# Definition of the Image class
#
#

class Image:
    """Image: abstract superclass

Note that the image is a 'view' and may not actually reflect
the data on disc because the wavelengths may be sorted and because
the bad band list may be taken into account.

Regardless whether the original image format was BSQ, BIL or BIP,
the view is mapped into BIP format (y, x, band). Also new images
are mapped onto a BIP view regardless there output format.
Why BIP? Well, why not?

The Image class attributes bands and wavelength reflect the bands and
wavelengths of the virtual image, NOT the one on disk!

The band attribute may be less than the header.band attribute
if a bad band list is used. (if the image was opened with use_bbl=True)
Always use the band attribute from the image NOT from the header.

Attributes:
data    - the data, mostly of type memmap, 2D (1-band) or 3D (data cube)
header  - the metadata from the original header file
samples - number of samples (x)
lines   - number of lines (y)
bands   - number of bands (z or b)
shape   - shape of the data array, basically the same as data.shape
wavelength - list of wavelengths, if any are supplied in the header.
band_names - list of band names
bbl - bad band list
"""
    def __init__(self, header):
        self.header = header
        
        # set image attributes
        self.lines = self.header.lines
        self.samples = self.header.samples
        self.bands = self.header.bands

        self._wavelength2index_hints = dict()

        # in an ENVI Spectral Library things are swapped...
        if getattr(self.header, 'file_type', ' ')==ENVI_Speclib:
            self.samples = self.header.bands
            self.bands = self.header.samples
            # delete band names if not meaningful
            if hasattr(self.header, 'band_names') and (self.header.band_names is None or len(self.header.band_names)!=self.bands):
                self.header.attrlist.remove('band_names')
                del self.header.band_names

        if hasattr(self.header, 'itoi'):
            self.bands = len(self.header.itoi)
            if hasattr(self.header, 'wavelength'):
                self.wavelength = numpy.array(self.header.wavelength)[self.header.itoi]
            if hasattr(self.header, 'fwhm'):
                self.fwhm = numpy.array(self.header.fwhm)[self.header.itoi]
            if hasattr(self.header, 'band_names'):
                self.band_names = [self.header.band_names[i] for i in self.header.itoi]
            if hasattr(self.header, 'bbl'):
                self.bbl = [self.header.bbl[i] for i in self.header.itoi]
        else:
#            self.bands = self.header.bands
            if hasattr(self.header, 'wavelength'):
                self.wavelength = numpy.array(self.header.wavelength)
            if hasattr(self.header, 'fwhm'):
                self.fwhm = numpy.array(self.header.fwhm)
            if hasattr(self.header, 'band_names'):
                self.band_names = self.header.band_names
            if hasattr(self.header, 'bbl'):
                self.bbl = self.header.bbl

    def __len__(self):
        return self.bands

    def __getitem__(self, i):
        """The image object can take 1, 2, 3 indices or ellipsis.

1 index     assumes we want a band
2 indices   assumes we want a spectrum
3 indices   assumes we a value or a subset from the image
ellipsis    assumes we want the whole image data

All indices can be slices.

All images are made to behave as if they are BIP images.
This means that the indices must be given in the order y, x, band.

This function returns a number or an array. The returned array
will be in BIP format (y, x, band), in which all the dimensions
are optional.
"""
        if i == Ellipsis:
            return self.data[:, : , self.real_band(slice(None))]
        elif type(i)!=tuple:
            # one argument, assume we want bands
            return self.data[:, : ,self.real_band(i)]
        elif len(i)==2:
            # two arguments, assume we want a spectrum
            y, x = i
            return self.data[y, x, self.real_band(slice(None))]
        elif len(i)==3:
            # three arguments, pass indices in the correct order
            y, x, b = i
            return self.data[y, x, self.real_band(b)]
        else:
            raise IndexError('invalid index')

    def __setitem__(self, i, value):
        """The image object can take 1, 2, 3 indices or ellipsis.

1 index     assumes we want to set a band
2 indices   assumes we want to set a spectrum
3 indices   assumes we want to set a value or a subset in the image
ellipsis    assumes we want to set values in the whole image

All indices can be slices.

All images are made to behave as if they are BIP images.
This means that the indices must be given in the order y, x, band.

This function sets image to value value at index i.
"""
        if i == Ellipsis:
            self.data[...] = value
        elif type(i)!=tuple:
            # one argument, assume we have a band
            self.data[:, :, i] = value
        elif len(i)==2:
            # two arguments, assume we have a spectrum
            y, x = i
            self.data[y, x, :] = value
        elif len(i)==3:
            # three arguments, pass indices in the correct order
            y, x, b = i
            self.data[y, x, b] = value
        else:
            raise IndexError('invalid index')

    def get_value(self, j, i, b):
        """Function get_value: get a value at location j, i, b.
"""
        return self.data[j,i,self.real_band(b)]

    def set_value(self, j, i, b, value):
        """Function set_value: set a value at location j, i, b.
"""
        self.data[j,i,b] = value

    def get_spectrum(self, j, i):
        """Function get_spectrum: get the spectrum at location j, i.
"""
        return self.virtual_spectrum(self.data[j,i,:])
        
    def set_spectrum(self, j, i, value):
        """Function set_spectrum: set the spectrum at location j, i.
"""
        self.data[j,i,:] = value[:]
        
    def get_band(self, b):
        """Function get_band: get band data with band index b.
"""
        return self.data[:,:,self.real_band(b)]

    def set_band(self, b, value):
        """Function set_band: set band data with band index b.
"""
        self.data[:,:,b] = value[:,:]


##    def __del__(self):
##        self.data.sync()

    # sync is obsolete, use flush instead!
    def sync(self):
        self.data.sync()

    def flush(self):
        self.data.flush()

    def _to_file(self, fname):
        """Writes the image to file. Basically creates a writable memmap.
fname should be the name of the output file.
"""
        h = self.header
        shape = self.shape
        
        self.data = numpy.memmap(fname,mode='w+',shape=shape,
                           dtype=h.data_type)

        # make data look like BIP
        if h.file_type==ENVI_Speclib:
#            self.data = self.data.transpose(2, 1, 0)
            pass
        elif h.bands == 1:
            pass
        elif h.interleave.lower()==ENVI_bil:
            self.data = self.data.transpose(0, 2, 1)
        elif h.interleave.lower()==ENVI_bsq:
            self.data = self.data.transpose(1, 2, 0)

    def _from_file(self, fname, as_type=None):
        """Reads an image from file, basically by setting up a memmap.

fname should be the name of the image file.

The argument as_type can be used to load the image as a different type than
the image file on disk. Be aware that this ceates a copy rather than a
memory map to the file. This mean that the entire image will be loaded into
memory!"""
        h = self.header
        file_type = getattr(h, 'file_type', ENVI_Standard)
        if file_type not in [ENVI_Standard, ENVI_Standard_short, ENVI_Classification, ENVI_Other, 'PCI', ENVI_Speclib]:
            raise ValueError("ENVI file type not recognized: %s" % (file_type,))
            
        shape = self.shape

        # Set up the memmap
        # The memmap manual says: "an offset requires `shape=None`"???
        # but it seems to work just fine...
        if getattr(h, 'header_offset', 0) != 0:
            self.data = numpy.memmap(fname, mode='r', shape=shape,
                               dtype=h.data_type, offset=h.header_offset)
            h.header_offset = 0   # reset offset...
        else:
            self.data = numpy.memmap(fname, mode='r', shape=shape,
                               dtype=h.data_type)

        # Set up the byte order
        # look at the endianness of the data
        # Do NOT use byteswap(), use newbyteorder() for a view!
        if hasattr(h, 'byte_order'):
            if sys.byteorder == 'little' and h.byte_order==1:
                print("Warning: swapping byte order to %s-endian" % (sys.byteorder,))
                self.data = self.data.newbyteorder()
                h.byte_order = 0
            elif sys.byteorder=='big' and h.byte_order==0:
                print("Warning: swapping byte order to %s-endian" % (sys.byteorder,))
                self.data = self.data.newbyteorder()
                h.byte_order = 1
        else:
            if sys.byteorder == 'little':
                print("Warning: byte order not set, assuming %s-endian" % (sys.byteorder,))
                h.byte_order = 0
            elif sys.byteorder=='big':
                print("Warning: byte order not set, assuming %s-endian" % (sys.byteorder,))
                h.byte_order = 1

        # make data look like BIP
        if getattr(h, 'file_type', ' ')==ENVI_Speclib:
#            self.data = self.data.transpose(0, 2, 1)
            pass
        elif h.bands == 1:
            pass
        elif h.interleave.lower()==ENVI_bil:
            self.data = self.data.transpose(0, 2, 1)
        elif h.interleave.lower()==ENVI_bsq:
            self.data = self.data.transpose(1, 2, 0)

        # set up the data type
        # this creates a copy, not a view!!!
        # should not be used on large data sets!
        if as_type is not None:
            self.data = self.data.astype(as_type)


    #
    # Some distance measures as methods of the class
    #  input: two coordinate pairs (tuples!)
    #  output: the distance
    #
    
    def spectral_angle(im, t1, t2):
        """Calculate the spectral angle between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.spectral_angle(s1, s2)

    def nan_spectral_angle(im, t1, t2):
        """Calculate the spectral angle between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
This is the nan-safe version of the function.
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.nan_spectral_angle(s1, s2)

    def euclidean_distance(im, t1, t2):
        """Calculate the Euclidean distance between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.euclidean_distance(s1, s2)

    def nan_euclidean_distance(im, t1, t2):
        """Calculate the Euclidean distance between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
This is the nan-safe version of the function.
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.nan_euclidean_distance(s1, s2)

    def intensity_difference(im, t1, t2):
        """Calculate the intensity difference between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.intensity_difference(s1, s2)

    def nan_intensity_difference(im, t1, t2):
        """Calculate the intensity difference between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
This is the nan-safe version of the function.
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.nan_intensity_difference(s1, s2)

    def spectral_information_divergence(im, t1, t2):  # a.k.a. SID
        """Calculate the spectral information divergence between spectra at
locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.spectral_information_divergence(s1, s2)

    def nan_spectral_information_divergence(im, t1, t2):  # a.k.a. SID
        """Calculate the spectral information divergence between spectra at
locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
This is the nan-safe version of the function.
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.nan_spectral_information_divergence(s1, s2)

    def bray_curtis_distance(im, t1, t2):
        """Calculate the Bray-Curtis distance between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.bray_curtis_distance(s1, s2)

    def nan_bray_curtis_distance(im, t1, t2):
        """Calculate the Bray-Curtis distance between spectra at locations t1 and t2.

t1 and t2 should be 2-tuples (x, y).
This is the nan-safe version of the function.
"""
        x1, y1 = t1
        x2, y2 = t2
        s1 = im.get_spectrum(y1, x1)
        s2 = im.get_spectrum(y2, x2)
        return spectral.nan_bray_curtis_distance(s1, s2)

    # functions for determining best wavelength
##    def closest(x, w):
##        return x[sorted(zip(numpy.abs(x-w), range(len(x))))[0][1]]

    def real_band(self, b):
        """Translates virtual band number to real band number on disk
using the index-to-index (itoi) lookup-table.

Argument b can be a number or a list/array.
"""
        if hasattr(self.header, 'itoi'):
            return self.header.itoi[b]
        else:
            return b

    def virtual_spectrum(self, s):
        """Translates real spectrum to virtual spectrum by filtering out bad bands
as they are given in the header file.
"""
        if hasattr(self.header, 'itoi'):
            return numpy.array(s)[self.header.itoi]
        else:
            return s

##    _wavelength2index_hints = dict()

    def wavelength2index(im, wavelength):
        """Returns the index of the band with the closest wavelength number.

wavelength is the required wavelength.

Note that the units used should reflect the units used in the header file.
Currently there is no check on whether the given units make any sense with
relation to the wavelengths supplied with the image.
"""
        if wavelength in im._wavelength2index_hints:
            return im._wavelength2index_hints[wavelength]
        else:
            index = sorted(zip(numpy.abs(numpy.array(im.wavelength)-wavelength), list(range(len(im.wavelength)))))[0][1]
            im._wavelength2index_hints[wavelength] = index
            return index

    def index2wavelength(im, index):
        """Returns the wavelength of the band with this index.

The wavelength is returned in the units that are used in the header file.
These may be microns, nanometers or ???
"""
        return im.wavelength[index]

    def __call__(im, wav):
        """Returns the band with given wavelength.
This assumes that the image does have wavelengths.

A numpy array will be returned.
Use as follows: band = im(wavelength)

There is no check on units. There is no check on whether
the returned band is close to the requested band.
"""
        return im[im.wavelength2index(wav)]


###########################################################################
#
# Image1Band
#
# NOTE: as of 20100518 1-band images are treated as 3D datasets with the
# band dimension having length 1. By default 1-band images are now loaded
# as ImageBIP objects.
#
# HOWEVER, the Image1Band class is still used for the Classification class!
#

class Image1Band(Image):
    """Class Image1Band is used for 1-band images.

See information on the abstract superclass Image for more details.
"""
    def __init__(self, header):
        # call super class __init__()
        Image.__init__(self, header)
        self.shape = (header.lines, header.samples)

    def __getitem__(self, i):
        """The Image1Band object can take 2 indices or ellipsis.

All indices can be slices.

The indices must be given in the order y, x.

This function returns a number or an array.
"""
        if i == Ellipsis:
            return self.data
        elif type(i)!=tuple:
            # one argument, return the data
            return self.data
        elif len(i)==2:
            y, x = i
            return self.data[y, x]
        elif len(i)==3: # ignore band index !
            y, x, b = i
            return self.data[y, x]
        else:
            raise IndexError('invalid index')

    def __setitem__(self, i, value):
        """The Image1Band object can take 2 indices.

All indices can be slices.

The indices must be given in the order y, x.

This function sets image to value value at index i.
"""
        if i == Ellipsis:
            self.data[...] = value
        elif type(i)!=tuple:
            # one argument, assume we have only one band
            self.data[:, :] = value
        elif len(i)==2:
            y, x = i
            self.data[y, x] = value
        elif len(i)==3: # ignore band index !
            y, x, b = i
            self.data[y, x] = value
        else:
            raise IndexError('invalid index')
    # get_value(j, i) # 1-band only! a band argument will be ignored!

    def get_value(self, j, i, b=0):
        """Get value at location j, i.
For compatibility a similar function in the other images classes a third
band argument (b) can be supplied, which will always be ignored.
"""
        return self.data[j,i]

    def set_value(self, j, i, value):
        """Set value at location j, i.
"""
        self.data[j,i] = value

    def get_band(self, b=0): # band will be ignored!
        """Get band function. Will return the whole data set.
Any band argument b will be ignored.
"""
        return self.data

    def set_band(self, value):
        """Set band function. Will copy the whole data set to disk.
"""
        self.data[:,:] = value[:,:]

    def get_spectrum(self, j, i):
        """This function is supplied for conformity with the other image classes.
It fakes a single value at location j, i as a spectrum.
"""
        return numpy.array([self.data[j, i]])
    
    def set_spectrum(self, j, i, value):
        """This function is supplied for conformity with the other image classes.
It fakes a single value at location j, i as a spectrum.
"""
        self.data[j, i] = value[0]


###########################################################################
#
# ImageBIP
#

    
class ImageBIP(Image):
    """Class ImageBIP is used for creating a view on BIP Images.
BIP = Band interleaved by pixel
The band index b is the fastest running index, then x, then y.

See information on the abstract superclass Image for more details.
"""
    def __init__(self, header):
        # call super class __init__()
        Image.__init__(self, header)
        self.shape = (header.lines, header.samples, header.bands)

##    def __getitem__(self, i):
##        """The image object can take 1, 2 or 3 indices.
##
##1 index     assumes we want a band
##2 indices   assumes we want a spectrum
##3 indices   assumes we a value or a subset from the image
##
##All indices can be slices.
##
##All images are made to behave as if they are BIP images.
##This means that the indices must be given in the order y, x, band.
##
##This function returns a number or an array.
##"""
##        if type(i)!=tuple:
##            # one argument, assume we want bands
##            return self.data[:, : ,self.real_band(i)]
##        elif len(i)==2:
##            # two arguments, assume we want a spectrum
##            y, x = i
##            return self.data[y, x, self.real_band(slice(None))]
##        elif len(i)==3:
##            # three arguments, pass indices in the correct order
##            y, x, b = i
##            return self.data[y, x, self.real_band(b)]
##        else:
##            raise IndexError, 'invalid index'
##
##    def __setitem__(self, i, value):
##        """The image object can take 1, 2 or 3 indices.
##
##1 index     assumes we want to set a band
##2 indices   assumes we want to set a spectrum
##3 indices   assumes we want to set a value or a subset in the image
##
##All indices can be slices.
##
##All images are made to behave as if they are BIP images.
##This means that the indices must be given in the order y, x, band.
##
##This function sets image to value value at index i.
##"""
##        if type(i)!=tuple:
##            # one argument, assume we have a band
##            self.data[:, :, i] = value
##        elif len(i)==2:
##            # two arguments, assume we have a spectrum
##            y, x = i
##            self.data[y, x, :] = value
##        elif len(i)==3:
##            # three arguments, pass indices in the correct order
##            y, x, b = i
##            self.data[y, x, b] = value
##        else:
##            raise IndexError, 'invalid index'
##
##    def get_value(self, j, i, b):
##        """Function get_value: get a value at location j, i, b.
##"""
##        return self.data[j,i,self.real_band(b)]
##
##    def set_value(self, j, i, b, value):
##        """Function set_value: set a value at location j, i, b.
##"""
##        self.data[j,i,b] = value
##
##    def get_spectrum(self, j, i):
##        """Function get_spectrum: get the spectrum at location j, i.
##"""
##        return self.virtual_spectrum(self.data[j,i,:])
##        
##    def set_spectrum(self, j, i, value):
##        """Function set_spectrum: set the spectrum at location j, i.
##"""
##        self.data[j,i,:] = value[:]
##        
##    def get_band(self, b):
##        """Function get_band: get band data with band index b.
##"""
##        return self.data[:,:,self.real_band(b)]
##
##    def set_band(self, b, value):
##        """Function set_band: set band data with band index b.
##"""
##        self.data[:,:,b] = value[:,:]

###########################################################################
#
# ImageBIL

class ImageBIL(Image):    # BIL Image
    """Class ImageBIL is used for creating a view on BIL Images.
BIL = Band interleaved by line
The x index is the fastest running index, then b, then y.

See information on the abstract superclass Image for more details.
"""
    def __init__(self, header):
        # call super class __init__()
        Image.__init__(self, header)
        self.shape = (header.lines, header.bands, header.samples)

##    def __getitem__(self, i):
##        """The image object can take 1, 2 or 3 indices.
##
##1 index     assumes we want a band
##2 indices   assumes we want a spectrum
##3 indices   assumes we a value or a subset from the image
##
##All indices can be slices.
##
##All images are made to behave as if they are BIP images.
##This means that the indices must be given in the order y, x, band.
##
##This function returns a number or an array.
##"""
##        if type(i)!=tuple:
##            # one argument, assume we want bands
##            return self.data[:,self.real_band(i),:]
##        elif len(i)==2:
##            # two arguments, assume we want a spectrum
##            y, x = i
##            return self.data[y, self.real_band(slice(None)), x]
##        elif len(i)==3:
##            # three arguments, pass indices in the correct order
##            y, x, b = i
##            return self.data[y, self.real_band(b), x]
##        else:
##            raise IndexError, 'invalid index'
##
##    def __setitem__(self, i, value):
##        """The image object can take 1, 2 or 3 indices.
##
##1 index     assumes we want to set a band
##2 indices   assumes we want to set a spectrum
##3 indices   assumes we want to set a value or a subset in the image
##
##All indices can be slices.
##
##All images are made to behave as if they are BIP images.
##This means that the indices must be given in the order y, x, band.
##
##This function sets image to value value at index i.
##"""
##        if type(i)!=tuple:
##            # one argument, assume we have a band
##            self.data[:, i, :] = value
##        elif len(i)==2:
##            # two arguments, assume we have a spectrum
##            y, x = i
##            self.data[y, :, x] = value
##        elif len(i)==3:
##            # three arguments, pass indices in the correct order
##            y, x, b = i
##            self.data[y, b, x] = value
##        else:
##            raise IndexError, 'invalid index'
##
##    def get_value(self, j, i, b):
##        """Function get_value: get a value at location j, i, b.
##"""
##        return self.data[j,self.real_band(b),i]
##
##    def set_value(self, j, i, b, value):
##        """Function set_value: set a value at location j, i, b.
##"""
##        self.data[j,b,i] = value
##
##    def get_spectrum(self, j, i):
##        """Function get_spectrum: get the spectrum at location j, i.
##"""
##        return self.virtual_spectrum(self.data[j,:,i])
##
##    def set_spectrum(self, j, i, value):
##        """Function get_spectrum: get the spectrum at location j, i.
##"""
##        self.data[j,:,i] = value[:]
##
##    def get_band(self, b):
##        """Function get_band: get band data with band index b.
##"""
##        return self.data[:,self.real_band(b),:]
##
##    def set_band(self, b, value):
##        """Function get_band: get band data with band index b.
##"""
##        self.data[:,b,:] = value[:,:]


###########################################################################
#
# ImageBSQ

class ImageBSQ(Image):    # BSQ Image
    """Class ImageBSQ is used for creating a view on BSQ Images.
BSQ = Band sequential
The x index is the fastest running index, then y, then b.

See information on the abstract superclass Image for more details.
"""
    def __init__(self, header):
        # call super class __init__()
        Image.__init__(self, header)
        self.shape = (header.bands, header.lines, header.samples)

##    def __getitem__(self, i):
##        """The image object can take 1, 2 or 3 indices.
##
##1 index     assumes we want a band
##2 indices   assumes we want a spectrum
##3 indices   assumes we a value or a subset from the image
##
##All indices can be slices.
##
##All images are made to behave as if they are BIP images.
##This means that the indices must be given in the order y, x, band.
##
##This function returns a number or an array.
##"""
##        if type(i)!=tuple:
##            # one argument, assume we want bands
##            return self.data[self.real_band(i),:,:]
##        elif len(i)==2:
##            # two arguments, assume we want a spectrum
##            y, x = i
##            return self.data[self.real_band(slice(None)), y, x]
##        elif len(i)==3:
##            # three arguments, pass indices in the correct order
##            y, x, b = i
##            return self.data[self.real_band(b), y, x]
##        else:
##            raise IndexError, 'invalid index'
##
##    def __setitem__(self, i, value):
##        """The image object can take 1, 2 or 3 indices.
##
##1 index     assumes we want to set a band
##2 indices   assumes we want to set a spectrum
##3 indices   assumes we want to set a value or a subset in the image
##
##All indices can be slices.
##
##All images are made to behave as if they are BIP images.
##This means that the indices must be given in the order y, x, band.
##
##This function sets image to value value at index i.
##"""
##        if type(i)!=tuple:
##            # one argument, assume we have a band
##            self.data[i, :, :] = value
##        elif len(i)==2:
##            # two arguments, assume we have a spectrum
##            y, x = i
##            self.data[: , y, x] = value
##        elif len(i)==3:
##            # three arguments, pass indices in the correct order
##            y, x, b = i
##            self.data[b, y, x] = value
##        else:
##            raise IndexError, 'invalid index'
##
##    def get_value(self, j, i, b):
##        """Function get_value: get a value at location j, i, b.
##"""
##        return self.data[self.real_band(b),j,i]
##
##    def set_value(self, j, i, b, value):
##        """Function set_value: set a value at location j, i, b.
##"""
##        self.data[b,j,i] = value
##
##    def get_spectrum(self, j, i):
##        """Function get_spectrum: get the spectrum at location j, i.
##"""
##        return self.virtual_spectrum(self.data[:,j,i])
##
##    def set_spectrum(self, j, i, value):
##        """Function set_spectrum: set the spectrum at location j, i.
##"""
##        self.data[:,j,i] = value[:]
##
##    def get_band(self, b):
##        """Function get_band: get band data with band index b.
##"""
##        return self.data[self.real_band(b),:,:]
##
##    def set_band(self, b, value):
##        """Function get_band: get band data with band index b.
##"""
##        self.data[b,:,:] = value[:,:]

###########################################################################
#
# Class Classification
#
# ENVI Classification files should have the following attributes:
#
#   file type = ENVI Classification
#   bands = 1
#   interleave = bsq
#
#   classes     - number of classes
#   class lookup - color lookup table one r,g,b triple for each class
#   class names - list of class names
#

class Classification(Image1Band):
    """Used for ENVI Clasification file ypes."""
    def __init__(self, header):
        # call super class __init__()
        Image1Band.__init__(self, header)

###########################################################################
#
# ImageSL

class ImageSL(Image):    # Spectral Library as Image
    """Class ImageSL is used for creating a view on Spectral Libraries as Images.
samples are the spectra
lines are the bands
bands is always 1

See information on the abstract superclass Image for more details.
"""
    def __init__(self, header):
        # call super class __init__()
        Image.__init__(self, header)
        self.shape = (header.lines, header.bands, header.samples)



######################################################################
#
# Factory function, Open()
#

def Open(fname, as_type=None, hdr=None,
                 sort_wavelengths=True, use_bbl=True):
    """Factory function Open returns one of the image objects of class
Image1Band, ImageBIP, ImageBIL or ImageBSQ.

The data is basically memory mapped on file, which means that not much extra
memory will be used for images. There is one exception, if the argument
as_type is supplied then the data will be copied into memory.

A header or image object can be supplied in the hdr argument. This can be
useful in the case the header file is corrupted or missing.

The argument sort_wavelengths can be used to make a view on the data in such
a way that the bands in the image appear to be sorted on wavelength. This is
useful for file in which detector ranges overlap or are not in the right
order.

The argument use_bbl can be used to make a view on the data in which the
bad bands are not visible in the image. This is useful to skip the data
which is marked as bad in the header file.

as_type should be any of the types defined in the dtype of numpy.
hdr should be of type Image or type Header.
sort_wavelengths and use_bbl should be True or False (default is True).
"""
    # read header first
    h = header.Header(fname, hdr=hdr,
                          sort_wavelengths=sort_wavelengths,
                          use_bbl=use_bbl)

    # Check image type and create appropriate object
    if getattr(h, 'file_type', ' ') == ENVI_Speclib:
        im = ImageSL(h)
    elif getattr(h, 'file_type', ' ') == ENVI_Classification:
        im = Classification(h)
    elif h.bands == 1:            # line, sample
##        im = Image1Band(h)
        im = ImageBIP(h)
    elif h.interleave.lower() == ENVI_bip: # line, sample, band
        im = ImageBIP(h)
    elif h.interleave.lower() == ENVI_bil: # line, band, sample
        im = ImageBIL(h)
    elif h.interleave.lower() == ENVI_bsq: # band, line, sample
        im = ImageBSQ(h)
    else:
        raise ValueError('file not recognized')

    # connect to image file
    im._from_file(fname, as_type=as_type)

    return im

######################################################################
#
# Factory function, New()
#

def New(fname, hdr=None, value=None, **keys):
    """Factory function New returns one of the image objects of class
Image1Band, ImageBIP, ImageBIL or ImageBSQ.

The data is basically memory mapped on file, which means that not much extra
memory will be used for images.

A header or image object should be supplied in the hdr argument for setting
up the header information for the newly constructed image.

Any key=value pair supplied to the function will end up in the Envi header
of the image file. This can be useful for controlling the Envi header. The
value can be number, string or list. Lists will be translated into curly
bracket items { and } in the Envi header.

Note that for created images no views are created, everything is going to
disk as is. No mapping by sort_wavelength or use_bbl is assumed.
"""
    # if supplied, use header object
    h = header.Header(hdr=hdr,
                      sort_wavelengths=False,
                      use_bbl=False, **keys)

    # Check image type and create object
    if getattr(h, 'file_type', ' ') == ENVI_Speclib:
        im = ImageSL(h)
    elif getattr(h, 'file_type', ' ') == ENVI_Classification:
        im = Classification(h)
    elif h.bands == 1:            # line, sample
##        im = Image1Band(h)
        im = ImageBIP(h)
    elif h.interleave.lower() == ENVI_bip: # line, sample, band
        im = ImageBIP(h)
    elif h.interleave.lower() == ENVI_bil: # line, band, sample
        im = ImageBIL(h)
    elif h.interleave.lower() == ENVI_bsq: # band, line, sample
        im = ImageBSQ(h)
    else:
        raise ValueError('bad header values')

    # create new header
    im.header.write(fname)

    # create and set up image file
    im._to_file(fname)

    # set initial value if supplied
    if value is not None:
        im.data[...] = value
            
    return im
