
# HypPy Readme

## HypPy Overview

Hyperspectral Python (HypPy) is a collection of tools developed at the University of Twente. HypPy has adopted the ENVI file format as the image format.

## HypPy Features

    Viewer for ENVI format hyperspectral images.
    Viewer for spectra and spectral libraries.
    Conversion programs.
    Simple spectral tools.
    Band Math.
    Spectral Math.
    Minimum Wavelength mapping.
    Destriping
    PCA and inverse PCA.
    Hyperspectral filters.
    Spectral Angle Mapper (SAM).
    Rule image classifier.
    Linear Unmixing (fully constrained).
    Tools for processing Omega images from the Mars Express.
    Command-line interface for scripting.
    Manuals:
        graphical user-interface
        scripting with HypPy
        programming interface
        spectral math 

## HypPy Prerequisites

In order to run, HypPy needs Python3 plus additional modules. These can be picked up by installing the following packages:

    Python
    NumPy
    SciPy
    PIL/Pillow (Python imaging libary)
    Matplotlib
    OWSlib (optional, needed for WMS get)
    colour-science (optional, for colour science calculations)
    PySptools (for Linear Unmixing)
    pyproj (for conversion to KML) 
    netCDF4 (for conversion of EMIT data)
    h5py (HDF5 format for PRISMA data)
    rasterio (for the TIF files of ENMAP)

## HypPy Download

HypPy3 has been ported to Python3 and current development and bug-fixes are only continued on the HypPy3 version.

The following packages are needed on Linux:

    python3
    python3-tk
    python3-numpy
    python3-scipy
    python3-pil
    python3-pil.imagetk
    python3-matplotlib
    python3-owslib
    pip install colour-science
    pip install pysptools
    pip install pyproj 
    pip install netCDF4
    pip install h5py
    pip install rasterio

Since there's no regular installer yet, the next best thing you can do is to create a new directory for HypPy and to unpack the tar file into this directory:

    $ cd
    $ mkdir HypPy
    $ cd HypPy
    $ tar zxvf ../hyppy.tar.gz
    $ python tkHypPy.pyw

## HypPy Installation, Windows

The easiest way to run HypPy on Windows is to pick up a Portable Python, for instance [WinPython](https://sourceforge.net/projects/winpython/). WinPython is a complete portable scientific Python 3 distribution for Windows.

Download the latest WinPython with Python 3 and extract the package into a directory. This may be any directory of your choice; that's why it's called a portable Python.

From the WinPython directory run the WinPython control panel.exe. Go to the Advanced tab and Register your WinPython.

There is no uninstall for WinPython. Should you want to get rid of the WinPython then you can do that by simply unregistering first using the WinPython control panel and then to delete the entire WinPython directory tree.

Alternatively, you can install Python 3 and all the required packages yourself.

Next, download the HypPy3 zip file. Create a directory for HypPy. Unzip the hyppy3.zip into this directory.

To start HypPy go to the HypPy directory and double-click the tkHypPy.pyw. The HypPy main menu will pop up in the upper-right corner.

(If you need installers for 64-bit Windows systems, these can be found at [this site maintained by Christoph Gohlke](https://www.cgohlke.com/).)

(Tip: if Python installers hang on Windows you can trying running the installer as administrator; right-click the installer and click Run as administrator.)

## HypPy Installation, other systems

Install Python 3 plus packages

Pick up the zip file, create a directory HypPy, unzip the hyppy.zip into this directory. To run HypPy double-click the file tkHypPy.pyw.

## HypPy Documentation

The documentation of HypPy is contained by the code. The documentation is split into three levels:

1. The User Manual for the graphical user-interface (GUI). 
2. The Scripting Manual for the conmmandline-interface (CLI). 
3. The Programming Manual for Pythonites.
4. The Spectral Math manual for expressions in spectral math.

As the package is in development, the documentation is never really finished.

## HypPy Contact

HypPy is distributed under the [GNU General Public License (GNU-GPL)](http://www.gnu.org/licenses/gpl.html). We don't claim that this software is fit for any purpose. HypPy does have its limitations in the sense that the file size on 32-bit systems is limited to 2 GB (no limits on 64-bit systems) and that the display program was not designed to handle huge images. However, if you find HypPy useful, or if you have comments or contributions, please, send us an e-mail.

If you produce any scientific output using HypPy, please consider citing the references mentioned below.

## Contributors

    Frank van Ruitenbeek
    Chris Hecker
    Harald van der Werff
    Jelmer Oosthoek

## References

- WH Bakker, KS Schmidt, *Hyperspectral edge filtering for measuring homogeneity of surface cover types*, ISPRS Journal of Photogrammetry and Remote Sensing, vol. 56, ed. 4, pp 246-256, 2002, Elsevier, [DOI](http://dx.doi.org/10.1016/S0924-2716(02)00060-6)

- WH Bakker, FJA van Ruitenbeek, HMA van der Werff, TE Zegers, JHP Oosthoek, SH Marsh, FD van der Meer, *Processing OMEGA/Mars Express hyperspectral imagery from radiance-at-sensor to surface reflectance*, Planetary and Space Science, vol. 90, pages 1-9, 2014, Pergamon, [DOI](http://dx.doi.org/10.1016/j.pss.2013.11.007)

- FJA van Ruitenbeek, WH Bakker, HMA van der Werff, TE Zegers, JHP Oosthoek, ZA Omer, SH Marsh, FD van der Meer, *Mapping the wavelength position of absorption features between 2.1 and 2.4 μm: a new method for exploratory analysis of OMEGA/Mars Express hyperspectral imagery*, Planetary and Space Science, Volume 101, 15 October 2014, Pages 108-117, Pergamon, [DOI](http://dx.doi.org/10.1016/j.pss.2014.06.009)

- F van der Meer, V Kopačková, L Koucká, HMA van der Werff, FJA van Ruitenbeek, WH Bakker, *Wavelength feature mapping as a proxy to mineral chemistry for investigating geologic systems: An example from the Rodalquilar epithermal system*, International Journal of Applied Earth Observation and Geoinformation, Volume 64, 2018, Pages 237-248, Elsevier, [DOI](http://dx.doi.org/10.1016/j.jag.2017.09.008)

- C Hecker, FJA van Ruitenbeek, WH Bakker, BJ Fagbohun, Dean Riley, HMA van der Werff, FD van der Meer, 2019, *Mapping the wavelength position of mineral features in hyperspectral thermal infrared data*, International Journal of Applied Earth Observation and Geoinformation, 79, 133-140, [DOI](https://doi.org/10.1016/j.jag.2019.02.013) 

- C Hecker, FJA van Ruitenbeek, HMA van der Werff, WH Bakker, RD Hewson, FD van der Meer, *Spectral Absorption Feature Analysis for Finding Ore: A Tutorial on Using the Method in Geological Remote Sensing*, IEEE geoscience and remote sensing magazine, vol 7, issue 2, 2019, [DOI](https://doi.org/10.1109/MGRS.2019.2899193)

- FJA van Ruitenbeek, J Goseling, WH Bakker, KAA Hein, *Shannon entropy as an indicator for sorting processes in hydrothermal systems*, Entropy 22 (6), 656, [DOI](https://doi.org/10.3390/e22060656)

- RDPM Scafutto, H van der Werff, WH Bakker, F van der Meer, …, *An evaluation of airborne SWIR imaging spectrometers for CH4 mapping: Implications of band positioning, spectral sampling and noise*, International Journal of Applied Earth Observation and Geoinformation 94, 102233, [DOI](https://doi.org/10.1016/j.jag.2020.102233)

- W Bakker, F van Ruitenbeek, H van der Werff, C Hecker, A Dijkstra, F van der Meer. *Hyperspectral Python: HypPy*, Algorithms 2024, 17, 337, [DOI](https://doi.org/10.3390/a17080337)

*Wim Bakker*
