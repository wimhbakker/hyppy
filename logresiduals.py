#!/usr/bin/python3
#
# logresiduals.py
#
# Modified: WHB 20091105, make it NaN safe...
# Modified: WHB 20100210, include real Log Residuals using geometric means.
#
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

import envi2
import numpy
##from scipy.stats.stats import nanmean, nanstd
from numpy import nanmean, nanstd

try:
    from pylab import plot, title, xlabel, ylabel, ion, show, draw
    ion()
    HAS_PYLAB = True
except ImportError:
    HAS_PYLAB = False

LINEWIDTH = 1.0

def message(s):
    pass

def logresiduals(fin, fout, albedo=None, rlub=None, N=3.0,
                 sort_wavelengths=False, use_bbl=True,
                 message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

#    im2 = envi2.New('/tmp/znorm', hdr=im, interleave='bsq', data_type='d')
    if albedo:
        imalbedo = envi2.New(albedo, hdr=im, interleave='bsq', data_type='d',
                             bands=1, wavelength=None, bbl=None, fwhm=None,
                             band_names=['Albedo of %s' % (fin,)])

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    im3 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d', bbl=bbl)

    im2 = im3

    oldsettings = numpy.seterr(all='ignore')

    message('Pass 1: normalize spectra by albedo')
    
    if progress:
        progress(0.0)

    for j in range(im.lines):
        if progress:
            progress(j / float(im.lines))
        for i in range(im.samples):
            spec = im[j, i].astype('float')
            spec[numpy.where(spec<=0.0)] = numpy.nan
            # geometric mean
            m = numpy.e**nanmean(numpy.log(spec))  ## LOG + EXP

            im2[j, i] = spec / m

            if albedo:
                imalbedo[j, i] = m

    im2.flush()

    if albedo:
        del imalbedo
    
    message('\n')

    message('Pass 2: determine RLUB (ignore highest 1%)')
    message('Using %f Standard Deviations' % (N,))

    slub = numpy.zeros(im.bands)

    if progress:
        progress(0.0)

    for b in range(im2.bands):
        if progress:
            progress(b / float(im2.bands))
        band = im2[b].flatten().astype('float')
        band[numpy.where(band<=0.0)] = numpy.nan
        #geometric mean
        band = numpy.log(band)  ## LOG
        m = nanmean(band)
        s = nanstd(band)
#        mx = band.max()
##        band = band.flatten()
        # Take out any NaN's in the band...
        band = band[numpy.where(numpy.isnan(band)==False)]
        band.sort()
        mx = band[int(len(band)*0.99)]
        
        slub[b] = numpy.e**min((m + N * s), mx)  ## EXP

    message('\n')

    # Plot RLUB, if we can...
    if HAS_PYLAB:
        if hasattr(im, 'wavelength'):
            plot(im.wavelength, slub, linewidth=LINEWIDTH)
            xlabel('wavelength')
        else:
            plot(slub, linewidth=LINEWIDTH)
            xlabel('band')

        ylabel('RLUB')
        title('Robust Least Upper Bound')
        draw()

    # write RLUB to text file
    if rlub:
        ftxt = open(rlub, 'w')
        if hasattr(im, 'wavelength'):
            ftxt.write('Wavelength RLUB\n')
            for i in range(im.bands):
                ftxt.write('%f %f\n' % (im.wavelength[i], slub[i]))
        else:        
            ftxt.write('Band RLUB\n')
            for i in range(im.bands):
                ftxt.write('%d %f\n' % (i, slub[i]))
        ftxt.close()

    message('Pass 3: divide spectra by RLUB')
    
    if progress:
        progress(0.0)

    for j in range(im2.lines):
        if progress:
            progress(j / float(im2.lines))
        for i in range(im2.samples):
            im3[j, i] = im2[j, i] / slub

    if progress:
        progress(1.0)

    numpy.seterr(**oldsettings)

    del im, im2, im3

def kwikresiduals(fin, fout, albedo=None, rlub=None, N=3.0,
                 sort_wavelengths=False, use_bbl=True,
                 message=message, progress=None):

    im = envi2.Open(fin, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

#    im2 = envi2.New('/tmp/znorm', hdr=im, interleave='bsq', data_type='d')
    if albedo:
        imalbedo = envi2.New(albedo, hdr=im, interleave='bsq', data_type='d',
                             bands=1, wavelength=None, bbl=None, fwhm=None,
                             band_names=['Albedo of %s' % (fin,)])

    bbl = None
    if hasattr(im, 'bbl'):
        bbl = im.bbl

    im3 = envi2.New(fout, hdr=im, interleave='bsq', data_type='d', bbl=bbl)

    im2 = im3

    oldsettings = numpy.seterr(all='ignore')

    message('Pass 1: normalize spectra by albedo')
    
    if progress:
        progress(0.0)

    for j in range(im.lines):
        if progress:
            progress(j / float(im.lines))
        for i in range(im.samples):
            spec = im[j, i]
##            m = spec.mean()
            m = nanmean(spec)

            im2[j, i] = spec / m

            if albedo:
                imalbedo[j, i] = m

    im2.flush()

    if albedo:
        del imalbedo
    
    message('\n')

    message('Pass 2: determine RLUB (ignoring highest 1%)')
    message('Using %f Standard Deviations' % (N,))

    slub = numpy.zeros(im.bands)

    if progress:
        progress(0.0)

    for b in range(im2.bands):
        if progress:
            progress(b / float(im2.bands))
        band = im2[b].flatten()
##        m = band.mean()
        m = nanmean(band)
##        s = band.std()
        s = nanstd(band)
#        mx = band.max()
##        band = band.flatten()
        # Take out any NaN's in the band...
        band = band[numpy.where(numpy.isnan(band)==False)]
        band.sort()
        mx = band[int(len(band)*0.99)]
        
        slub[b] = min((m + N * s), mx)

    message('\n')

    # Plot RLUB, if we can...
    if HAS_PYLAB:
        if hasattr(im, 'wavelength'):
            plot(im.wavelength, slub, linewidth=LINEWIDTH)
            xlabel('wavelength')
        else:
            plot(slub, linewidth=LINEWIDTH)
            xlabel('band')

        ylabel('RLUB')
        title('Robust Least Upper Bound')

    # write RLUB to text file
    if rlub:
        ftxt = open(rlub, 'w')
        if hasattr(im, 'wavelength'):
            ftxt.write('Wavelength RLUB\n')
            for i in range(im.bands):
                ftxt.write('%f %f\n' % (im.wavelength[i], slub[i]))
        else:        
            ftxt.write('Band RLUB\n')
            for i in range(im.bands):
                ftxt.write('%d %f\n' % (i, slub[i]))
        ftxt.close()

    message('Pass 3: divide spectra by RLUB')
    
    if progress:
        progress(0.0)
    for j in range(im2.lines):
        if progress:
            progress(j / float(im2.lines))
        for i in range(im2.samples):
            im3[j, i] = im2[j, i] / slub

    if progress:
        progress(1.0)

    numpy.seterr(**oldsettings)

    del im, im2, im3

if __name__ == '__main__':
##    logresiduals('/data/Data/Tmp/logres/Rodalquilar_01_rad_geo_sub2', '/data/Data/Tmp/logres/Rodalquilar_01_rad_geo_sub2_lr')
##    raise RuntimeError('Run this module using tkLogResiduals.py')

    # command line version
    import optparse
    import os

    parser = optparse.OptionParser(
        usage='logresiduals.py -s -b -f -k -i input -o output -a albedo -r rlub -p -n stddevs',
        description='Normalize image data using Log Residuals or Kwik Residuals')

    parser.add_option('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_option('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_option('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_option('-i', dest='input', help='input file name')
    parser.add_option('-o', dest='output', help='output file name')

    parser.add_option('-k', action='store_true', dest='kwik',
                      help='use kwik residuals instead of log residuals')
    parser.add_option('-a', dest='albedo',
                      help='albedo output file name')
    parser.add_option('-r', dest='rlub',
                      help='rlub output file name (text file)')
    parser.add_option('-p', action='store_true', dest='plot',
                      help='plot RLUB')
    parser.add_option('-n', dest='n', type='float',
                      help='number of standard deviations for maximum (default=3.0)')

    parser.set_defaults(sort_wavelengths=False, use_bbl=False, force=False,
                        kwik=False, n=3.0, plot=False)

    (options, args) = parser.parse_args()

    assert options.input, "Option -i input file name required."
    assert options.output, "Option -o output file name required."
    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    if options.kwik:
        kwikresiduals(options.input, options.output, albedo=options.albedo,
                     rlub=options.rlub, N=options.n,
                     sort_wavelengths=options.sort_wavelengths,
                     use_bbl=options.use_bbl)
    else:
        logresiduals(options.input, options.output, albedo=options.albedo,
                     rlub=options.rlub, N=options.n,
                     sort_wavelengths=options.sort_wavelengths,
                     use_bbl=options.use_bbl)

    if options.plot:
        show()
