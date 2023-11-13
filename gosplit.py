#!/usr/bin/python3
## gosplit.py
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

### version 1
##def gosplit1d(x0, x1):
##    d = x1 - x0
##    if d == 1:
##        return (None,)
##    elif d == 2:
##        return (x0+1,)
##    elif d == 3:
##        return (x0+1,x0+2)
##    elif d == 4:
##        return (x0+1, x0+2, x0+3)
##    elif d == 5:
##        return (x0+2, x0+3)
##    elif d == 6:
##        return (x0+2, x0+3, x0+4)
##    elif d == 7:
##        return (x0+3, x0+4)
##    elif d == 8:
##        return (x0+3, x0+4, x0+5)
##    else:
##        return (x0+int(round(.382*d)), x0+int(0.5*d), x0+int(round(.618*d)))
##    
##def gosplit1d(x0, x1):
##    d = x1 - x0
##    if d == 1:
##        return (None,)
##    elif d == 2:
##        return (x0+1,)
##    elif d == 3:
##        return (x0+1,x0+2)
##    elif d == 4:
##        return (x0+1, x0+3, x0+2)
##    elif d == 5:
##        return (x0+2, x0+3)
##    elif d == 6:
##        return (x0+2, x0+4, x0+3)
##    elif d == 7:
##        return (x0+3, x0+4)
##    elif d == 8:
##        return (x0+3, x0+5, x0+4)
##    else:
##        return (x0+int(round(.382*d)), x0+int(round(.618*d)), x0+int(0.5*d))
##
from random import randint

def gosplit1d(x0, x1):
    d = x1 - x0
    if d == 1:
        t = (None,)
    elif d == 2:
        t = (x0+1,)
    elif d == 3:
        t = (x0+1,x0+2)
    elif d == 4:
        t = (x0+1, x0+3)
    elif d == 5:
        t = (x0+2, x0+3)
    elif d == 6:
        t = (x0+2, x0+4)
    elif d == 7:
        t = (x0+3, x0+4)
    elif d == 8:
        t = (x0+3, x0+5)
    else:
        t = (x0+int(round(.382*d)), x0+int(round(.618*d)))
    if len(t)==2 and randint(0,1):
        return (t[1], t[0])
    else:
        return t

def gosplit1d_regular(x0, x1):
    d = x1 - x0
    if d == 1:
        t = (None,)
    else:
        t = (x0+d//2,)
    return t
    
def gosplit(t):
    x0, x1, y0, y1 = t
    result = []
    for j in gosplit1d(y0, y1):
        for i in gosplit1d(x0,x1):
            result.append((i, j))
    return tuple(result)
