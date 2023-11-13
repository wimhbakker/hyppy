## __init__.py
##
## Copyright (C) 2018 Wim Bakker
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
## Data was copied from the USGS and must be credited accordingly
## https://speclab.cr.usgs.gov/spectral-lib.html
##

import os

f = open(os.path.join(os.path.dirname(__file__), 'splib07a_Wavelengths_ASD_0.35-2.5_microns_2151_ch.txt'), 'r')
data = f.readlines()
ASD = list(map(float, data[1:]))
f.close()

f = open(os.path.join(os.path.dirname(__file__), 'splib07a_Wavelengths_AVIRIS_1996_0.37-2.5_microns.txt'), 'r')
data = f.readlines()
AVIRIS = list(map(float, data[1:]))
f.close()

f = open(os.path.join(os.path.dirname(__file__), 'splib07a_Wavelengths_BECK_Beckman_0.2-3.0_microns.txt'), 'r')
data = f.readlines()
BECK = list(map(float, data[1:]))
f.close()

f = open(os.path.join(os.path.dirname(__file__), 'splib07a_Wavelengths_NIC4_Nicolet_1.12-216microns.txt'), 'r')
data = f.readlines()
NIC4 = list(map(float, data[1:]))
f.close()

del f, data, os
