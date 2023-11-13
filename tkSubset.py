#!/usr/bin/python3
#
#     tkSubset.py
#
#   Created: WHB 20100510
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

from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

import numpy

try:
    import envi2
    from envi2.constants import *
    import subset
    import tkSelector
    import conf
    import about
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Make Subset"

POSTFIX = '_sub'

class Application(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        # create the frame, resizable
        self.grid(sticky=N+E+S+W)
        top=self.winfo_toplevel()

        # allow toplevel to stretch
        top.columnconfigure(0, weight=1)
        top.rowconfigure(0, weight=1)

        self.makeWindow()
        self.message(DESCRIPTION)
        self.message(about.about)
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())

        self.message("Making subset...")
        try:
            subset.subset(self.nameIn.get(), self.nameOut.get(),
                      output_format=self.format.get(),
                      top=self.top.get(),
                      bottom=self.bottom.get(),
                      left=self.left.get(),
                      right=self.right.get(),
                band_selection=getattr(self, 'band_selection', None),
                message=self.message,
                sort_wavelengths=self.sortWav.get(),
                use_bbl=self.useBBL.get(),
                          data_type=self.datatype.get())

            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            self.clear_band_selection()
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)
            # generate output names
            if self.nameOut.get() == "":
                if name[-4] != '.':
                    self.nameOut.set(name + POSTFIX)
                else:
                    names = name.rsplit('.', 1)
                    self.nameOut.set(names[0] + POSTFIX + '.' + names[1])
            # get image dimensions
            h = envi2.Header(fname=name)
            self.left.set(0)
            self.right.set(h.getsamples())
            self.top.set(0)
            self.bottom.set(h.lines)
            if hasattr(h, 'interleave'):
                self.format.set(h.interleave)
            if hasattr(h, 'data_type'):
                self.datatype.set(numpy.dtype(h.data_type).name)
            del h
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
        else:
            self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def set_band_selection(self, band_selection):
        self.band_selection = band_selection

    def clear_band_selection(self):
        if hasattr(self, 'band_selection'):
            del self.band_selection

    def do_band_select(self):
##        if hasattr(self, 'band_selector'):
##            self.band_selector.deiconify()
##        else:
        nameIn = self.nameIn.get()
        if nameIn:
            im = envi2.Open(nameIn,
                        sort_wavelengths=self.sortWav.get(),
                        use_bbl=self.useBBL.get())

            selection = getattr(im, 'wavelength', None)
            if selection is None:
                selection = getattr(im, 'band_names', None)
            if selection is None:
                selection = list(range(im.bands))

            tkSelector.Selector(selection,
                                master=self, title='Bands Selector',
                                command=self.set_band_selection)
            del im

    def makeWindow(self):
        # variables
        self.nameIn  = StringVar()
        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.useBBL  = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 1, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        self.top    = IntVar()
        self.bottom = IntVar()
        self.left   = IntVar()
        self.right  = IntVar()

        self.format = StringVar()
        self.datatype = StringVar()

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav).grid(row=row, column=0, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL, command=self.clear_band_selection).grid(row=row, column=0, sticky=W)

        row = row + 1

        # frame 1
        self.frame1 = Frame(self)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(1, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        frow = 0

        Label(self.frame1, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn).grid(row=frow, column=1, sticky=W+E)
        Button(self.frame1, text='Browse', command=self.pick_input).grid(row=frow, column=2, sticky=W+E)

        frow = frow + 1

        Label(self.frame1, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameOut).grid(row=frow, column=1, sticky=W+E)
        Button(self.frame1, text='Browse', command=self.pick_output).grid(row=frow, column=2, sticky=W+E)

        row = row + 1

        # frame, offer output format choices
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)

        Label(frame, text="Output Format:").grid(row=0, column=0, sticky=E)
        Radiobutton(frame, variable=self.format, value=ENVI_bip, text=ENVI_bip).grid(row=0, column=1, sticky=W)
        Radiobutton(frame, variable=self.format, value=ENVI_bil, text=ENVI_bil).grid(row=0, column=2, sticky=W)
        Radiobutton(frame, variable=self.format, value=ENVI_bsq, text=ENVI_bsq).grid(row=0, column=3, sticky=W)
        self.format.set(ENVI_bsq)

        row = row + 1

        # frame 0, offer processing choices
        self.frame0 = Frame(self, bd=1, relief=GROOVE)
        self.frame0.grid(row=row, column=0, sticky=N+E+S+W)

        Label(self.frame0, text="Spatial selection:").grid(row=0, column=0, sticky=E)
        Label(self.frame0, text="Samples:").grid(row=1, column=0, sticky=E)
        Entry(self.frame0, textvariable=self.left, width=6).grid(row=1, column=1, sticky=E)
        Entry(self.frame0, textvariable=self.right, width=6).grid(row=1, column=2, sticky=E)
        Label(self.frame0, text="Lines  :").grid(row=2, column=0, sticky=E)
        Entry(self.frame0, textvariable=self.top, width=6).grid(row=2, column=1, sticky=E)
        Entry(self.frame0, textvariable=self.bottom, width=6).grid(row=2, column=2, sticky=E)

        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)
        self.frame2.rowconfigure(0, weight=1)
        
        Button(self.frame2,text="Select Bands",command=self.do_band_select).grid(row=0, column=0, columnspan=2, sticky=W+E)

        # put data type selection here
        mb = Menubutton(self.frame2, text='Output Data Type', relief=RAISED)
        mb.grid(row=1, column=0, columnspan=2, sticky=W+E)

        menu = Menu(mb, tearoff=0)
        menu.add_radiobutton(label='same as input', value='keep', variable=self.datatype)
        menu.add_separator()
        menu.add_radiobutton(label='unsigned integer 8-bit (byte)', value='uint8', variable=self.datatype)
        menu.add_separator()
        menu.add_radiobutton(label='signed integer 16-bit', value='int16', variable=self.datatype)
        menu.add_radiobutton(label='signed integer 32-bit', value='int32', variable=self.datatype)
        menu.add_radiobutton(label='signed integer 64-bit', value='int64', variable=self.datatype)
        menu.add_separator()
        menu.add_radiobutton(label='unsigned integer 16-bit', value='uint16', variable=self.datatype)
        menu.add_radiobutton(label='unsigned integer 32-bit', value='uint32', variable=self.datatype)
        menu.add_radiobutton(label='unsigned integer 64-bit', value='uint64', variable=self.datatype)
        menu.add_separator()
        menu.add_radiobutton(label='floating point 32-bit', value='float32', variable=self.datatype)
        menu.add_radiobutton(label='floating point 64-bit', value='float64', variable=self.datatype)
        self.datatype.set('keep')

        mb.menu = menu
        mb["menu"] = mb.menu

        # end data type selection menu
        
        Button(self.frame2,text="Run",command=self.do_run).grid(row=2, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=2, column=1, sticky=W+E)

        row = row + 1

        # frame 3
        self.frame3 = Frame(self)
        self.frame3.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.rowconfigure(0, weight=1)
        
        self.text = Text(self.frame3, width=35, height=10)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        self.scroll=Scrollbar(self.frame3)
        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.text.yview)
        self.scroll.grid(row=0, column=1, sticky=N+S)

        # allow column=... and row=... to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
