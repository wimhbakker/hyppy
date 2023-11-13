from subprocess import Popen, PIPE
import json
import os
import sys

import osgeo

OSGEOPATH = osgeo.__path__

WINPATHLIST = ['C:\\OSGeo4W64\\bin', 'C:\\Program Files\\QGIS 2.18\\bin']
PATH = [ ]

env = os.environ

if 'PATH'in env:
    PATH = env['PATH'].split(';')

#print(PATH)

#sys.exit()

if sys.platform.startswith('win'):
    GDALWARP = ''
    for path in OSGEOPATH + PATH + WINPATHLIST:
        GDALINFO = os.path.join(path, 'gdalinfo.exe')
        if os.path.exists(GDALINFO):
            GDALWARP = os.path.join(path, 'gdalwarp.exe')
            GDAL_TRANSLATE = os.path.join(path, 'gdal_translate.exe')
            break
    if not GDALWARP:
        raise ImportError("GDAL scripts not found")
else:
    GDALINFO = 'gdalinfo'
    GDALWARP = 'gdalwarp'
    GDAL_TRANSLATE = 'gdal_translate'

def console(cmd):
    p = Popen(cmd, stdout=PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)

def message(s):
    print(s)

def convert_aster(fname, message=message, progress=None):
    base = os.path.splitext(fname)[0]
    info = console((GDALINFO, '-json', fname))
    meta = json.loads(info[1].decode('utf-8'))
    subs = meta['metadata']['SUBDATASETS']
    if progress:
        progress(0)
    n = len(subs)//2
    message("Number of subdatasets: %d" % (n,))
##    message(str(subs))
    for i in range(1, 1+n):
        if progress:
            progress(i / n)
        key = "SUBDATASET_%d_DESC" % (i,)
        desc = subs[key]
        message(desc)
        if 'ImageData' in desc or 'Band' in desc or 'Temperature' in desc:
            desc2 = '_'.join(desc.split('] ')[1].split(' (')[0].split(' '))
            out = base + '_' + desc2
            message(out)
            key = "SUBDATASET_%d_NAME" % (i,)
            name = subs[key]
            if 'Swath' in name:
                info = console((GDALWARP,'-of', 'ENVI', '-overwrite', name, out))
            else:
                info = console((GDAL_TRANSLATE,'-of', 'ENVI', name, out))
            message(info[1].decode('utf-8'))

if __name__ == '__main__':
##    convert_aster(r'C:\Users\bakker\surfdrive\Data\Aster\AST_L1T_00305112016104003_20160512094027_20237.hdf')
    convert_aster('/home/bakker/ownCloud/Data/Aster/AST_L1T_00305112016104003_20160512094027_20237.hdf')
