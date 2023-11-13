#!/usr/bin/python3
## ascspeclib.py
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
import glob
import os
import crismread
import asdread
import speclib07
import spectrum

##import header
##import spectral
import envi2
import envi2.resample
import envi2.constants

##
##from constants import *

##from numpy import array, arange, where

DELETED_NUMBER = '-1.23e34'

OPUS_DATATYPES = ['Refl', 'AB', 'TR', 'IgSm', 'PhSm', 'ScSm', 'IgRf', 'ScRf']

## Class Spectrum THIS IS OBSOLETE!!!
class Spectrum:
    def __init__(self, name='', wavelength=None, spectrum=None, description=None, fwhm=None):
        self.name = name
        self.wavelength = numpy.array(wavelength)
        self.spectrum = numpy.array(spectrum)
        self.description = description
        self.fwhm = fwhm

    def wavelength2index(self, wavelength):
        """Returns the index of the band with the closest wavelength number.

wavelength is the required wavelength.

Note that the units used should reflect the units used in the speclib.
Currently there is no check on whether the given units make any sense with
relation the the wavelengths supplied with the image.
"""
        return sorted(zip(numpy.abs(numpy.array(self.wavelength)-wavelength),
                          list(range(len(self.wavelength)))))[0][1]

    def index2wavelength(self, index):
        """Returns the wavelength of the band with this index.

The wavelength is returned in the units that are used in the header file.
These may be microns, nanometers or ???
"""
        return self.wavelength[index]

    def resampled(self, w):
        return envi2.resample.resample(self.spectrum, self.wavelength, w)

    def _index(self, s):
        """Translates any index or range of indices to the proper spectrum index.
It handles integers, floats, strings, slices and sequences.
"""
        if s is None:
            return None
        elif type(s) == slice:
            return slice(self._index(s.start), self._index(s.stop), s.step)
        elif isinstance(s, float):
            return self.wavelength2index(s)
        elif isinstance(s, collections.abc.Sequence) or isinstance(s, numpy.ndarray):
            return list(map(self._index, s))
        else:
            return s

    def __getitem__(self, i):
        """The Spectrum object takes 1 index.
The index can be a slice.
"""
        if i == Ellipsis:
            return self.spectrum
        else:
            # one argument, assume we want a value
            return self.spectrum[self._index(i)]
##        else:
##            raise IndexError, 'invalid index'

    def __len__(self):
        return len(self.wavelength)

    def __call__(self, wav):
        """Returns the band with given wavelength.
This assumes that the spectrum does have wavelengths.

A numpy array will be returned.
Use as follows: band = spec(wavelength)

There is no check on units. There is no check on whether
the returned band is close to the requested band.
"""
        return self[self.wavelength2index(wav)]

    def save(self, dname):
        """Save a spectrum to a given directory."""
        if self.name:
            fname = os.path.join(dname, self.name.translate(str.maketrans({'/':'_'}))+'.txt')
            f = open(fname, "w")
            f.write("# %s\n" % (self.name))
            if self.description:
                f.write("# %s\n" % (self.description))
            for w, s in zip(self.wavelength, self.spectrum):
                f.write("%f %f\n" % (w, s))
            f.close()

#################################################################################
#################################################################################
##
## Class AscSpeclib
##
            
class AscSpeclib:
    def __init__(self, dname, recursive=False):
        """Constructor of class AscSpeclib.
dname   - directory on disk
"""
        self.spectra = []
        self.recursive = recursive
        self.dname = dname

        if isinstance(dname, list): # list
            if isinstance(dname[0], str): # list of dirs
                self._from_list(dname)
            else: # list of spectra ?
                for s in dname:
                    self.spectra_append(s)
        elif os.path.isdir(dname):  # directory
            self._from_files(dname, recursive)
        elif os.path.isfile(dname): # one file
            try:
                self.read_envi(dname)  # try ENVI Speclib first
            except ValueError:
                self.spectra_append(self.read_spectrum(dname))
        
        self.spectra.sort(key=lambda s: s.name.lower())

    def __getitem__(self, i):
        """The Speclib object can take 1 or 2 indices.

1 index     assumes we want a spectrum
2 indices   assumes we want a value

Indices follow the BIP principle and must be given as (spectrum, band).

All indices can be slices.

Spectrum names can also be used as indices.
"""
        if i == Ellipsis:
            return self.spectra
        elif type(i)!=tuple:
            # one argument, assume we want a spectrum
            return self.spectra[self._spec_index(i)]
        elif len(i)==2:
            # two arguments, assume we want a value
            s, b = i
            return self.spectra[self._spec_index(s)].spectrum[b]
        else:
            raise IndexError('invalid index')

##    def __setitem__(self, i, value):
##        """The Speclib object can take 1 or 2 indices.
##
##1 index     assumes we set a spectrum
##2 indices   assumes we set a value
##
##Indices follow the BIP principle and must be given as (spectrum, band).
##
##All indices can be slices.
##
##Spectrum names can also be used as indices.
##"""
##        if i == Ellipsis:
##            self.data[...] = value
##        elif type(i)!=tuple:
##            # one argument, assume we want a spectrum
##            self.data[self._spec_index(i), :] = value[:]
##        elif len(i)==2:
##            # two arguments, assume we want a value
##            s, b = i
##            self.data[self._spec_index(s), b] = value
##        else:
##            raise IndexError, 'invalid index'

    def __len__(self):
        """Returns the number of spectra in the Spectral library.
"""
        return len(self.spectra)

##    def __del__(self):
##        self.data.sync()

##    def sync(self):
##        self.data.sync()
##
##    def flush(self):
##        self.data.flush()

##    def _to_file(self, fname):
##        """Sets up the writable memory map to the given file fname.
##"""
##        h = self.header
##        shape = (h.lines, h.samples)
##        self.data = numpy.memmap(fname,mode='w+',shape=shape,
##                           dtype=h.data_type)

    def _glob_files(self, dname, ext, recursive=False):
        if recursive:
            fnames = glob.glob(os.path.join(dname, '**/*.'+ext), recursive=True)
        else:
            fnames = glob.glob(os.path.join(dname, '*.'+ext))
##        fnames = fnames + glob.glob(os.path.join(dname, '?', '*.'+ext))
##        fnames = fnames + glob.glob(os.path.join(dname, '*', '?', '*.'+ext))
        return fnames        

    def spectra_append(self, s):
        if s:
            self.spectra.append(s)

    def _from_files(self, dname, recursive=False):
        """Reads spectra from files in directory dname.
"""
        # heck, try them all!
        fnames = []
        fnames.extend(self._glob_files(dname, 'asc', recursive))
        fnames.extend(self._glob_files(dname, 'txt', recursive))
        fnames.extend(self._glob_files(dname, 'dat', recursive))
        fnames.extend(self._glob_files(dname, 'tab', recursive))
        fnames.extend(self._glob_files(dname, 'sco', recursive))
        fnames.extend(self._glob_files(dname, 'asd', recursive))
        fnames.extend(self._glob_files(dname, '[0-9][0-9][0-9]', recursive))

        if 'win' not in sys.platform:
            fnames.extend(self._glob_files(dname, 'ASC', recursive))
            fnames.extend(self._glob_files(dname, 'TXT', recursive))
            fnames.extend(self._glob_files(dname, 'DAT', recursive))
            fnames.extend(self._glob_files(dname, 'TAB', recursive))
            fnames.extend(self._glob_files(dname, 'SCO', recursive))
            fnames.extend(self._glob_files(dname, 'ASD', recursive))

        for ext in OPUS_DATATYPES:
            fnames.extend(self._glob_files(dname, ext, recursive))
            
        for fname in fnames:
            self.spectra_append(self.read_spectrum(fname))

    def _from_list(fnames):
        for fname in fnames:
            self.spectra_append(self.read_spectrum(fname))

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
            for i in range(len(self.spectra)):
                if s.lower() in self.spectra[i].name.lower():
                    return i
            return None
        elif isinstance(s, collections.abc.Sequence) or isinstance(s, numpy.ndarray):
            return list(map(self._spec_index, s))
        else:
            return s

    def spec_match(self, name, matchall=True):
        """Returns a spectral library with a subset of spectra that matches
the given name.

With matchall False only the first match is returned.
With matchall equal to True all matches are returned."""
        result = []
        for i in range(len(self)):
            sname = self[i].name
            if name.lower() in sname.lower():
                if matchall:
                    result.append(self[i])
                else:
                    return self[i]
        return AscSpeclib(result)

    # functions for getting data
    def get_band(self, s, b):
        """Get the value of spectrum s at band b.
"""
        return self[s, b]

    def get_value(self, s, b):
        """Get the value of spectrum s at band b.
"""
        return self[s, b]

    def get_spectrum(self, s):
        """Get spectrum s."""
        return self[s].spectrum

##    #
##    # Some distance measures as methods of the class
##    #  input: two coordinate pairs (tuples!)
##    #  output: the distance
##    #
##    
##    def spectral_angle(im, t1, t2):
##        s1 = im.get_spectrum(t1)
##        s2 = im.get_spectrum(t2)
##        return spectral.spectral_angle(s1, s2)
##
##    def euclidean_distance(im, t1, t2):
##        s1 = im.get_spectrum(t1)
##        s2 = im.get_spectrum(t2)
##        return spectral.euclidean_distance(s1, s2)
##
##    def intensity_difference(im, t1, t2):
##        s1 = im.get_spectrum(t1)
##        s2 = im.get_spectrum(t2)
##        return spectral.intensity_difference(s1, s2)
##
##    def spectral_information_divergence(im, t1, t2):  # a.k.a. SID
##        s1 = im.get_spectrum(t1)
##        s2 = im.get_spectrum(t2)
##        return spectral.spectral_information_divergence(s1, s2)
##
##    def bray_curtis_distance(im, t1, t2):
##        s1 = im.get_spectrum(t1)
##        s2 = im.get_spectrum(t2)
##        return spectral.bray_curtis_distance(s1, s2)

    def wavelength2index(self, s, wavelength):
        """Returns the index of the band with the closest wavelength number.

wavelength is the required wavelength.

Note that the units used should reflect the units used in the header file.
Currently there is no check on whether the given units make any sense with
relation the the wavelengths supplied with the image.
"""
        return self[s].wavelength2index(wavelength)

    def index2wavelength(self, s, index):
        """Returns the wavelength of the band with this index.

The wavelength is returned in the units that are used in the header file.
These may be microns, nanometers or ???
"""
        return self[s].index2wavelength(index)

    def wavelength(self, s):
        """Return wavelengths of spectrum"""
        return self[s].wavelength

    def wavelength_units(self, s):
        """Return wavelength units of spectrum"""
        wav = self[s].wavelength
        if wav[0] > wav[1]:
            return 'Wavenumbers'
        elif wav[0] > 100:
            return 'Nanometers'
        elif wav[-1] < 100:
            return 'Micrometers'
        else:
            return 'Unknown'

    def spectrum(self, s):
        """Return spectral values of spectrum"""
        return self[s].spectrum

    def name(self, s):
        """Return name of spectrum"""
        return self[s].name

    def names(self):
        """Return names of spectra"""
        return [x.name for x in self.spectra]

    def description(self, s):
        """Return description of spectrum"""
        return self[s].description

    def resampled(self, s, w):
        return self[s].resampled(w)

    def read_spectrum(self, fname):
        f = open(fname, 'rb') # first try binary
        data = f.read(1000)
        f.close()
        
        if len(data) == 0:
            return None

        if data[0:3].lower() in asdread.MAGIC: # assume ASD format
            w, r, description = asdread.asd_read_spectrum(fname)
            return spectrum.Spectrum(name=os.path.basename(fname), wavelength=numpy.array(w),
                                     spectrum=numpy.array(r), description=description)

        try:
            f = open(fname, 'r') # second, try text
            data = f.readlines()
            f.close()
        except:       # UnicodeDecodeError, this needs work!
            return None

        if len(data) == 0:
            return None

        if 'PDS' in data[0]: # assume CRISM ascii speclib format
            w, r, description = crismread.crism_read_spectrum(fname)
            return spectrum.Spectrum(name=os.path.basename(fname), wavelength=numpy.array(w),
                                     spectrum=numpy.array(r), description=description)
        elif 'USGS' in data[0]: # assume USGS ascii speclib format
            description = data[14].strip()
            data = data[16:]

            result = []
            
            for line in data:
                w, r, d = line.strip().split()
                if w != DELETED_NUMBER and r != DELETED_NUMBER:
                    result.append([float(w), float(r)])
        elif 'splib07a' in data[0]:
            description = data[0].strip()
            try:
                r = numpy.array(list(map(float, data[1:])))
            except:
                return None
            r[numpy.where(r==float(DELETED_NUMBER))] = numpy.nan
            if 'ASD' in description:
                w = speclib07.ASD
            elif 'AVIRIS' in description:
                w = speclib07.AVIRIS
            elif 'BECK' in description:
                w = speclib07.BECK
            elif 'NIC4' in description:
                w = speclib07.NIC4
            else:
                return None
            return spectrum.Spectrum(name=os.path.basename(fname), wavelength=numpy.array(w),
                                     spectrum=r, description=description)
        else:   # assuming 2-column data, cross your fingers...
##            description = data[0] # maybe there's something in line 1?

            description = ''
            result = []
            
            for line in data:
                if line.startswith('#'): # comment?
                    if description:
                        description = description + '\n' + line.strip('# \n')
                    else:
                        description = line.strip('# \n')
                    continue
                if ',' in line:
                    words = line.strip().split(',')
                else:
                    words = line.strip().split()
                try:
                    w, r = words[0].strip(), words[1].strip()
                except IndexError:
                    continue
                try:
                    if w != DELETED_NUMBER and r != DELETED_NUMBER:
                        result.append([float(w), float(r)])
                except ValueError:
                    continue

        if result:
            w, r = list(zip(*result))
            if self.recursive:
                return spectrum.Spectrum(name=fname[len(self.dname)+1:],
                                         wavelength=numpy.array(w),
                                         spectrum=numpy.array(r), description=description)
            else:
                return spectrum.Spectrum(name=os.path.basename(fname), wavelength=numpy.array(w),
                                         spectrum=numpy.array(r), description=description)
        else:
            return None

    def save(self, dname):
        """Save all the spectra of the spectral library to a directory"""
        for s in self:
            s.save(dname)

    def save_as_envi(self, fname, wavelength=None):
        if len(self)==0:
            return
        
        if wavelength is None: # if no wavelengths are supplied take the first spectrum
            wavelength = self[0].wavelength

        sl = envi2.New(fname, file_type=envi2.constants.ENVI_Speclib,
                       bands=len(wavelength), lines=len(self), samples=1,
                       interleave=envi2.constants.ENVI_BSQ,
                       data_type='d', wavelength=wavelength,
                       spectra_names=self.names(), byte_order=0)

        for i, S in enumerate(self):
            sl[i, 0, :] = S.resample(w=wavelength).spectrum

    def read_envi(self, fname):
        sl = envi2.Open(fname)
        for j in range(sl.lines):
            self.spectra_append(spectrum.Spectrum(name=sl.header.spectra_names[j], wavelength=sl.wavelength,
                                         spectrum=sl[j,0,:]))

##def subset_speclib(sl, w1, w2):
##    wav, refl = sl
##    i1 = wav.searchsorted(w1)
##    i2 = wav.searchsorted(w2)

if __name__ == '__main__':
    from pylab import *

    speclib = AscSpeclib('/home/bakker/Speclib06/ASCII/M')

    asl = speclib.spec_match('alunite')

##    for s in sel:
##        plot(s.wavelength, s.spectrum, label=s.name)

##    legend()
    
##    wav, refl = read_speclib('M/actinolite_hs22.119.asc')
##
##    wav2 = arange(2, 5.2, 0.01)
##
##    refl2 = envi2.resample.resample(refl, wav, wav2)
##
##    plot(wav2, refl2)
