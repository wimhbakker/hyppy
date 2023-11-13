#!/usr/bin/python3
## gregorian.py
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

# import standard modules
##import os
##import glob
##import sys
##
### import image and array support
##import Image
##import numpy
##
### the envi2 module for writing ENVI format images
##import envi2
##import envi2.constants

# Here comes trouble!
import datetime

# define a generic time zone object
class UTC(datetime.tzinfo):
    def __init__(self, offset):
        self.offset = offset
    def utcoffset(self, dt):
        return datetime.timedelta(hours=self.offset)
    def dst(self, dt):
        return datetime.timedelta(0)
    def tzname(self, dt):
        return "UTC%+d" % (self.offset,)

# set time zone to UTC+0
tzUTC0 = UTC(0)

# Functions for time conversion

def to_linear_time_dt(dt):
    ''' takes a datetime object
returns prolectic Gregorian ordinal (=days since 01-01-0001)
plus a fraction of the day
'''
    return dt.toordinal() + (((dt.second/60.0)+dt.minute)/60.0+dt.hour)/24.0

def to_linear_time(year, month, day, hour, minute):
    ''' takes 5 arguments
returns prolectic Gregorian ordinal (=days since 01-01-0001)
plus a fraction of the day
'''
    dt = datetime.datetime(year, month, day, hour, minute, 0, 0, tzinfo=tzUTC0)
    return dt.toordinal() + (((dt.second/60.0)+dt.minute)/60.0+dt.hour)/24.0

def from_linear_time(lt):
    '''takes a prolectic Gregorian ordinal plus fraction of day
returns a datetime object
'''
    return datetime.datetime.fromordinal(int(lt)) + datetime.timedelta(lt%1)
    
####    print t
##    year, month, day, hour, minute = map(int, (t[:4], t[4:6], t[6:8], t[8:10], t[10:]))
##
##    dt = datetime.datetime(year, month, day, hour, minute, 0, 0, tzinfo=tzUTC0)
##
##    ltime = to_linear_time(dt)
####    print ltime
####    print from_linear_time(ltime)
##    
##    # add linear time to the list of 'wavelengths'
##    wavelength.append(ltime)
##
