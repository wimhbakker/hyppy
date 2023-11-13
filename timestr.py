#!/usr/bin/python3
## timestr.py
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

import re

time_pattern = re.compile(r'[12][09]\d\d[01]\d[0123]\d[012]\d[012345]\d')

def time_from_string(s):
    l = time_pattern.findall(s)
    for t in l:
        t = t[:4], t[4:6], t[6:8], t[8:10], t[10:]
        year, month, day, hour, minute = [int(e) for e in t]
        if not 1900<=year<=2099: continue
        if not 1<=month<=12: continue
        if not 1<=day<=31: continue
        if not hour<=24: continue
        if not minute<=60: continue
        return year, month, day, hour, minute
    return None
