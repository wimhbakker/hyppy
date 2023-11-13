#########################################################################
#
# speclib.py
#
# read / write module for ENVI spectral libraries
#
# Modified WHB 20090513, refactoring
# Modified WHB 20090528, added __getitem__() and __setitem__()
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
import collections

from . import header
from . import spectral
from . import resample

from .constants import *

######################################################################
#
# Definition of the envi Speclib class
#

class Speclib:
    def __init__(self, fname, mode='r', as_type=None, hdr=None, **keys):
        """Constructor of class Speclib.

fname   - file on disk
mode    - 'r' for reading, 'w' for writing
as_type - read spectrum as type 'as_type', should be a numpy type
hdr     - used for constructing new spectral libraries
key=value - any remaining key=value pair will end up in the header,
        useful for setting up new headers.
"""
        if mode[0]=='w':
##            if hdr:
##                self.header = header.Header(hdr=hdr, **keys)
            self.header = header.Header(hdr=hdr,
                              file_type=ENVI_Speclib,
                              sort_wavelengths=False,
                              use_bbl=False, **keys)
            self.header.write(fname)
            self._to_file(fname)
        else:
            if not hdr:
                self.header = header.Header(fname)
            self._from_file(fname, as_type=as_type)

    def __getitem__(self, i):
        """The Speclib object can take 1 or 2 indices.

1 index     assumes we want a spectrum
2 indices   assumes we want a value

Indices follow the BIP principle and must be given as (spectrum, band).

All indices can be slices.

Spectrum names can also be used as indices.
"""
        if i == Ellipsis:
            return self.data
        elif type(i)!=tuple:
            # one argument, assume we want a spectrum
            return self.data[self._spec_index(i), :]
        elif len(i)==2:
            # two arguments, assume we want a value
            s, b = i
            return self.data[self._spec_index(s), b]
        else:
            raise IndexError('invalid index')

    def __setitem__(self, i, value):
        """The Speclib object can take 1 or 2 indices.

1 index     assumes we set a spectrum
2 indices   assumes we set a value

Indices follow the BIP principle and must be given as (spectrum, band).

All indices can be slices.

Spectrum names can also be used as indices.
"""
        if i == Ellipsis:
            self.data[...] = value
        elif type(i)!=tuple:
            # one argument, assume we want a spectrum
            self.data[self._spec_index(i), :] = value[:]
        elif len(i)==2:
            # two arguments, assume we want a value
            s, b = i
            self.data[self._spec_index(s), b] = value
        else:
            raise IndexError('invalid index')

    def __len__(self):
        """Returns the number of spectra in the Spectral library.
"""
        return self.header.lines

##    def __del__(self):
##        self.data.sync()

    def sync(self):
        self.data.sync()

    def flush(self):
        self.data.flush()

    def _to_file(self, fname):
        """Sets up the writable memory map to the given file fname.
"""
        h = self.header
        shape = (h.lines, h.samples)
        self.data = numpy.memmap(fname,mode='w+',shape=shape,
                           dtype=h.data_type)

    def _from_file(self, fname, as_type=None):
        """Sets up a readable memory map to the file fname.

Spectra my be mapped to a different data type than the one used on
disk by supplying the argument as_type.

as_type     - map data to this type, should be a numpy data type.
"""
        h = self.header

        if getattr(h, 'file_type', ENVI_Speclib) != ENVI_Speclib:
            raise ValueError("not an ENVI Spectral Library")
        
        shape = (h.lines, h.samples)

        # The memmap manual says: "an offset requires `shape=None`"???
        # but it seems to work just fine...
        if getattr(h, 'offset', 0) != 0:
            self.data = numpy.memmap(fname, mode='r', shape=shape,
                               dtype=h.data_type, offset=h.offset)
            h.offset = 0   # reset offset...
        else:
            self.data = numpy.memmap(fname, mode='r', shape=shape,
                               dtype=h.data_type)

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

        # this creates a copy, not a view!!!
        # should not be used on large data sets!
        if as_type is not None:
            self.data = self.data.astype(as_type)

    # translate spectra name to index
    def _spec_index(self, s):
        """Translates any index or range of indices to the proper spectrum index.
It handles integers, floats, strings, slices and sequences.
"""
        if s is None:
            return None
        elif type(s) == slice:
            return slice(self._spec_index(s.start), self._spec_index(s.stop),
                         s.step)
        elif isinstance(s, str):
            return self.header.spectra_names.index(s)
        elif isinstance(s, collections.abc.Sequence) or isinstance(s, numpy.ndarray):
            return list(map(self._spec_index, s))
        else:
            return s

    def spec_match(self, name, matchall=True):
        result = []
        for i in range(len(self.header.spectra_names)):
            sname = self.header.spectra_names[i]
            if name.lower() in sname.lower():
                if matchall:
                    result.append(i)
                else:
                    return i
        return result

    # functions for getting data
    def get_band(self, s, b):
        """Get the value of spectrum s at band b.
"""
        return self.data[self._spec_index(s), b]

    def get_value(self, s, b):
        """Get the value of spectrum s at band b.
"""
        return self.data[self._spec_index(s), b]

    def get_spectrum(self, s):
        """Get spectrum s."""
        return self.data[self._spec_index(s), :]

    #
    # Some distance measures as methods of the class
    #  input: two coordinate pairs (tuples!)
    #  output: the distance
    #
    
    def spectral_angle(im, t1, t2):
        s1 = im.get_spectrum(t1)
        s2 = im.get_spectrum(t2)
        return spectral.spectral_angle(s1, s2)

    def euclidean_distance(im, t1, t2):
        s1 = im.get_spectrum(t1)
        s2 = im.get_spectrum(t2)
        return spectral.euclidean_distance(s1, s2)

    def intensity_difference(im, t1, t2):
        s1 = im.get_spectrum(t1)
        s2 = im.get_spectrum(t2)
        return spectral.intensity_difference(s1, s2)

    def spectral_information_divergence(im, t1, t2):  # a.k.a. SID
        s1 = im.get_spectrum(t1)
        s2 = im.get_spectrum(t2)
        return spectral.spectral_information_divergence(s1, s2)

    def bray_curtis_distance(im, t1, t2):
        s1 = im.get_spectrum(t1)
        s2 = im.get_spectrum(t2)
        return spectral.bray_curtis_distance(s1, s2)

    def wavelength2index(self, wavelength):
        """Returns the index of the band with the closest wavelength number.

wavelength is the required wavelength.

Note that the units used should reflect the units used in the header file.
Currently there is no check on whether the given units make any sense with
relation the the wavelengths supplied with the image.
"""
        return sorted(zip(numpy.abs(numpy.array(self.header.wavelength)-wavelength),
                          list(range(len(self.header.wavelength)))))[0][1]

    def index2wavelength(self, index):
        """Returns the wavelength of the band with this index.

The wavelength is returned in the units that are used in the header file.
These may be microns, nanometers or ???
"""
        return self.header.wavelength[index]


    def resampled(self, s, w):
        return resample.resample(self[s], self.header.wavelength, w)

####### Added for compatibility with AscSpeclib ###########
    def wavelength(self, s):
        """Return wavelengths of spectrum"""
        return getattr(self.header, 'wavelength', None)

    def wavelength_units(self, s):
        """Return wavelength units of spectrum"""
        return getattr(self.header, 'wavelength_units', None)

    def spectrum(self, s):
        """Return spectral values of spectrum"""
        return self[s]

    def name(self, s):
        """Return name of spectrum"""
        return self.header.spectra_names[s]

    def names(self):
        """Return names of spectra"""
        return self.header.spectra_names

    def description(self, s):
        """Return description of spectrum"""
        return None

    def __call__(self, wav):
        """Returns the band with given wavelength.
This assumes that the spectrum does have wavelengths.

A numpy array will be returned.
Use as follows: band = spec(wavelength)

There is no check on units. There is no check on whether
the returned band is close to the requested band.
"""
        return self[self.wavelength2index(wav)]

