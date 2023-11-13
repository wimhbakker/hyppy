from struct import unpack
#import glob
import time
import os

MAGIC = [b'asd', b'as7']
#MAGIC = [b'asd']

data_format = {0:'float', 1:'integer', 2:'double', 3:'unknown'}

def make_time_tuple(tm):
    """Convert ASD time tuple to Python time tuple"""
    sec, mins, hour, day, month, year, wday, yday, isdst = tm
    year = year + 1900
    month = month + 1
    wday = (wday + 6) % 7
    yday = yday + 1
    return (year, month, day, hour, mins, sec, wday, yday, isdst)

def major_minor(version):
    """Get major and minor version from a byte"""
    return (version >> 4, version & 0b1111)

def asd_read_spectrum(fin):
    """Read ASD format"""
    print("ASD read:", fin)
    f = open(fin, 'rb')

    header = f.read(484)
    data = f.read()
    print("data length", len(data))

    f.close()

    if header[0:3].lower() not in MAGIC:
        raise ValueError('not an ASD file')

    description = os.path.basename(fin)

    # Get data info from header
    # See: "Indico Version 8 File Format" document
    # http://support.asdi.com/Document/Documents.aspx
    comments, = unpack('157s', header[3:160])
##    if ord(comments[0]):
##        print "comments:", comments
    
    tm = unpack('<9h', header[160:178])
    print("file creation time: ", time.asctime(make_time_tuple(tm)))

    pversion, fversion = unpack('2B', header[178:180])
##    print "program version: %d.%d" % major_minor(pversion)
##    print "file version: %d.%d" % major_minor(fversion)

    specformat, = unpack('B', header[199:200])
    print("format of spectrum:", data_format[specformat])
    
    nchannels, = unpack('<h', header[204:206])
    print("number of channels", nchannels)
    
    start, step = unpack('<2f', header[191:199])
    print("wavelength start and step", start, step)

    wav = [start + i * step for i in range(nchannels)]
    if specformat==0:
        num = unpack('<%df' % nchannels, data[:4*nchannels])
    elif specformat==1:
        num = unpack('<%di' % nchannels, data[:4*nchannels])
    elif specformat==2:
        num = unpack('<%dd' % nchannels, data[:8*nchannels])
    else:
        raise ValueError('unknown data format of spectrum')

    return wav, num, description

if __name__ == "__main__":
    x = asd_read_spectrum('/data2/data/Specim/20160405-ASD-drillcore1/drillcore1_00000.asd.sco')
    y = asd_read_spectrum('/home/bakker/ownCloud/TerraSpec/Halo/Exports/asd/30092_HaloDefaultProject_HaloStandard-Default1-S_30092_0005.ASD')
