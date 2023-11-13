#!/usr/bin/python3
## entropy.py
##
## Copyright (C) 2021 Wim Bakker
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
##     Wim Bakker, <w.h.bakker@utwente.nl>
##     University of Twente, Faculty ITC
##     Hengelosestraat 99
##     7514 AE Enschede
##     Netherlands
##

import numpy as np
from scipy.stats import entropy

def hist_entropy(data, bins=256, range=None, density=True, base=2):
    hist, bin_edges = np.histogram(data, bins=bins, range=range, density=density)

    return entropy(hist, base=base)

