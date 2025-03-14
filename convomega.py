#!/usr/bin/python3
## convomega.py
##
## Copyright (C) 2025 Wim Bakker
##
##        Created: 20250314
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
##     Netherlands
##

import os
import sys

import envi2
from envi2.constants import * 

os.environ["TQDM_MININTERVAL"] = "20.0"
os.environ["TQDM_MAXINTERVAL"] = "60.0"

# Package import
import omegapy
import omegapy.omega_data as od
print(f"{od.get_omega_bin_path()}")
print(f"{od.get_omega_py_path()}")

print("setting paths") # needed for a number of data files...
od.set_omega_py_path(os.path.dirname(omegapy.__file__))

print(f"{od.get_omega_py_path()}")

import omegapy.omega_plots as op
#import omegapy.useful_functions as uf

def message(s):
    print(s)

def read_omega(filename, message=message, progress=None):
    message("Converting")
    # OMEGA file importation (ORB0979_3)
    od.set_omega_bin_path(os.path.dirname(filename))
    print(f"{od.get_omega_bin_path()}")
    
    omega = od.OMEGAdata(os.path.basename(filename)[3:]) # strip off 'ORB'

    ##print("--Atm. correction")
    ### Atmospheric correction
    ##omega_corr_atm = od.corr_atm(omega)

    # Simultaneous Atmospheric & Thermal corrections (for the use of the L-channel)
    # > Use the `npool` argument to control the number of simultaneous processes 
    # > used to compute the thermal correction 
    # > (e.g., npool=15 is usually a nice choice if your system can handle it)
    # > Note: multiprocessing is currently not available for Windows

    message("Starting Atm. & Therm. correction")
    omega_corr_therm_atm = od.corr_therm_atm(omega, npool=1)

    ##print("--Thermal correction only")
    ### Thermal correction only
    ##omega_corr_therm = od.corr_therm(omega, npool=1)

    message("Masking")
    # OMEGA mask to hide bad pixels / calibration lines
    mask = od.omega_mask(
        omega_corr_therm_atm, 
        hide_128=True, 
        emer_lim=10, 
        inci_lim=70, 
        tempc_lim=-194, 
        limsat_c=500
        )

    message("Interactive display")
    # Interactive display of the observation (@ λ = 1.085 µm)
    op.show_omega_interactif_v2(
        omega_corr_therm_atm, 
        lam=1.085, 
        cmap='Greys_r', 
        vmin=0, 
        vmax=0.5, 
        polar=False,
        mask=mask
        )

##    print("--search for band")
##    # Search for the index of λ = 1.085 µm in the wavelength array
##    i_lam = uf.where_closer(1.085, omega.lam)

    ######### Export #########
    lines, samples, bands = omega_corr_therm_atm.cube_rf.shape
    data_type = omega_corr_therm_atm.cube_rf.dtype

    byte_order = 0 if sys.byteorder == 'little' else 1

    wavelength = omega_corr_therm_atm.lam

    name = omega_corr_therm_atm.name

    message(f"Exporting {name}")

    ###############################################
    if hasattr(omega_corr_therm_atm, "cube_rf"):
        cube_rf = omega_corr_therm_atm.cube_rf    

        message("Saving reflectance cube")
        im = envi2.New(filename + "_cube_rf", file_type=ENVI_Standard, lines=lines, samples=samples, \
                       bands=bands, data_type=data_type, byte_order=byte_order, \
                       wavelength=wavelength, \
                       interleave=ENVI_BIP)

        im[...] = cube_rf[...]

        del im

    ###############################################

    if hasattr(omega_corr_therm_atm, "alt"):
        alt = omega_corr_therm_atm.alt
        
        message("Saving altitude")
        im = envi2.New(filename + "_alt", file_type=ENVI_Standard, lines=lines, samples=samples, \
                   bands=1, data_type=alt.dtype, byte_order=byte_order, \
                   band_names=["altitude"], \
                   interleave=ENVI_BIP)

        im[:, :, 0] = alt[...]

        del im

    ###############################################

    if hasattr(omega_corr_therm_atm, "alt_l"):
        alt_l = omega_corr_therm_atm.alt_l
        
        message("Saving altitude L")
        im = envi2.New(filename + "_alt_l", file_type=ENVI_Standard, lines=lines, samples=samples, \
                   bands=1, data_type=alt_l.dtype, byte_order=byte_order, \
                   band_names=["altitude L"], \
                   interleave=ENVI_BIP)

        im[:, :, 0] = alt_l[...]

        del im

    ###############################################

    if hasattr(omega_corr_therm_atm, "alt_v"):
        alt_v = omega_corr_therm_atm.alt_v
        
        message("Saving altitude V")
        im = envi2.New(filename + "_alt_v", file_type=ENVI_Standard, lines=lines, samples=samples, \
                   bands=1, data_type=alt_v.dtype, byte_order=byte_order, \
                   band_names=["altitude V"], \
                   interleave=ENVI_BIP)

        im[:, :, 0] = alt_v[...]

        del im

    ###############################################

    if hasattr(omega_corr_therm_atm, "lat") and hasattr(omega_corr_therm_atm, "lon"):
        lat = omega_corr_therm_atm.lat
        lon = omega_corr_therm_atm.lon

        message("Saving latitude and longitude")
        im = envi2.New(filename + "_latlon", file_type=ENVI_Standard, lines=lines, samples=samples, \
                   bands=2, data_type=lat.dtype, byte_order=byte_order, \
                   band_names=["latitude", "longitude"], \
                   interleave=ENVI_BIP)

        im[:, :, 0] = lat[...]
        im[:, :, 1] = lon[...]

        del im

    ###############################################

    if hasattr(omega_corr_therm_atm, "lat_l") and hasattr(omega_corr_therm_atm, "lon_l"):
        lat_l = omega_corr_therm_atm.lat_l
        lon_l = omega_corr_therm_atm.lon_l

        message("Saving latitude and longitude L")
        im = envi2.New(filename + "_latlon_l", file_type=ENVI_Standard, lines=lines, samples=samples, \
                   bands=2, data_type=lat_l.dtype, byte_order=byte_order, \
                   band_names=["latitude L", "longitude L"], \
                   interleave=ENVI_BIP)

        im[:, :, 0] = lat_l[...]
        im[:, :, 1] = lon_l[...]

        del im

    ###############################################

    if hasattr(omega_corr_therm_atm, "lat_v") and hasattr(omega_corr_therm_atm, "lon_v"):
        lat_v = omega_corr_therm_atm.lat_v
        lon_v = omega_corr_therm_atm.lon_v

        message("Saving latitude and longitude V")
        im = envi2.New(filename + "_latlon_v", file_type=ENVI_Standard, lines=lines, samples=samples, \
                   bands=2, data_type=lat_v.dtype, byte_order=byte_order, \
                   band_names=["latitude V", "longitude V"], \
                   interleave=ENVI_BIP)

        im[:, :, 0] = lat_v[...]
        im[:, :, 1] = lon_v[...]

        del im


    ###############################################

    if hasattr(omega_corr_therm_atm, "surf_temp"):
        surf_temp = omega_corr_therm_atm.surf_temp
        
        message("Saving surface temperature")
        im = envi2.New(filename + "_surf_temp", file_type=ENVI_Standard, lines=lines, samples=samples, \
                   bands=1, data_type=surf_temp.dtype, byte_order=byte_order, \
                   band_names=["surface temperature"], \
                   interleave=ENVI_BIP)

        im[:, :, 0] = surf_temp[...]

        del im


if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='convomega.py',
        description='Convert OMEGA image to ENVI format.')

#    parser.add_argument('-f', action='store_true', dest='force',
#                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name', required=True)
#    parser.add_argument('-o', dest='output', help='output file name', required=True)

    options = parser.parse_args()

##    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    read_omega(options.input)

