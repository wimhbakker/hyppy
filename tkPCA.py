#!/usr/bin/python3
#
#     tkPCA.py
#
#   Created: WHB 20120416
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

try:
    import envi2
    import pca
    import tkSelector
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Principal Components."
POSTFIX = '_pca'
STATS = '.stats'

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
    
    def get_bbox(self):
        if self.useBbox.get():
            return self.X0.get(), self.X1.get(), self.Y0.get(), self.Y1.get()
        else:
            return None

    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            if self.nanSafe.get():
                pca.pca_bb_nansafe(self.nameIn.get(), self.nameOut.get(),
                      stats=self.nameStats.get(),
                      bbox=self.get_bbox(),
                      band_selection=getattr(self, 'band_selection', None),
                      sort_wavelengths=self.sortWav.get(),
                      use_bbl=self.useBBL.get(), message=self.message)
            elif self.useBbox.get():
                pca.pca_bb(self.nameIn.get(), self.nameOut.get(),
                      stats=self.nameStats.get(),
                      bbox=self.get_bbox(),
                      band_selection=getattr(self, 'band_selection', None),
                      sort_wavelengths=self.sortWav.get(),
                      use_bbl=self.useBBL.get(), message=self.message)
            else:
                pca.pca(self.nameIn.get(), self.nameOut.get(),
                      stats=self.nameStats.get(),
                      band_selection=getattr(self, 'band_selection', None),
                      sort_wavelengths=self.sortWav.get(),
                      use_bbl=self.useBBL.get(), message=self.message)
            self.message("Completed!")
        except ValueError:
            self.message('Image seems to contain NaNs. Try the "Exclude NaNs" option.')
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
            # generate output name
#            if self.nameOut.get() == "":
            if name[-4] != '.':
                self.nameOut.set(name + POSTFIX)
            else:
                names = name.rsplit('.', 1)
                self.nameOut.set(names[0] + POSTFIX + '.' + names[1])
            self.nameStats.set(self.nameOut.get() + STATS)
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)
            self.nameStats.set(name + STATS)

    def pick_stats(self):
        self.message("Pick statistics output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Statistics Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
##            conf.set_option('output-dir', os.path.dirname(name))
            self.nameStats.set(name)

    def message(self, s):
        self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def set_band_selection(self, band_selection):
        self.band_selection = band_selection

    def clear_band_selection(self):
        if hasattr(self, 'band_selection'):
            del self.band_selection

    def do_band_select(self):
        nameIn = self.nameIn.get()
        if nameIn:
            im = envi2.Open(nameIn,
                        sort_wavelengths=self.sortWav.get(),
                        use_bbl=self.useBBL.get())

            tkSelector.Selector(im.wavelength,
                                master=self, title='Bands Selector',
                                command=self.set_band_selection)
            del im

    def makeWindow(self):
        # variables
        self.nameIn = StringVar()
        self.nameOut = StringVar()
        self.nameStats = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(conf.get_option('sort-wavelength', 1, type_=int))
        self.useBBL = IntVar()
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        self.useBbox = IntVar()
        self.useBbox.set(conf.get_option('use-bbox', 0, type_=int))

        self.X0 = IntVar()
        self.X0.set(conf.get_option('x0', 0, type_=int))
        self.X1 = IntVar()
        self.X1.set(conf.get_option('x1', 1000, type_=int))
        self.Y0 = IntVar()
        self.Y0.set(conf.get_option('y0', 0, type_=int))
        self.Y1 = IntVar()
        self.Y1.set(conf.get_option('y1', 1000, type_=int))

        self.nanSafe = IntVar()
        self.nanSafe.set(conf.get_option('nan-safe', 0, type_=int))

        row = 0

        # frame for input/output
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        frow = 0

        # checkbutton
        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=frow, column=1, sticky=W)
        
        frow = frow + 1

        # checkbutton
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=frow, column=1, sticky=W)

        frow = frow + 1

        Label(frame, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_input).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="Stats").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameStats, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_stats).grid(row=frow, column=2, sticky=W)

        row = row + 1

        # frame for bounding box
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
##        frame.columnconfigure(0, weight=1)
##        frame.columnconfigure(1, weight=1)

        Checkbutton(frame, text="Subset", variable=self.useBbox).grid(row=0, column=0, sticky=W)
        Label(frame, text="Samples:").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.X0, width=5).grid(row=1, column=1, sticky=W)
        Entry(frame, textvariable=self.X1, width=5).grid(row=1, column=2, sticky=W)
        Label(frame, text="Lines:").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self.Y0, width=5).grid(row=2, column=1, sticky=W)
        Entry(frame, textvariable=self.Y1, width=5).grid(row=2, column=2, sticky=W)

        row = row + 1

        # frame for band selection
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(0, weight=1)

##        Label(frame, text="Bands:").grid(row=0, column=0, sticky=W)
        Button(frame,text="Select Bands",command=self.do_band_select).grid(row=0, column=0, sticky=W+E)
       
        row = row + 1

        # frame for nansafe
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
##        frame.columnconfigure(0, weight=1)
##        frame.columnconfigure(1, weight=1)

        Checkbutton(frame, text="Exclude NaNs", variable=self.nanSafe).grid(row=0, column=0, sticky=W)

        row = row + 1
        
        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, sticky=W+E)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)

        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # text frame
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+S+W+E)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.text = Text(frame, width=30, height=10)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        self.scroll=Scrollbar(frame)
        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.text.yview)
        self.scroll.grid(row=0, column=1, sticky=N+S)
        
        # allow column=1 and row=... to stretch
        self.columnconfigure(1, weight=1)
        self.rowconfigure(row, weight=1)

        row = row + 1

        self.progressBar = ProgressBar(self)
        self.progressBar.grid(row=row, column=0, sticky=W+E)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

conf.set_option('use-bbox', app.useBbox.get())
conf.set_option('x0', app.X0.get())
conf.set_option('x1', app.X1.get())
conf.set_option('y0', app.Y0.get())
conf.set_option('y1', app.Y1.get())

conf.set_option('nan-safe', app.nanSafe.get())

root.destroy()
