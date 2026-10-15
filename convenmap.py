import xml.dom.minidom
import os
import rasterio
import numpy as np
from scipy import ndimage

##import sys
##sys.path.append(r"C:\Users\bakker\Nextcloud\Python\hyppy-main20261005\hyppy-main")
import envi2
import envi2.constants

DEBUG = False

def message(s):
    print(s)

def get_filelist_from_manifest(f):
    doc = xml.dom.minidom.parse(f)
 
    filelist = list()
    for node in doc.getElementsByTagName('file'):
        number = node.getAttribute('number')
        name = node.getElementsByTagName('name')[0].firstChild.nodeValue
        if DEBUG:
            message(f"file {number}: {name}")
        filelist.append(name)

    return filelist

def read_enmap(fname, message=message, apply_pixelmask=True, apply_cloudmask=True):
    message(f"Reading METADATA {os.path.basename(fname)}")
    the_dir = os.path.dirname(fname)

    filelist = get_filelist_from_manifest(fname)
    if DEBUG:
        message(filelist)

    pixelmask = None
    cloudmask = None

    for f in filelist:
        base, ext = os.path.splitext(f)
        path_f = os.path.join(the_dir, f)
        if 'SPECTRAL_IMAGE.B' in f:
            imagefilename = f
        if ext.lower()=='.tif':
            if DEBUG:
                message("\n=====================================")
                message(base)

            with rasterio.open(path_f) as src:
                band1 = src.read()          # 2D NumPy array; bands are numbered from 1 !!
                if DEBUG:
                    message(f"Shape: {band1.shape}")
                    message(f"Type: {band1.dtype}")
        #            message("CRS:", src.crs.to_wkt())
        #            message("Bounds:", src.bounds)
                    message(f"No-data value: {src.nodata}")

                ql_quality = base.split('_')[-1]
                if ql_quality in ['PIXELMASK']:
                    pixelmask = band1.transpose([1, 2, 0])
                    message(f"Reading PIXELMASK {pixelmask.shape}")
                elif ql_quality in ['CIRRUS', 'CLOUD', 'CLOUDSHADOW', 'HAZE', 'SNOW']:
                    if cloudmask is None:
                        cloudmask = band1[0]
                    else:
                        cloudmask = cloudmask | band1[0]
                    message(f"Reading {ql_quality} {cloudmask.shape}")

    if cloudmask is not None:
        message("Dilating cloudmask")
        struct_plus = np.array([[0, 1, 0],
                                [1, 1, 1],
                                [0, 1, 0]])
        struct_full = np.array([[1, 1, 1],
                                [1, 1, 1],
                                [1, 1, 1]])
        cloudmask = ndimage.grey_dilation(cloudmask, footprint=struct_full)

        description = ['EnMAP cloud mask']
        file_type = envi2.constants.ENVI_Standard
        interleave = envi2.constants.ENVI_BIP
        data_type = cloudmask.dtype
        byte_order = 0
        lines, samples = cloudmask.shape
        bands = 1

        message('Creating new CLOUDMASK image')

        envi_im = envi2.New(os.path.join(the_dir, base+'_CLOUDMASK'), value=0,
                            description=description,
                            file_type=file_type,
                              interleave=interleave, data_type=data_type,
                              byte_order=byte_order, samples=samples,
                              lines=lines, bands=bands)

        message('Writing CLOUDMASK image')

        envi_im[:, :, 0] = cloudmask

        del envi_im

    # open EnMAP image
    message(f"Opening {os.path.basename(imagefilename)}")
    enmap_im = envi2.Open(os.path.join(the_dir, imagefilename))
    if DEBUG:
        message(f"Data ignore value: {enmap_im.header.data_ignore_value}")

    # set up output image
    message("Creating new MASKED image")
    output_im = envi2.New(os.path.join(the_dir, base+'_MASKED'), hdr=enmap_im)

    message("Reading SPECTRAL_IMAGE")
    output_im[...] = enmap_im[...].clip(min=0)

    if apply_pixelmask and pixelmask is not None:
        message("Applying pixel mask") 
        output_im[...] = output_im[...] * (1 - pixelmask[...])

    if apply_cloudmask and cloudmask is not None:
        message("Applying cloud mask") 
        output_im[...] = output_im[...] * (1 - cloudmask[:,:,np.newaxis].clip(min=0, max=1))

    del output_im

#read_enmap(r"C:\Users\bakker\Tmp\hsi\hsi\enmap\0raw\ENMAP01-____L2A-DT0000062245_20240221T084216Z_001_V010506_20260710T115912Z\ENMAP01-____L2A-DT0000062245_20240221T084216Z_001_V010506_20260710T115912Z-METADATA.XML",
#           apply_cloudmask=True, apply_pixelmask=True)

if __name__ == '__main__':
    # command line version
    import argparse
    import os

    parser = argparse.ArgumentParser(prog='convenmap.py',
        description='Convert EnMAP image to ENVI format.')

    parser.add_argument('-i', dest='input', help='input METADATA file name', required=True)

    parser.add_argument('-p', action='store_true', dest='apply_pixelmask',
                        help='apply pixelmask (default false)',
                        default=False, required=False)

    parser.add_argument('-c', action='store_true', dest='apply_cloudmask',
                        help='apply cloudmask (default false)',
                        default=False, required=False)

    options = parser.parse_args()

    read_enmap(options.input, apply_pixelmask=options.apply_pixelmask ,
               apply_cloudmask=options.apply_cloudmask)

