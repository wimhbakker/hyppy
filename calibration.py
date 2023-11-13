#!/usr/bin/python3
## calibration.py
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

from gregorian import *
from numpy import array

YEARS = [1999, 2000, 2001, 2002, 2003, 2004]

cname = 'Meteosat/IR_Calibration_info_'

mon2mon = {'Jan':1,
           'Feb':2,
           'Mar':3,
           'Apr':4,
           'May':5,
           'Jun':6,
           'Jul':7,
           'Aug':8,
           'Sep':9,
           'Oct':10,
           'Nov':11,
           'Dec':12}

def read_calibration(year, name):
    f = open(name)
    data = f.readlines()
    f.close()

    calib = []
    for line in data:
        dayofyear, daymonth, slot, coeff, spacecount = line.strip().split()
        day, month = daymonth.split('-')
        day = int(day)
        month = mon2mon[month]
        hour = (int(slot)-1)/2.0    # does it include the slot or not?
        minute = int(hour%1 * 60)
        hour = int(hour)
        coeff = float(coeff)
        spacecount = float(spacecount)

        # Proleptic Gregorian time...
        ltime = to_linear_time(year, month, day, hour, minute)
        
        calib.append((ltime, year, month, day, hour, minute, coeff, spacecount))
    return calib

calibration = []
for year in YEARS:
    name = cname + str(year) + '.txt'
    calibration.extend(read_calibration(year, name))

calibration_index = array([x[0] for x in calibration])

def get_coeffs(year, month, day, hour, minute):
    # Proleptic Gregorian time...
    ltime = to_linear_time(year, month, day, hour, minute)

    # add 4 minutes to be sure to fall inside a slot
    index = calibration_index.searchsorted(ltime+0.003)

    if index > 0:
        index = index - 1
    return calibration[index]


if __name__=='__main__':
    print(get_coeffs(2003, 2, 1, 11, 0))
    #(731246.0625, 2003, 1, 31, 1, 30, 0.074721999999999997, 5.0)
