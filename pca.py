import tempfile
import pickle
import envi2
import extmath # for fast_svd()
import numpy
from pylab import *

def message(s):
    print(s)

def write_stats(fname, Xm, s, V, w):
    if fname:
        f = open(fname, 'wb')
        pickle.dump(numpy.array(Xm), f)
        pickle.dump(s, f)
        pickle.dump(V, f)
        pickle.dump(w, f)
        f.close()

def read_stats(fname):
    f = open(fname, 'rb')
    Xm = pickle.load(f)
    s = pickle.load(f)
    V = pickle.load(f)
    w = pickle.load(f)
    f.close()
    return Xm, s, V, w

def pca_inverse(fin, fout, stats=None, band_selection=None, message=message):

    im = envi2.Open(fin, use_bbl=False, sort_wavelengths=False)

    Xm, s, V, wavelength = read_stats(stats)

    shape = (im.lines, im.samples, im.bands)

    flatshape = (shape[0] * shape[1], shape[2])

    message('create memmap for data copy...')
    U = numpy.memmap(tempfile.TemporaryFile(), shape=flatshape, dtype=im.data.dtype)

    message('copy image and reshape bands into columns...')
    U[...] = im[...].reshape((shape[0] * shape[1], shape[2]))

    if band_selection: # invert band selection and make it zero
        idx = numpy.ones(shape[2], dtype='bool')
        idx[numpy.array(band_selection)] = False
        U[:, numpy.where(idx)] = 0

    message('open output...')
    out = envi2.New(fout, hdr=im, data_type='f', wavelength=wavelength,
                    fwhm=None, bbl=None, band_names=None)

    message('calculating inverse PCA...')
    out[...] = numpy.dot(U, numpy.dot(numpy.diag(s), V)).reshape(shape) + Xm

def pca(fin, fout, stats=None, band_selection=None, use_bbl=True,
        sort_wavelengths=True, message=message, do_plot=True):

    im = envi2.Open(fin, use_bbl=use_bbl, sort_wavelengths=sort_wavelengths)

    wavelength = getattr(im, 'wavelength', None)

    if band_selection:
        bands = len(band_selection)
        if wavelength is not None:
            wavelength = numpy.array(wavelength)[band_selection]
    else:
        bands = im.bands
        
    shape = (im.lines, im.samples, bands)

    flatshape = (shape[0] * shape[1], shape[2])

    message('create memmap for data copy...')
    X = numpy.memmap(tempfile.TemporaryFile(), shape=flatshape, dtype=im.data.dtype)

    message('copy image and reshape bands into columns...')
    if band_selection:
        X[...] = im[:,:,band_selection].reshape(flatshape)
    else:
        X[...] = im[...].reshape(flatshape)

##    X = X.reshape((shape[0] * shape[1], shape[2]))

    ## this is for true PCA?
    Xm = X.mean(axis=0)
    X[...] = X - Xm

    message('fast SVD...')
    U, s, V = extmath.fast_svd(X, shape[2])  

    del X

##    ## this gives me the original (does this mean that V is actually Vt?)
##    Y = dot(U, dot(diag(s), V))

    out = envi2.New(fout, hdr=im, data_type='f', bands=bands,
                    wavelength=None, fwhm=None, bbl=None, band_names=None,
                    original_bbl=None)

    message('copy U to output, reshape to original dimensions...')
    out[...] = U.reshape(shape)

    del out

    if do_plot:
        plot(s)
        title('Singular values = sqrt(Eigenvalues)')
        xlabel('component')
        ylabel('singular value')

    write_stats(stats, Xm, s, V, wavelength)

def pca_bb(fin, fout, stats=None, band_selection=None, bbox=None, use_bbl=True, sort_wavelengths=True, message=message):
    """Determines statistics from Bounding Box"""
    im = envi2.Open(fin, use_bbl=use_bbl, sort_wavelengths=sort_wavelengths)

    wavelength = getattr(im, 'wavelength', None)

    if bbox:
        x0, x1, y0, y1 = bbox

        # safety checks
        x0 = max(0, x0)
        x1 = min(im.samples, x1)
        y0 = max(0, y0)
        y1 = min(im.lines, y1)
    else:
        x0, x1 = 0, im.samples
        y0, y1 = 0, im.lines
    
    if band_selection:
        bands = len(band_selection)
        if wavelength is not None:
            wavelength = numpy.array(wavelength)[band_selection]
    else:
        bands = im.bands
        
    shape = (y1-y0, x1-x0, bands)

    flatshape = (shape[0] * shape[1], shape[2])

    message('create memmap for subset...')
    X = numpy.memmap(tempfile.TemporaryFile(), shape=flatshape, dtype=im.data.dtype)

    message('copy image and reshape bands into columns...')
    if band_selection:
        X[...] = im[y0:y1, x0:x1, band_selection].reshape(flatshape)
    else:
        X[...] = im[y0:y1, x0:x1, :].reshape(flatshape)

    ## this is for true PCA?
    Xm = X.mean(axis=0)
    X[...] = X - Xm

    message('fast SVD...')
    Usub, s, V = extmath.fast_svd(X, shape[2])  

    del X
    del Usub

    shape = (im.lines, im.samples, bands)

    flatshape = (shape[0] * shape[1], shape[2])

    message('create memmap for full data...')
    X = numpy.memmap(tempfile.TemporaryFile(), shape=flatshape, dtype=im.data.dtype)

    message('copy image and reshape bands into columns...')
    if band_selection:
        X[...] = im[:,:,band_selection].reshape(flatshape)
    else:
        X[...] = im[...].reshape(flatshape)

    out = envi2.New(fout, hdr=im, data_type='f', bands=bands,
                    wavelength=None, fwhm=None, bbl=None, band_names=None,
                    original_bbl=None)

    message('calculate U, reshape to original dimensions, copy to output...')
    out[...] = (numpy.dot(X, numpy.dot(V.T, numpy.diag(1/s)))).reshape(shape)

    del out

    plot(s)
    title('Singular values = sqrt(Eigenvalues)')
    xlabel('component')
    ylabel('singular value')

    write_stats(stats, Xm, s, V, wavelength)

def pca_bb_nansafe(fin, fout, stats=None, band_selection=None, bbox=None, use_bbl=True, sort_wavelengths=True, message=message):
    """Determines statistics from Bounding Box. Ignore NaNs."""
    im = envi2.Open(fin, use_bbl=use_bbl, sort_wavelengths=sort_wavelengths)

    wavelength = getattr(im, 'wavelength', None)

    if bbox:
        x0, x1, y0, y1 = bbox

        # safety checks
        x0 = max(0, x0)
        x1 = min(im.samples, x1)
        y0 = max(0, y0)
        y1 = min(im.lines, y1)
    else:
        x0, x1 = 0, im.samples
        y0, y1 = 0, im.lines
    
    if band_selection:
        bands = len(band_selection)
        if wavelength is not None:
            wavelength = numpy.array(wavelength)[band_selection]
    else:
        bands = im.bands
        
    shape = (y1-y0, x1-x0, bands)

    flatshape = (shape[0] * shape[1], shape[2])

    message('create memmap for subset...')
    X = numpy.memmap(tempfile.TemporaryFile(), shape=flatshape, dtype=im.data.dtype)

    message('copy image and reshape bands into columns...')
    if band_selection:
        X[...] = im[y0:y1, x0:x1, band_selection].reshape(flatshape)
    else:
        X[...] = im[y0:y1, x0:x1, :].reshape(flatshape)

    message('checking for NaNs...')
    idx = numpy.where(numpy.isfinite(X).all(axis=1))[0]
    message('found %d spectra, keeping %d' % (X.shape[0], idx.shape[0]))

    message('create memmap for NaNless subset...')
    Xnn = numpy.memmap(tempfile.TemporaryFile(), shape=(len(idx), shape[2]), dtype=im.data.dtype)

    message('getting rid of NaNs...')
    Xnn[...] = X[idx,:]

    del X
    
    ## this is for true PCA?
    Xm = Xnn.mean(axis=0)
    Xnn[...] = Xnn - Xm

    message('fast SVD...')
    Usub, s, V = extmath.fast_svd(Xnn, shape[2])  

    del Xnn
    del Usub

    shape = (im.lines, im.samples, bands)

    flatshape = (shape[0] * shape[1], shape[2])

    message('create memmap for full data...')
    X = numpy.memmap(tempfile.TemporaryFile(), shape=flatshape, dtype=im.data.dtype)

    message('copy image and reshape bands into columns...')
    if band_selection:
        X[...] = im[:,:,band_selection].reshape(flatshape)
    else:
        X[...] = im[...].reshape(flatshape)

    out = envi2.New(fout, hdr=im, data_type='f', bands=bands,
                    wavelength=None, fwhm=None, bbl=None, band_names=None,
                    original_bbl=None)

    message('calculate U, reshape to original dimensions, copy to output...')
    out[...] = (numpy.dot(X, numpy.dot(V.T, numpy.diag(1/s)))).reshape(shape)

    del out

    plot(s)
    title('Singular values = sqrt(Eigenvalues)')
    xlabel('component')
    ylabel('singular value')

    write_stats(stats, Xm, s, V, wavelength)
    
if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='pca.py',
        description='Principal Components.')

    parser.add_argument('-s', action='store_true', dest='sort_wavelengths',
                      help='sort bands on wavelength')
    parser.add_argument('-b', action='store_true', dest='use_bbl',
                      help='use bad band list from the header')
    parser.add_argument('-f', action='store_true', dest='force',
                      help='force overwrite on existing output file')
    parser.add_argument('-i', dest='input', help='input file name',
                        required=True)
    parser.add_argument('-o', dest='output', help='output file name',
                        required=True)
    parser.add_argument('-p', dest='stats', help='statistics output file name',
                        required=False)

    options = parser.parse_args()

    assert options.force or not os.path.exists(options.output), "Output file exists. Use -f to overwrite."

    pca(options.input, options.output,
        stats=options.stats,
        band_selection=None,
        sort_wavelengths=options.sort_wavelengths,
        use_bbl=options.use_bbl,
        do_plot=False)
