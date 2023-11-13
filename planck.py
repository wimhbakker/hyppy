#!/usr/bin/python3
## planck.py
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

import math

from pylab import *

H = 6.626068e-34 # Planck's constant
C = 2.99792458e8 # speed of light
K = 1.3806504e-23 # Boltzmann's constant

SOLAR_T = 5780 # temp. of sun in Kelvin

# wavelength l in meter!
# temperature T in Kelvin

#### incorrect version!
##def planck(l, T):
##    c1 = 2 * math.pi * H * C**2
##    c2 = H * C / K
##    return c1 / (l**5 * (math.e**(c2/(l * T)) - 1.0))

def planck(l, T):
    c1 = 2 * H * C**2
    c2 = H * C / K
    return c1 / (l**5 * (math.e**(c2/(l * T)) - 1.0))

def inverse_planck(l, I):
    K1 = 2 * H * C**2 * l**-5
    K2 = (H * C) / (K * l)
    return K2 / log((K1 / I) + 1)

if __name__ == '__main__':
    # main
    xs = arange(0.300, 15.000, 0.001)
    ys = []

    for l in xs:
        ys.append(planck(l * 1e-6, 5000.0))

##    plot(xs, ys)

    for temp in [320.0, 300.0, 268.0, 210.0, 186.0]:
        ys = []

        for l in xs:
            ys.append(planck(l * 1e-6, temp) * 1e-6) # per micron

        plot(xs, ys, label=str(temp))

    legend()
