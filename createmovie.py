from subprocess import Popen, PIPE
import os
import sys
import tempfile
import envi2
import stretch
from PIL import Image, ImageDraw, ImageFont

if sys.platform.startswith('win'):
    raise NotImplementedError("Windows not supported")
else:
    FFMPEG = 'ffmpeg'

def console(cmd):
    p = Popen(cmd, stdout=PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)

def message(s):
    print(s)

def create_movie(fname, fps=10, sort_wavelengths=False, use_bbl=False,
                 mode='1P', bitrate='1500k', message=message, progress=None):
    
    im = envi2.Open(fname, sort_wavelengths=sort_wavelengths, use_bbl=use_bbl)

    base = os.path.basename(fname)
    tdir = tempfile.TemporaryDirectory()

    stretch_fun = stretch.fundict[mode]

    message('Saving bands...')
    if progress:
        progress(0)
    for b in range(im.bands):
        if progress:
            progress(b / im.bands)
##        band = stretch_fun(im[b])
##        band = stretch.custom_stretch(im[b], 0.37, 0.61)
        band = stretch.percent_percent_stretch(im[b], 0.4, 0.99)[0]
        imout = Image.fromarray(band)
        d = ImageDraw.Draw(imout)
        fnt = ImageFont.truetype('Pillow/Tests/fonts/FreeMono.ttf', 30)
        txt = "%6.1f nm" % (im.wavelength[b],)
        txtsize = d.textsize(txt, font=fnt)
        d.text((im.samples-txtsize[0]-10, im.lines-txtsize[1]-10), txt, font=fnt, fill=255)
        imout.save(os.path.join(tdir.name, '%s%05d.png' % (base, b)))
        
    if progress:
        progress(1)

    message('Creating movie...')
    console((FFMPEG, '-r', str(fps), '-i', os.path.join(tdir.name, '%s%%05d.png' % (base,)), '-b:v', bitrate, '-y', '%s.mp4'%(fname,)))

if __name__ == '__main__':

    create_movie('/data2/data/AVIRISNG/L2/ang20140625t191627_rfl_v1c/ang20140625t191627_corr_v1c_img_sub_fix',
                 mode='MAD', bitrate='1500k')
