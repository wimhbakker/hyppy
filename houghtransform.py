import envi2
from circle import *
from numpy import *

##MAXSIZE=100

# globals
xs = None
ys = None
zs = None

def AddPixel(x, y, r):
    global xs, ys, zs
    xs.append(x)
    ys.append(y)
    zs.append(r)

def message(s):
    print(s)

def hough_transform(fin, fout, minsize, maxsize, stepsize=1, threshold=128,
                    message=message, progress=None):
    global xs, ys, zs
    xs = []
    ys = []
    zs = []

    # get ENVI image data
    im = envi2.Open(fin)

    if im.bands > 1:
        raise ValueError('Input image must have 1 band only!')

##    print im.lines, im.samples, im.bands

    lines   = im.lines + 2 * maxsize
    samples = im.samples + 2 * maxsize
    bands   = (maxsize - minsize) // stepsize
    x_start = -maxsize
    y_start = -maxsize

    if hasattr(im.header, 'x_start'):
        x_start += im.header.x_start

    if hasattr(im.header, 'y_start'):
        y_start += im.header.y_start

    band_names = ['radius ' + str(s) for s in range(minsize, maxsize, stepsize)]

    # open output Hough Transform image
    hough = envi2.New(fout, 
                      hdr=im.header, lines=lines, samples=samples, bands=bands,
                      x_start=x_start, y_start=y_start,
                      data_type='d',
                      band_names=band_names)

    # construct coordinate list of hough cone
    for radius in range(minsize, maxsize, stepsize):
        MidpointCircle(0, 0, radius, writepix=AddPixel)

    # convert to array
    xs = array(xs)
    ys = array(ys)
    zs = (array(zs) - minsize) // stepsize
 
    count = 0
    y, x, z = where(im.data>threshold)
    if progress:
        progress(0.0)
    for i in range(len(x)):
        if progress:
            progress(i / float(len(x)))
        count += 1
        hough[ys+maxsize+y[i], xs+maxsize+x[i], zs] += 1

    if progress:
        progress(1.0)

    del hough, im

if __name__ == '__main__':
    print("No CLI available!")

##    fin = '/data/Data/AgentschapNL/Areas/area1/koeltoren_envi_grad_ID'
##    fout = '/tmp/hough'
##    hough_transform(fin, fout, 50, 70, 5, 100) 
