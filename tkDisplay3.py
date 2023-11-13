#!/usr/bin/python3
#
#   tkDisplay.py
#   Created:  WHB 20080903
#   Modified: WHB 20081202
#   Modified: WHB 20090302
#   Modified: WHB 20090313
#   Modified: WHB 20090402, Slider motion
#   Modified: WHB 20090515, outside image area
#   Modified: WHB 20100326, added bbl in status
#   Modified: WHB 20100330, band_names now taken from image
#   Modified: WHB 20111219, added flipping
#   Modified: WHB 20120221, added zooming
#   Modified: WHB 20140326, changed histogram to probability on y-axis
#   Modified: WHB 20141126, added 3 bands to values window in case of color
#   Modified: WHB 20141128, added band statistics
#   Modified: WHB 20160831, added saturation enhancement
#   Modified: WHB 20180112, looks at default stretch for wavelength maps
#   Modified: WHB 20210315, added support for ENVI speclibs as images
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

import os
import sys
import math
import random
import time
import numpy

from tkinter import *
import tkinter.filedialog
import tkinter.messagebox

# Try to import Pillow or PIL
try:
    try:
        from PIL import Image
        from PIL import ImageTk
    except ImportError as errtext:
        import Image
        import ImageTk
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message="Module Pillow or PIL not found")
    raise

try:
    import colorsys
    
    import tkValueViewer
    import tkStretchValueWindow

    import envi2
    from envi2.constants import *
##    from numpy import nanmin, nanmax
    import numpy
##    from scipy.stats import histogram2

    import stretch
    import conf

##    from matplotlib import rcParams
##    rcParams['legend.fontsize'] = 10
    import matplotlib as mpl
    mpl.rcParams['legend.fontsize'] = 10

    from pylab import plot, xlabel, ylabel, legend, array, ion, close, figure, clf, arange, where, isnan, median, fabs

except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

LINEWIDTH = 1.0
NUMBINS = conf.get_option('histogram-bins', 255, type_=int)

WINDOWS = 'win' in sys.platform.lower()

ion()

def rainbow():
    result = []
    for i in range(256):
        h = 0.8 * (1 - i / 255.0)
        r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
        r = math.pow(r, 0.6)
        g = math.pow(g, 0.6)
        b = math.pow(b, 0.6)
        result.extend([int(255*r), int(255*g), int(255*b)])
    return result

def rainbow2():
    result = []
    result.extend([0, 0, 0])
    for i in range(1, 255):
        h = 0.8 * (1 - i / 255.0)
        r, g, b = colorsys.hsv_to_rgb(h, 1, math.sqrt(math.sqrt(i/255.0)))
        r = math.pow(r, 0.6)
        g = math.pow(g, 0.6)
        b = math.pow(b, 0.6)
        result.extend([int(255*r), int(255*g), int(255*b)])
    result.extend([255, 255, 255])
    return result

def spiral():
    result = []
    for i in range(256):
        h = (1.8 * (1 - i / 255.0)) % 1.0
##        r, g, b = colorsys.hsv_to_rgb(h, 1, math.sqrt(math.sqrt(i/255.0)))
        v = 0.3 + 0.4 * ((i%16)/15.0)
        s = 1 - 0.5 * math.sqrt(i / 255.0)
        r, g, b = colorsys.hls_to_rgb(h, v, s)
        result.extend([int(255*r), int(255*g), int(255*b)])
    return result

def spiral2():
    result = []
    for i in range(256):
        h = (0.9 * (1 - i / 255.0) - 0.2) % 1.0
        v = 0.3 + 0.4 * ((i%16)/15.0)
        s = 1 - 0.5 * math.sqrt(i / 255.0)
        r, g, b = colorsys.hls_to_rgb(h, v, s)
        result.extend([int(255*r), int(255*g), int(255*b)])
    return result

def spiral3():
    result = []
    for i in range(256):
        h = (0.9 * (1 - i / 255.0) - 0.22) % 1.0
        r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
        r = math.pow(r, 0.6)
        g = math.pow(g, 0.6)
        b = math.pow(b, 0.6)
        result.extend([int(255*r), int(255*g), int(255*b)])
    return result

def palette_random():
    result = []
    for i in range(3*256):
        result.append(int(random.random()*255))
    return result

def blue_red():
    result = []
    for i in range(256):
        h = 0.6666 + 0.3333 * (i / 255.0)
        r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
        result.extend([int(255*r), int(255*g), int(255*b)])
    return result

def green_red():
    result = []
    for i in range(256):
        h = 0.3333 - 0.3333 * (i / 255.0)
        r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
        result.extend([int(255*r), int(255*g), int(255*b)])
    return result

palette_rainbow = rainbow()
palette_rainbow2 = rainbow2()
palette_spiral = spiral()
palette_spiral2 = spiral2()
palette_spiral3 = spiral3()
palette_blue_red = blue_red()
palette_green_red = green_red()

class Application(Frame):

    def __init__(self, master=None):
        # call superclass constructor
        Frame.__init__(self, master)

        # create the frame, resizable
        self.grid(sticky=N+E+S+W)
        top=self.winfo_toplevel()

        # allow toplevel to stretch
        top.columnconfigure(0, weight=1)
        top.rowconfigure(0, weight=1)

        # create contents
        self.makeWindow(master)

    def pick_input(self):
##        name = self.nameIn.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'

        idir = conf.get_option('input-dir')
        
        # dialog pickfile
        name = tkinter.filedialog.askopenfilename(title='Open Image',
                                            initialdir=idir,
                                            initialfile='')

        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            # set file name in text box
            self.nameIn.set(name)
            self.open_image()
            self.set_default_bands()
            self.load_data()
            self.check_file()

    def pick_shadow(self):
        idir = conf.get_option('input-dir')
        
        # dialog pickfile
        name = tkinter.filedialog.askopenfilename(title='Open Shadow Image for Z-profiles',
                                            initialdir=idir,
                                            initialfile='')

        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            # set file name in text box
            self.nameShadow.set(name)
            # open image
            self.shadow = envi2.Open(self.nameShadow.get(), sort_wavelengths=self.sortWav.get(),
                                       use_bbl=self.useBBL.get())
            self.status.set('Shadow: %s' % (os.path.basename(name),))
        else:
            if hasattr(self, 'shadow'):
                del self.shadow
            self.status.set('No Shadow')

    def save_image(self):
        if hasattr(self, 'im'):
            odir = conf.get_option('output-dir')
            
            # dialog pickfile
            name = tkinter.filedialog.asksaveasfilename(title='Save Image',
                                                initialdir=odir,
                                                initialfile='')

            if name:
                conf.set_option('output-dir', os.path.dirname(name))
                try:
                    self.im.save(name)
                except KeyError:
                    self.im.save(name+'.png')
                self.status.set('Image saved')
            
    def open_image(self, event=None):
##        self.winfo_toplevel().title("Display: %s" % (self.nameIn.get(),))
        self.winfo_toplevel().title("%s" % (os.path.basename(self.nameIn.get()),))

        # open image
        self.envi_im = envi2.Open(self.nameIn.get(), sort_wavelengths=self.sortWav.get(),
                                       use_bbl=self.useBBL.get())
        # set max band in slider
        bands = self.envi_im.bands
        samples = self.envi_im.samples
        lines = self.envi_im.lines
        self.scale.config(to=bands-1)

        self.Rscale.config(to=bands-1)
        self.Gscale.config(to=bands-1)
        self.Bscale.config(to=bands-1)

        # check default stretch in header
        if hasattr(self.envi_im.header, 'default_stretch'):
            s = self.envi_im.header.default_stretch
            ssplit = s.split()
            if len(ssplit)==3 and ssplit[2]=='linear' and float(ssplit[0])==0 and float(ssplit[1])==255:
                self.stretch.set('NO')

##        self.canvas.configure(width=samples, height=lines, scrollregion=(0, 0,samples, lines))

    def set_default_bands(self):
        if self.envi_im:
            default_bands = getattr(self.envi_im.header, 'default_bands', None)
            if default_bands:
                r, g, b = default_bands
                self.Rscale.set(r-1)
                self.Gscale.set(g-1)
                self.Bscale.set(b-1)
                self.colorDisplay.set(1)
                self.toggle_colordisplay()

    def get_viewport(self):
        samples = self.envi_im.samples
        lines = self.envi_im.lines
        M = self.canvas.winfo_width()
        N = self.canvas.winfo_height()
        z = self.zoom

        if self.viewFlipLeftRight.get():
            ax = 1 - self.scrollx.get()[1]
        else:
            ax = self.scrollx.get()[0]

        if self.viewFlipTopBottom.get():
            ay = 1 - self.scrolly.get()[1]
        else:            
            ay = self.scrolly.get()[0]

        self.x0 = int(ax * samples)
        self.y0 = int(ay * lines)

        if self.x0 > int(samples - M / z):
            self.x0 = max(0, int(samples - M / z))
        if self.y0 > int(lines - N / z):
            self.y0 = max(0, int(lines - N / z))

        self.x1 = min(samples, int(self.x0 + M / z) + 1)
        self.y1 = min(lines, int(self.y0 + N / z) + 1)

        a, b = float(self.x0)/samples, float(self.x1)/samples
        if self.viewFlipLeftRight.get():
            self.scrollx.set(1-b, 1-a)
        else:
            self.scrollx.set(a, b)

        a, b = float(self.y0)/lines, float(self.y1)/lines
        if self.viewFlipTopBottom.get():
            self.scrolly.set(1-b, 1-a)
        else:
            self.scrolly.set(a, b)

    def band2image(self, band):
        # convert from envi to Image to Tk
##        b = self.envi_im.get_band(band)
        b = self.envi_im[self.y0:self.y1, self.x0:self.x1, band]

        # Stretch
        mode = self.stretch.get()
        if mode == 'NO':
            c = stretch.no_stretch(b)
        elif mode == 'MM':
            c = stretch.minmax_stretch(b)
        elif mode == '1P':
            c = stretch.percent_stretch(b)
        elif mode == 'SD':
            c = stretch.stddev_stretch(b)
        elif mode == 'MAD':
            c = stretch.mad_stretch(b)
        elif mode == 'HEQ':
            c = stretch.hist_eq(b)
        elif mode == 'Custom':
            min_ = self.stretchvaluewindow.graymin.get()
            max_ = self.stretchvaluewindow.graymax.get()
            c = stretch.custom_stretch(b, min_, max_)
        else:
            raise ValueError

        if self.inverted.get():
            c = 255 - c

        im = Image.fromarray(c)

        mode = self.pseudoColor.get()
        
        if mode=='rainbow':
            im.putpalette(palette_rainbow)
        elif mode=='rainbow2':
            im.putpalette(palette_rainbow2)
        elif mode=='spiral':
            im.putpalette(palette_spiral)
        elif mode=='spiral2':
            im.putpalette(palette_spiral2)
        elif mode=='spiral3':
            im.putpalette(palette_spiral3)
        elif mode=='bluered':
            im.putpalette(palette_blue_red)
        elif mode=='greenred':
            im.putpalette(palette_green_red)
        elif mode=='random':
            im.putpalette(palette_random())
        return im
        
    def class2image(self):
        # the .copy() is a workaround for the PIL tobytes/tostring bug in v1.1.7
        im = Image.fromarray(self.envi_im[self.y0:self.y1, self.x0:self.x1, 0].copy())

        palette = self.envi_im.header.class_lookup
        palette = palette + (3*256-len(palette)) * [0]
        im.putpalette(palette)

        return im

    def rgb2image(self, rband, gband, bband):
                # convert from envi to Image to Tk
        r = self.envi_im[self.y0:self.y1, self.x0:self.x1, rband]
        g = self.envi_im[self.y0:self.y1, self.x0:self.x1, gband]
        b = self.envi_im[self.y0:self.y1, self.x0:self.x1, bband]

        # Stretch
        mode = self.stretch.get()
        if mode == 'NO':
            r = stretch.no_stretch(r)
            g = stretch.no_stretch(g)
            b = stretch.no_stretch(b)
        elif mode == 'MM':
            r = stretch.minmax_stretch(r)
            g = stretch.minmax_stretch(g)
            b = stretch.minmax_stretch(b)
        elif mode == '1P':
            r = stretch.percent_stretch(r)
            g = stretch.percent_stretch(g)
            b = stretch.percent_stretch(b)
        elif mode == 'SD':
            r = stretch.stddev_stretch(r)
            g = stretch.stddev_stretch(g)
            b = stretch.stddev_stretch(b)
        elif mode == 'MAD':
            r = stretch.mad_stretch(r)
            g = stretch.mad_stretch(g)
            b = stretch.mad_stretch(b)
        elif mode == 'HEQ':
            r = stretch.hist_eq(r)
            g = stretch.hist_eq(g)
            b = stretch.hist_eq(b)
        elif mode == 'Custom':
            rmin_ = self.stretchvaluewindow.redmin.get()
            rmax_ = self.stretchvaluewindow.redmax.get()
            gmin_ = self.stretchvaluewindow.greenmin.get()
            gmax_ = self.stretchvaluewindow.greenmax.get()
            bmin_ = self.stretchvaluewindow.bluemin.get()
            bmax_ = self.stretchvaluewindow.bluemax.get()
            r = stretch.custom_stretch(r, rmin_, rmax_)
            g = stretch.custom_stretch(g, gmin_, gmax_)
            b = stretch.custom_stretch(b, bmin_, bmax_)
        else:
            raise ValueError

        if self.inverted.get():
            r = 255 - r
            g = 255 - g
            b = 255 - b

        if self.satenh.get():
            rgb = numpy.dstack([r, g, b]).astype('float64') / 255.0
            hsv = mpl.colors.rgb_to_hsv(rgb)
            hsv[:, :, 1] = hsv[:, :, 1]**.25
            rgb = mpl.colors.hsv_to_rgb(hsv) * 255
            r[...] = rgb[:, :, 0]
            g[...] = rgb[:, :, 1]
            b[...] = rgb[:, :, 2]

        # Convert to PIL image
        r = Image.fromarray(r)
        g = Image.fromarray(g)
        b = Image.fromarray(b)

        # Merge bands to one PIL image
        return Image.merge('RGB', (r,g,b))

    # Timer for checking if input file changed
    def check_file(self, oldmtime=None):
        mtime = os.stat(self.nameIn.get()).st_mtime
        if oldmtime:
            if mtime > oldmtime:
                self.load_data()
        
        self.timer_id = self.master.after(1000, self.check_file, mtime)

    # Timer for checking if input file changed
    def step_slider(self):
        if hasattr(self, 'envi_im'):
            self.scale.set((self.scale.get()+1)%self.envi_im.bands)
            self.load_data()
            self.timer_id = self.master.after(100, self.step_slider)

    def load_data(self):
        if not hasattr(self, 'envi_im'):
            self.status.set('Select image')
            return

        self.get_viewport()

        if getattr(self.envi_im.header, 'file_type', ' ')==ENVI_Classification and \
           hasattr(self.envi_im.header, 'class_lookup'):
            self.open_image() # reload colors from header as well!!!...
            self.im = self.class2image()
        else:
            if self.colorDisplay.get():
                rband = self.redBand.get()
                gband = self.greenBand.get()
                bband = self.blueBand.get()
                self.im = self.rgb2image(rband, gband, bband)
            else:
                band = self.bandIn.get()
                self.im = self.band2image(band)

##        imz = self.im.resize([s*self.zoom for s in self.im.size])
##        self.canvas.configure(width=imz.size[0], height=imz.size[1], scrollregion=(0, 0, self.im.size[0], self.im.size[1]))

        self.im = self.im.transform((self.canvas.winfo_width(), self.canvas.winfo_height()), Image.AFFINE, (1/self.zoom, 0, 0, 0, 1/self.zoom, 0), Image.NEAREST)
        
        if self.viewFlipLeftRight.get():
            self.im = self.im.transpose(Image.FLIP_LEFT_RIGHT)

        if self.viewFlipTopBottom.get():
            self.im = self.im.transpose(Image.FLIP_TOP_BOTTOM)

        # convert to something Tk can handle
##        self.imtk = ImageTk.PhotoImage(self.im.resize((int((self.x1-self.x0)*self.zoom), int((self.y1-self.y0)*self.zoom))))
        self.imtk = ImageTk.PhotoImage(self.im)
        
        # delete any old canvas images
        if getattr(self, "canvas_image", None):
            self.canvas.delete(self.canvas_image)
        # create canvas image
        
        if self.viewFlipLeftRight.get() and self.viewFlipTopBottom.get():
            self.canvas_image = self.canvas.create_image(self.canvas.winfo_width(), self.canvas.winfo_height(), image=self.imtk, anchor=SE)
        elif self.viewFlipLeftRight.get():
            self.canvas_image = self.canvas.create_image(self.canvas.winfo_width(), 0, image=self.imtk, anchor=NE)
        elif self.viewFlipTopBottom.get():
            self.canvas_image = self.canvas.create_image(0, self.canvas.winfo_height(), image=self.imtk, anchor=SW)
        else:
            self.canvas_image = self.canvas.create_image(0, 0, image=self.imtk, anchor=NW)

        # set scollable canvas region to the size of the image
#        self.canvas.configure(scrollregion=(0, 0) + self.im.size)

        self.info2statusbar()

    def info2statusbar(self):
        if self.colorDisplay.get():
            rband = self.redBand.get()
            gband = self.greenBand.get()
            bband = self.blueBand.get()
            if hasattr(self.envi_im, 'wavelength'):
                rwav = self.envi_im.wavelength[rband]
                gwav = self.envi_im.wavelength[gband]
                bwav = self.envi_im.wavelength[bband]
                self.status.set("wavelengths=(%g,%g,%g)" % (rwav,gwav,bwav))
            elif hasattr(self.envi_im, 'band_names'):
                rname = self.envi_im.band_names[rband]
                gname = self.envi_im.band_names[gband]
                bname = self.envi_im.band_names[bband]
                self.status.set("names=(%s,%s,%s)" % (rname,gname,bname))
            else:
                self.status.set("bands=(%d,%d,%d)" % (rband,gband,bband))
        else:
            band = self.bandIn.get()

            bad = ''
            if hasattr(self.envi_im, 'bbl'):
                if self.envi_im.bbl[band] == 0:
                    bad = ' (bad)'
                    
            if hasattr(self.envi_im, 'wavelength'):
                wav = self.envi_im.wavelength[band]
                xlbl = 'wavelength'
                if hasattr(self.envi_im.header, 'z_plot_titles'):
                    xlbl, ylbl = self.envi_im.header.z_plot_titles
                self.status.set("%s=%f%s" % (xlbl, wav, bad))
            elif hasattr(self.envi_im, 'band_names'):
                name = self.envi_im.band_names[band]
                self.status.set("%s%s" % (name, bad))
            else:
                self.status.set("band=%d%s" % (band, bad))

    def get_canvas_coordinates(self, event):
        return int(self.canvas.canvasx(event.x)), int(self.canvas.canvasy(event.y))

    def canvas2image_coordinates(self, x, y):
        if self.viewFlipLeftRight.get():
            x = self.canvas.winfo_width() - x
        if self.viewFlipTopBottom.get():
            y = self.canvas.winfo_height() - y
##        return x, y
        return int(self.x0 + x / self.zoom), int(self.y0 + y / self.zoom)
    
    def button_handler(self, event):
        if hasattr(self, 'envi_im'):
            x, y = self.get_canvas_coordinates(event)
            x, y = self.canvas2image_coordinates(x, y)
            if 0<=x<self.envi_im.samples and 0<=y<self.envi_im.lines:
                profile = self.profile.get()
                profilemode = self.profilemode.get()
                if profilemode=='single':
                    if profile == 'pz':
                        self.z_profile(x, y)
                    elif profile == 'px':
                        self.x_profile(x, y)
                    elif profile == 'py':
                        self.y_profile(x, y)
                elif profilemode=='mean':
                    if profile == 'pz':
                        self.z_profile_mean(x, y)
                    elif profile == 'px':
                        self.x_profile_mean(x, y)
                    elif profile == 'py':
                        self.y_profile_mean(x, y)

    def x_profile(self, x, y):
        xlbl, ylbl = 'sample', 'value'
        w = list(range(self.envi_im.samples))
        if hasattr(self.envi_im.header, 'z_plot_titles'):
            ylbl = self.envi_im.header.z_plot_titles[1]

        if self.colorDisplay.get():
            clf()
            band = self.redBand.get()
            s = self.envi_im[y, :, band]
            self.show_values(w, s, label='line %d, band %d' % (y, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='r', name=self.nameIn.get())
            band = self.greenBand.get()
            s = self.envi_im[y, :, band]
            self.show_values(w, s, label='line %d, band %d' % (y, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='g', name=self.nameIn.get(), clear=False)
            band = self.blueBand.get()
            s = self.envi_im[y, :, band]
            self.show_values(w, s, label='line %d, band %d' % (y, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='b', name=self.nameIn.get(), clear=False)
        else:
            band = self.bandIn.get()
            s = self.envi_im[y, :, band]
            self.show_values(w, s, label='line %d, band %d' % (y, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, name=self.nameIn.get())

    def x_profile_mean(self, x, y):
        xlbl, ylbl = 'sample', 'value'
        if hasattr(self.envi_im.header, 'z_plot_titles'):
            ylbl = self.envi_im.header.z_plot_titles[1]

        x0, x1, y0, y1 = self.x0, self.x1, self.y0, self.y1
        w = list(range(x0, x1))

        if self.colorDisplay.get():
            clf()
            band = self.redBand.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, band], axis=0)
            self.show_values(w, s, label='mean x-profile band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='r', name=self.nameIn.get())
            band = self.greenBand.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, band], axis=0)
            self.show_values(w, s, label='mean x-profile band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='g', name=self.nameIn.get(), clear=False)
            band = self.blueBand.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, band], axis=0)
            self.show_values(w, s, label='mean x-profile band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='b', name=self.nameIn.get(), clear=False)
        else:
            band = self.bandIn.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, band], axis=0)
            self.show_values(w, s, label='mean x-profile band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, name=self.nameIn.get())

    def y_profile(self, x, y):
        xlbl, ylbl = 'line', 'value'
        w = list(range(self.envi_im.lines))
        if hasattr(self.envi_im.header, 'z_plot_titles'):
            ylbl = self.envi_im.header.z_plot_titles[1]

        if self.colorDisplay.get():
            clf()
            b = self.redBand.get()
            s = self.envi_im[:, x, b]
            self.show_values(w, s, label='sample %d, band %d' % (x, b), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='r', name=self.nameIn.get())
            b = self.greenBand.get()
            s = self.envi_im[:, x, b]
            self.show_values(w, s, label='sample %d, band %d' % (x, b), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='g', name=self.nameIn.get(), clear=False)
            b = self.blueBand.get()
            s = self.envi_im[:, x, b]
            self.show_values(w, s, label='sample %d, band %d' % (x, b), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='b', name=self.nameIn.get(), clear=False)
        else:
            b = self.bandIn.get()
            s = self.envi_im[:, x, b]
            self.show_values(w, s, label='sample %d, band %d' % (x, b), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, name=self.nameIn.get())

    def y_profile_mean(self, x, y):
        xlbl, ylbl = 'line', 'value'
        if hasattr(self.envi_im.header, 'z_plot_titles'):
            ylbl = self.envi_im.header.z_plot_titles[1]

        x0, x1, y0, y1 = self.x0, self.x1, self.y0, self.y1
        w = list(range(y0, y1))

        if self.colorDisplay.get():
            clf()
            b = self.redBand.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, b], axis=1)
            self.show_values(w, s, label='mean y-profile band %d' % (b,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='r', name=self.nameIn.get())
            b = self.greenBand.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, b], axis=1)
            self.show_values(w, s, label='mean y-profile band %d' % (b,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='g', name=self.nameIn.get(), clear=False)
            b = self.blueBand.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, b], axis=1)
            self.show_values(w, s, label='mean y-profile band %d' % (b,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='b', name=self.nameIn.get(), clear=False)
        else:
            b = self.bandIn.get()
            s = numpy.nanmean(self.envi_im[y0:y1, x0:x1, b], axis=1)
            self.show_values(w, s, label='mean y-profile band %d' % (b,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, name=self.nameIn.get())

    def z_profile(self, x, y):
        if hasattr(self, 'shadow'):
            im = self.shadow
            name = self.nameShadow.get()
        else:
            im = self.envi_im
            name = self.nameIn.get()
        xlbl, ylbl = 'band', ''
        s = im.get_spectrum(y, x)
        if hasattr(im, 'wavelength'):
            w = im.wavelength
            xlbl = 'wavelength'
            if hasattr(im.header, 'z_plot_titles'):
                xlbl, ylbl = im.header.z_plot_titles
            if hasattr(im.header, 'wavelength_units'):
                xlbl = '%s (%s)' % (xlbl, im.header.wavelength_units)
        else:
            w = list(range(im.bands))
        band_names = getattr(im, 'band_names', None)
        if getattr(self.envi_im.header, 'file_type', ' ')==ENVI_Speclib and hasattr(self.envi_im.header, 'spectra_names'):
            label = '%s' % (self.envi_im.header.spectra_names[y],)
        else:
            label = 'spectrum %d, %d' % (x, y)
        self.show_values(w, s, label=label, linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, band_names=band_names, name=name)

    def z_profile_mean(self, x, y):
        if hasattr(self, 'shadow'):
            im = self.shadow
            name = self.nameShadow.get()
        else:
            im = self.envi_im
            name = self.nameIn.get()
        xlbl, ylbl = 'band', ''

        s = numpy.nanmean(im[self.y0:self.y1, self.x0:self.x1], axis=(0,1))

        if hasattr(im, 'wavelength'):
            w = im.wavelength
            xlbl = 'wavelength'
            if hasattr(im.header, 'z_plot_titles'):
                xlbl, ylbl = im.header.z_plot_titles
            if hasattr(im.header, 'wavelength_units'):
                xlbl = '%s (%s)' % (xlbl, im.header.wavelength_units)
        else:
            w = list(range(im.bands))
        band_names = getattr(im, 'band_names', None)

        self.show_values(w, s, label='mean spectrum %d-%d, %d-%d' % (self.x0, self.x1, self.y0, self.y1), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, band_names=band_names, name=name)

    # on the ButtonRelease event of the Scale
    def scale_handler(self, event):
        self.scalebox.delete(0, END)
        self.scalebox.insert(0, self.scale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    # on every motion of the Scale knob
    def scale_command(self, value):
        self.scalebox.delete(0, END)
        self.scalebox.insert(0, self.scale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    # on every motion of the Scale knob
    def Rscale_command(self, value):
        self.Rscalebox.delete(0, END)
        self.Rscalebox.insert(0, self.Rscale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    # on the ButtonRelease event of the Scale
    def Rscale_handler(self, event):
        self.Rscalebox.delete(0, END)
        self.Rscalebox.insert(0, self.Rscale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    # on every motion of the Scale knob
    def Gscale_command(self, value):
        self.Gscalebox.delete(0, END)
        self.Gscalebox.insert(0, self.Gscale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    # on the ButtonRelease event of the Scale
    def Gscale_handler(self, event):
        self.Gscalebox.delete(0, END)
        self.Gscalebox.insert(0, self.Gscale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    # on the ButtonRelease event of the Scale
    def Bscale_handler(self, event):
        self.Bscalebox.delete(0, END)
        self.Bscalebox.insert(0, self.Bscale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    # on every motion of the Scale knob
    def Bscale_command(self, value):
        self.Bscalebox.delete(0, END)
        self.Bscalebox.insert(0, self.Bscale.get())
        if hasattr(self, 'envi_im'):
            self.load_data()

    def motion_handler(self, event):
        if hasattr(self, 'envi_im'):
            x, y = self.get_canvas_coordinates(event)
            x, y = self.canvas2image_coordinates(x, y)

            if 0<=x<self.envi_im.samples and 0<=y<self.envi_im.lines:
                z = self.envi_im.get_value(y, x, self.bandIn.get())
                if getattr(self.envi_im.header, 'file_type', ' ')==ENVI_Speclib and \
                   hasattr(self.envi_im.header, 'spectra_names'):
                    if self.colorDisplay.get():
                        r = self.envi_im.get_value(y, x, self.redBand.get())
                        g = self.envi_im.get_value(y, x, self.greenBand.get())
                        b = self.envi_im.get_value(y, x, self.blueBand.get())
                        self.status.set("%s=(%g,%g,%g)" % (self.envi_im.header.spectra_names[y], r, g, b))
                    else:
                        self.status.set("%s=%g" % (self.envi_im.header.spectra_names[y], z))
                elif getattr(self.envi_im.header, 'file_type', ' ')==ENVI_Classification and \
                   hasattr(self.envi_im.header, 'class_names'):
                    if hasattr(self.envi_im.header, 'spectra_names'):
                        self.status.set("%s=%s" % (self.envi_im.header.spectra_names[y], self.envi_im.header.class_names[z]))
                    else:
                        self.status.set("(%d,%d)=%s" % (x, y, self.envi_im.header.class_names[z]))
                elif self.colorDisplay.get():
                    r = self.envi_im.get_value(y, x, self.redBand.get())
                    g = self.envi_im.get_value(y, x, self.greenBand.get())
                    b = self.envi_im.get_value(y, x, self.blueBand.get())
                    self.status.set("(%d,%d)=(%g,%g,%g)" % (x, y, r, g, b))
                else:                
                    self.status.set("(%d,%d)=%g" % (x, y, z))

    def rollWheel(self, event):
        oldzoom = self.zoom
        if WINDOWS:
            if event.delta>0:  # zoom in
                self.zoom = min(20.0, self.zoom * 1.1)
            elif event.delta<0: # zoom out
                self.zoom = max(0.1, self.zoom / 1.1)
        else:
            if event.num == 4:  # zoom in
                self.zoom = min(20.0, self.zoom * 1.1)
            elif event.num == 5: # zoom out
                self.zoom = max(0.1, self.zoom / 1.1)
##        print self.zoom, event.delta, event.x, event.y
##        self.status.set('Zoom %0.f' % (self.zoom,))
        if self.zoom != oldzoom:
            self.load_data()

    def zoom_in(self):
        self.zoom = min(20.0, self.zoom * 2.0)
        self.load_data()

    def zoom_reset(self):
        self.zoom = 1.0
        self.load_data()

    def zoom_out(self):
        self.zoom = max(0.1, self.zoom / 2.0)
        self.load_data()

    def create_valueviewer(self):
        if not hasattr(self, 'valueviewer'):
            self.valueviewer = tkValueViewer.ValueViewer(self, title='View Values', command=self.value_window_returns)
            self.valueviewer.withdraw()

    def create_stretchvaluewindow(self):
        if not hasattr(self, 'stretchvaluewindow'):
            self.stretchvaluewindow = tkStretchValueWindow.StretchValueWindow(self, command=self.load_data)
            self.stretchvaluewindow.withdraw()

    def custom_stretch(self):
        self.stretchvaluewindow.deiconify()

    def toggle_valueviewer(self):
        if self.viewValuesWindow.get():
            self.valueviewer.deiconify()
        else:
            self.valueviewer.withdraw()

    def toggle_movie(self):
        if hasattr(self, 'timer_id'):
            self.master.after_cancel(self.timer_id)
        if self.viewMovie.get():
            self.step_slider()
        else:
            self.check_file()

    def toggle_plotwindow(self):
        if self.viewPlotWindow.get():
            figure()
        else:
            close('all')

    def toggle_colordisplay(self):
        if self.colorDisplay.get():
            self.frameBW.grid_remove()
            self.frameRGB.grid()
        else:
            self.frameRGB.grid_remove()
            self.frameBW.grid()
        self.load_data()

    def show_values(self, x, y, label='', linewidth=1.0, xlbl='', ylbl='', color=None, band_names=None, do_plot=True, name='', clear=True):
        if do_plot and self.viewPlotWindow.get():
            if color:
                plot(x, y, label=label, linewidth=LINEWIDTH, color=color)
            else:
                plot(x, y, label=label, linewidth=LINEWIDTH)
            xlabel(xlbl)
            ylabel(ylbl)
            legend(loc=0)

        if clear:
            self.valueviewer.clear()

        self.valueviewer.add('# %s (%s)\n' % (name, label))
        if self.showBandnames.get() and band_names:
            for cx, cbn, cy in zip(x, band_names, y):
                self.valueviewer.add('%f %s %f\n' % (cx, cbn, cy))
        else:
            for cx, cy in zip(x, y):
                self.valueviewer.add(f'{cx} {cy}\n')

    def get_histogram(self, b):
        bf = b.flatten()
        # take out nan's
        bf = bf[where(~isnan(bf))]
        min_ = numpy.nanmin(bf)
        max_ = numpy.nanmax(bf)
        if NUMBINS < 1:
            bins = arange(min_, max_, 1)
        else:
            bins = arange(min_, max_, (max_ - min_) / float(NUMBINS))
##        hist = histogram2(bf, bins)
        hist, bins = numpy.histogram(bf, bins)
        return bins[:-1], hist

    def plot_histogram(self):
        if hasattr(self, 'envi_im'):
            self.viewPlotWindow.set(1)
            xlbl, ylbl = 'value', 'frequency'
            w = list(range(self.envi_im.samples))

            if self.colorDisplay.get():
                clf()
                band = self.redBand.get()
                s = self.envi_im[band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='r', name=self.nameIn.get())
                band = self.greenBand.get()
                s = self.envi_im[band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='g', name=self.nameIn.get(), clear=False)
                band = self.blueBand.get()
                s = self.envi_im[band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='b', name=self.nameIn.get(), clear=False)
            else:
                band = self.bandIn.get()
                s = self.envi_im[band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram band %d' % (band,), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, name=self.nameIn.get())

    def plot_histogram_viewport(self):
        if hasattr(self, 'envi_im'):
            self.viewPlotWindow.set(1)
            xlbl, ylbl = 'value', 'frequency'
#            w = list(range(self.envi_im.samples))
            x0, x1, y0, y1 = self.x0, self.x1, self.y0, self.y1 # get the viewport or display

            if self.colorDisplay.get():
                clf()
                band = self.redBand.get()
                s = self.envi_im[y0:y1, x0:x1, band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram x %d-%d, y %d-%d, band %d' % (x0, x1, y0, y1, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='r', name=self.nameIn.get())
                band = self.greenBand.get()
                s = self.envi_im[y0:y1, x0:x1, band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram x %d-%d, y %d-%d, band %d' % (x0, x1, y0, y1, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='g', name=self.nameIn.get(), clear=False)
                band = self.blueBand.get()
                s = self.envi_im[y0:y1, x0:x1, band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram x %d-%d, y %d-%d, band %d' % (x0, x1, y0, y1, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, color='b', name=self.nameIn.get(), clear=False)
            else:
                band = self.bandIn.get()
                s = self.envi_im[y0:y1, x0:x1, band]
                bins, hist = self.get_histogram(s)
                self.show_values(bins, hist/float(hist.sum()), label='histogram x %d-%d, y %d-%d, band %d' % (x0, x1, y0, y1, band), linewidth=LINEWIDTH, xlbl=xlbl, ylbl=ylbl, name=self.nameIn.get())

    def show_wavelengths(self):
        if hasattr(self, 'envi_im'):
            if hasattr(self.envi_im, 'wavelength'):
                self.viewValuesWindow.set(1)
                self.toggle_valueviewer()
                self.show_values(list(range(self.envi_im.bands)), self.envi_im.wavelength, label='band wavelength', do_plot=False, name=self.nameIn.get())
            elif hasattr(self.envi_im, 'band_names'):
                self.viewValuesWindow.set(1)
                self.toggle_valueviewer()
                self.show_values(list(range(self.envi_im.bands)), self.envi_im.band_names, label='band names', do_plot=False, name=self.nameIn.get())

    def show_statistics(self):
        if hasattr(self, 'envi_im'):
            self.viewValuesWindow.set(1)
            self.toggle_valueviewer()
            self.valueviewer.clear()

            self.valueviewer.add('# IMAGE STATISTICS\n')
            if self.colorDisplay.get():
                rband = self.redBand.get()
                b = self.envi_im[rband]
                self.valueviewer.add('# Statistics of band %d\n'%(rband,))
                self._show_band_statistics(b)
                gband = self.greenBand.get()
                b = self.envi_im[gband]
                self.valueviewer.add('# Statistics of band %d\n'%(gband,))
                self._show_band_statistics(b)
                bband = self.blueBand.get()
                b = self.envi_im[bband]
                self.valueviewer.add('# Statistics of band %d\n'%(bband,))
                self._show_band_statistics(b)
            else:
                bwband = self.bandIn.get()
                b = self.envi_im[bwband]
                self.valueviewer.add('# Statistics of band %d\n'%(bwband,))
                self._show_band_statistics(b)

            self.valueviewer.add('# DISPLAY STATISTICS\n')
            self.valueviewer.add('# Bounding Box (x0, x1, y0, y1) = (%d, %d, %d, %d)\n'%(self.x0, self.x1, self.y0, self.y1))
            if self.colorDisplay.get():
                rband = self.redBand.get()
                b = self.envi_im[self.y0:self.y1, self.x0:self.x1, rband]
                self.valueviewer.add('# Statistics of band %d\n'%(rband,))
                self._show_band_statistics(b)
                gband = self.greenBand.get()
                b = self.envi_im[self.y0:self.y1, self.x0:self.x1, gband]
                self.valueviewer.add('# Statistics of band %d\n'%(gband,))
                self._show_band_statistics(b)
                bband = self.blueBand.get()
                b = self.envi_im[self.y0:self.y1, self.x0:self.x1, bband]
                self.valueviewer.add('# Statistics of band %d\n'%(bband,))
                self._show_band_statistics(b)
            else:
                bwband = self.bandIn.get()
                b = self.envi_im[self.y0:self.y1, self.x0:self.x1, bwband]
                self.valueviewer.add('# Statistics of band %d\n'%(bwband,))
                self._show_band_statistics(b)
                
    def _show_band_statistics(self, b):
        band = b.flatten()
        # skip the NaN's
        band = band[where(isnan(band)==False)]
        if len(band) == 0: # all NaN's
            pass
        else:
            band.sort()
            mean = band.mean()
            sdev = band.std()
            min_ = band[0]
            max_ = band[len(band)-1]
            perc01  = float(band[int(0.01*len(band))]) # why float???
            perc02 = float(band[int(0.02*len(band))])
            perc05 = float(band[int(0.05*len(band))])
            perc50 = float(band[int(0.50*len(band))])
            perc95 = float(band[int(0.95*len(band))])
            perc98 = float(band[int(0.98*len(band))])
            perc99 = float(band[int(0.99*len(band))])
            median_ = median(band)
            mad = median(fabs(band - median_))

            self.valueviewer.add('min  %f\n'%(min_,))
            self.valueviewer.add('max  %f\n\n'%(max_,))

            self.valueviewer.add('mean %f\n'%(mean,))
            self.valueviewer.add('sdev %f\n\n'%(sdev,))

            self.valueviewer.add('m-3s %f\n'%(mean-3*sdev,))
            self.valueviewer.add('m-2s %f\n'%(mean-2*sdev,))
            self.valueviewer.add('m-1s %f\n'%(mean-1*sdev,))
            self.valueviewer.add('m    %f\n'%(mean,))
            self.valueviewer.add('m+1s %f\n'%(mean+1*sdev,))
            self.valueviewer.add('m+2s %f\n'%(mean+2*sdev,))
            self.valueviewer.add('m+3s %f\n\n'%(mean+3*sdev,))
            
            self.valueviewer.add(' 1%%  %f\n'%(perc01,))
            self.valueviewer.add(' 2%%  %f\n'%(perc02,))
            self.valueviewer.add(' 5%%  %f\n'%(perc05,))
            self.valueviewer.add('50%%  %f\n'%(perc50,))
            self.valueviewer.add('95%%  %f\n'%(perc95,))
            self.valueviewer.add('98%%  %f\n'%(perc98,))
            self.valueviewer.add('99%%  %f\n\n'%(perc99,))

            self.valueviewer.add('median    %f\n'%(median_,))
            self.valueviewer.add('MAD       %f\n\n'%(mad,))

            self.valueviewer.add('med-2mad  %f\n'%(median_-2*mad,))
            self.valueviewer.add('med+2mad  %f\n\n'%(median_+2*mad,))

    def value_window_returns(self, value):
        self.viewValuesWindow.set(0)

    def canvas_resize(self, ev):
##        print ev.width, ev.height
##        print self.canvas['width'], self.canvas['height']
##        print self.canvas.winfo_width(), self.canvas.winfo_height()
##        self.canvas.config(width=ev.width-2, height=ev.height-2)
##        print self.canvas['width'], self.canvas['height']
        self.load_data()

    def scrolly_handler(self, *args):
##        print args
        d = {'units':0.01, 'pages':0.1}
        a, b = self.scrolly.get()
##        print a, b
        if args[0]=='scroll':
            inc = int(args[1]) * d[args[2]]
            self.scrolly.set(a+inc, b+inc)
        elif WINDOWS and args[0]=='moveto':
            new_a = float(args[1])
            self.scrolly.set(new_a, max(1, b + new_a - a))
        self.load_data()

    def scrollx_handler(self, *args):
##        print args
        d = {'units':0.01, 'pages':0.1}
        a, b = self.scrollx.get()
##        print a, b
        if args[0]=='scroll':
            inc = int(args[1]) * d[args[2]]
            self.scrollx.set(a+inc, b+inc)
        elif WINDOWS and args[0]=='moveto':
            new_a = float(args[1])
            self.scrollx.set(new_a, max(1, b + new_a - a))
        self.load_data()

    def key_press(self):
        print("key")

    def toggle_flip_left_right(self):
        a, b = self.scrollx.get()
        a, b = 1-b, 1-a
        self.scrollx.set(a, b)
        self.load_data()

    def toggle_flip_top_bottom(self):
        a, b = self.scrolly.get()
        a, b = 1-b, 1-a
        self.scrolly.set(a, b)
        self.load_data()

    def pan_grab(self, event):
        self.grab_x, self.grab_y = event.x, event.y

    def pan_drag(self, event):
        pass

    def pan_do(self, event):
        dx, dy = event.x - self.grab_x, event.y - self.grab_y

        a, b = self.scrollx.get()
        M = self.canvas.winfo_width()
        dx = dx * (b - a) / M
        a, b = a - dx, b - dx
        self.scrollx.set(a, b)

        a, b = self.scrolly.get()
        N = self.canvas.winfo_height()
        dy = dy * (b - a) / N
        a, b = a - dy, b - dy
        self.scrolly.set(a, b)
        
        self.load_data()

    def makeWindow(self, master=None):
        # variables
        self.nameIn = StringVar()
        self.bandIn = IntVar()
        self.nameShadow = StringVar()
        self.stretch = StringVar()
        self.status = StringVar()
        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        self.inverted = IntVar(value=0)
        self.satenh = IntVar(value=0)
        self.profile = StringVar(value='pz')
        self.profilemode = StringVar(value='single')
        self.viewValuesWindow = IntVar(value=0)
        self.viewPlotWindow = IntVar(value=1)
        self.viewFlipLeftRight = IntVar(value=0)
        self.viewFlipTopBottom = IntVar(value=0)

        self.colorDisplay = IntVar(value=0)
        self.redBand = IntVar()
        self.greenBand = IntVar()
        self.blueBand = IntVar()

        self.pseudoColor = StringVar()

        self.viewMovie = IntVar(value=0)

        self.showBandnames = IntVar()
        self.showBandnames.set(0)

        self.zoom = 1

        row = 0

        # Menubar
        frame = Frame(master=self)
        frame.grid(row=row, column=0, sticky=W)

        mb = Menubutton(frame, text='File')
        mb.grid(row=0, column=0)

        menu = Menu(mb)
        mb['menu'] = menu

        menu.add_checkbutton(label='Sort on Wav.', variable=self.sortWav)
        menu.add_checkbutton(label='Use BBL', variable=self.useBBL)
        menu.add_separator()
        menu.add_command(label='Open image', command=self.pick_input)
        menu.add_command(label='Open shadow', command=self.pick_shadow)
        menu.add_command(label='Save display as', command=self.save_image)
        menu.add_command(label='Exit', command=self.quit)

        # next menubutton
        mb = Menubutton(frame, text='Stretch')
        mb.grid(row=0, column=1)

        menu = Menu(mb)
        mb['menu'] = menu

        self.create_stretchvaluewindow()
        menu.add_radiobutton(label='No Stretch', value='NO', variable=self.stretch, command=self.load_data)
        menu.add_radiobutton(label='Min-Max', value='MM', variable=self.stretch, command=self.load_data)
        menu.add_radiobutton(label='1%-99%', value='1P', variable=self.stretch, command=self.load_data)
        menu.add_radiobutton(label='Mean +/- 2 * Stddev', value='SD', variable=self.stretch, command=self.load_data)
        menu.add_radiobutton(label='Median +/- 3 * MAD', value='MAD', variable=self.stretch, command=self.load_data)
        menu.add_radiobutton(label='Histogram Equalization', value='HEQ', variable=self.stretch, command=self.load_data)
        menu.add_radiobutton(label='Custom Stretch', value='Custom', variable=self.stretch, command=self.custom_stretch)
        self.stretch.set("1P")
        
        menu.add_separator()
        menu.add_checkbutton(label='Inverted', variable=self.inverted, command=self.load_data)
        menu.add_checkbutton(label='Saturation Enhanced', variable=self.satenh, command=self.load_data)
        menu.add_separator()
        menu.add_radiobutton(label='No Pseudo-color', value='none', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Rainbow (bright)', value='rainbow', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Rainbow (dark->bright)', value='rainbow2', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Spiral (dark->bright)', value='spiral', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Spiral2', value='spiral2', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Spiral3', value='spiral3', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Blue-Red', value='bluered', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Green-Red', value='greenred', variable=self.pseudoColor, command=self.load_data)
        menu.add_radiobutton(label='Random', value='random', variable=self.pseudoColor, command=self.load_data)
        self.pseudoColor.set('none')

        # next menubutton
        mb = Menubutton(frame, text='View')
        mb.grid(row=0, column=2)

        menu = Menu(mb)
        mb['menu'] = menu

        self.create_valueviewer()
        menu.add_checkbutton(label='Color Display', variable=self.colorDisplay, command=self.toggle_colordisplay)
        menu.add_checkbutton(label='Movie', variable=self.viewMovie, command=self.toggle_movie)
        menu.add_separator()
        menu.add_checkbutton(label='Values Window', variable=self.viewValuesWindow, command=self.toggle_valueviewer)
        menu.add_checkbutton(label='Show Band Names', variable=self.showBandnames)
        menu.add_separator()
        menu.add_checkbutton(label='Plot Window', variable=self.viewPlotWindow, command=self.toggle_plotwindow)
        menu.add_separator()

        menu.add_radiobutton(label='X profile', value='px', variable=self.profile)
        menu.add_radiobutton(label='Y profile', value='py', variable=self.profile)
        menu.add_radiobutton(label='Z profile', value='pz', variable=self.profile)
        self.profile.set("pz")

        menu.add_separator()
        menu.add_radiobutton(label='single profile', value='single', variable=self.profilemode)
        menu.add_radiobutton(label='mean profile', value='mean', variable=self.profilemode)
        self.profilemode.set('single')

        menu.add_separator()
        menu.add_checkbutton(label='Flip left-right', variable=self.viewFlipLeftRight, command=self.toggle_flip_left_right)
        menu.add_checkbutton(label='Flip top-bottom', variable=self.viewFlipTopBottom, command=self.toggle_flip_top_bottom)

        # next menubutton
        mb = Menubutton(frame, text='Zoom')
        mb.grid(row=0, column=3)

        menu = Menu(mb)
        mb['menu'] = menu

        menu.add_command(label='Zoom In', command=self.zoom_in)
        menu.add_command(label='Normal', command=self.zoom_reset)
        menu.add_command(label='Zoom Out', command=self.zoom_out)

        # next menubutton
        mb = Menubutton(frame, text='Info')
        mb.grid(row=0, column=4)

        menu = Menu(mb)
        mb['menu'] = menu

        menu.add_command(label='Histogram Image', command=self.plot_histogram)
        menu.add_command(label='Histogram Display', command=self.plot_histogram_viewport)
        menu.add_command(label='Show Wavelengths', command=self.show_wavelengths)
        menu.add_command(label='Show Statistics', command=self.show_statistics)

        row = row + 1

        # Scale bar
        frame = Frame(master=self)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(1, weight=1)

        Label(frame, text="Band").grid(row=0, column=0, sticky=W)
        self.scale = Scale(frame, orient=HORIZONTAL, from_=0, to=100, variable=self.bandIn, showvalue=0, command=self.scale_command)
        self.scale.grid(row=0, column=1, sticky=W+E)
        self.scale.bind("<ButtonRelease>", self.scale_handler)
        self.scalebox = Entry(frame, width=6)
        self.scalebox.bind('<Key-Return>', lambda event: self.scale.set(self.scalebox.get()))
        self.scalebox.grid(row=0, column=2, sticky=W)

        self.frameBW = frame

        # Scale bars for color
        frame = Frame(master=self)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(1, weight=1)

        srow = 0
        Label(frame, text="Red band").grid(row=srow, column=0, sticky=W)
        self.Rscale = Scale(frame, orient=HORIZONTAL, from_=0, to=100, variable=self.redBand, showvalue=0, command=self.Rscale_command)
        self.Rscale.grid(row=srow, column=1, sticky=W+E)
        self.Rscale.bind("<ButtonRelease>", self.Rscale_handler)
        self.Rscalebox = Entry(frame, width=6)
        self.Rscalebox.bind('<Key-Return>', lambda event: self.Rscale.set(self.Rscalebox.get()))
        self.Rscalebox.grid(row=srow, column=2, sticky=W)

        srow = 1
        Label(frame, text="Green band").grid(row=srow, column=0, sticky=W)
        self.Gscale = Scale(frame, orient=HORIZONTAL, from_=0, to=100, variable=self.greenBand, showvalue=0, command=self.Gscale_command)
        self.Gscale.grid(row=srow, column=1, sticky=W+E)
        self.Gscale.bind("<ButtonRelease>", self.Gscale_handler)
        self.Gscalebox = Entry(frame, width=6)
        self.Gscalebox.bind('<Key-Return>', lambda event: self.Gscale.set(self.Gscalebox.get()))
        self.Gscalebox.grid(row=srow, column=2, sticky=W)

        srow = 2
        Label(frame, text="Blue band").grid(row=srow, column=0, sticky=W)
        self.Bscale = Scale(frame, orient=HORIZONTAL, from_=0, to=100, variable=self.blueBand, showvalue=0, command=self.Bscale_command)
        self.Bscale.grid(row=srow, column=1, sticky=W+E)
        self.Bscale.bind("<ButtonRelease>", self.Bscale_handler)
        self.Bscalebox = Entry(frame, width=6)
        self.Bscalebox.bind('<Key-Return>', lambda event: self.Bscale.set(self.Bscalebox.get()))
        self.Bscalebox.grid(row=srow, column=2, sticky=W)

        frame.grid(row=row, column=0, sticky=W+E)
        frame.grid_remove()

        self.frameRGB = frame

        row = row + 1
        
        stretchrow = row
        
        # the canvas
        frame = Frame(master=self)
        frame.grid(row=row, column=0, sticky=N+S+W+E)
##        frame.pack(fill=BOTH, expand=YES)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.canvas = Canvas(frame, highlightthickness=0, width=400, height=400) #, bg='red', scrollregion=(0, 0, 400, 400))
        self.canvas.grid(row=0, column=0, sticky=N+S+W+E)
##        self.canvas.pack(fill=BOTH, expand=YES)
        self.canvas.bind("<Button-1>", self.button_handler)
        self.canvas.bind("<Button-2>", lambda ev: self.zoom_reset())
        self.canvas.bind("<Motion>", self.motion_handler)
        self.canvas.bind('<4>', self.rollWheel)
        self.canvas.bind('<5>', self.rollWheel)
        master.bind('<MouseWheel>', self.rollWheel) # for Windows!
        self.canvas.bind('<Configure>', self.canvas_resize)
        self.canvas.bind("<Button-3>", self.pan_grab)
##        self.canvas.bind("<B3-Motion>", self.pan_drag)
        self.canvas.bind("<B3-ButtonRelease>", self.pan_do)

        # Vertical scroll bar
        self.scrolly=Scrollbar(frame, orient=VERTICAL, jump=1, command=self.scrolly_handler) #, command=self.canvas.yview)
        self.scrolly.grid(row=0, column=1, sticky=N+S)
        self.scrolly.set(0, 0.1)

        # Horizontal scroll bar
        self.scrollx=Scrollbar(frame, orient=HORIZONTAL, jump=1, command=self.scrollx_handler) #, command=self.canvas.xview)
        self.scrollx.grid(row=1, column=0, sticky=W+E)
        self.scrollx.set(0, 0.1)

##
##        # attach canvas to scrollbars
##        self.canvas.configure(yscrollcommand=self.scrolly.set)
##        self.canvas.configure(xscrollcommand=self.scrollx.set)

        row = row + 1

        # Status bar
        frame = Frame(master=self)
        frame.grid(row=row, column=0)
        Label(frame, textvariable=self.status).grid(row=0, column=0)
        
        # allow column=1 and row=5 to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(stretchrow, weight=1)

# create the root
root = Tk()
# create the application
app = Application(root)
#set title
root.title("Image Viewer")
# handle the 'X' button
root.protocol("WM_DELETE_WINDOW", root.quit)
# start event loop
root.mainloop()

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())
conf.set_option('histogram-bins', NUMBINS)

# destroy application after event loop ends
root.destroy()

# close all figures
close('all')
