#!/usr/bin/python3
## readconfig.py
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

ENVI2CONFIG='hyppymenu.cfg'

def read_config(fname=ENVI2CONFIG):
    if os.path.isfile(fname):
        f = open(fname)
        data = f.readlines()
        f.close()
        result = []
        for line in data:
            line = line.strip()
            if line:
                if line[0]=='#': # = comment
                    continue
                menuitem, action = line.split(';')
                menuitem = menuitem.strip()
                action = action.strip()
                result.append((menuitem, action))
            else:
                result.append(None)
    else:
        return None

    return tuple(result)
