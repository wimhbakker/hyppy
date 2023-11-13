#!/usr/bin/python3
#
#     tkDestripe3D.py
#
#   Created:  WHB 20160301
#   Modified: WHB 20161018, added "apply offset"
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
import traceback
from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import destripefilt
    import postfix
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_dfilt'
POSTFIX_OFFSET = '_offset'

DESCRIPTION = "Destriping filter"

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
        self.message("Destriping using spatio-spectral filtering")
        self.message(about.about)
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Using %d neighborhood kernel." % (4 if self.smallKernel.get() else 8))
        self.message("Running, please wait...")
        try:
            destripefilt.destriping_filter(self.nameIn.get(), self.nameOut.get(),
                  foffset=self.nameOffset.get(),
                  maxmean=self.maxMean.get(), maxstddev=self.maxStddev.get() ,
                  replace_nan=self.replaceNaN.get(),
                  apply_offset=self.applyOffset.get(),
                  sort_wavelengths=self.sortWav.get(),
                  use_bbl=self.useBBL.get(), message=self.message,
                  progress=self.progressBar,
                  smallkernel=self.smallKernel.get())
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))
            traceback.print_tb(sys.exc_info()[2])

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input file.")
##        name = self.nameIn.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)
            self.nameOut.set(postfix.insert(name, POSTFIX))
            self.nameOffset.set(postfix.insert(name, POSTFIX_OFFSET))
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def pick_offset(self):
        self.message("Pick output offset file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Offset File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOffset.set(name)

    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
        else:
            self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self):
        # variables
        self.nameIn = StringVar()
        self.nameOut = StringVar()
        self.nameOffset = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(0)
        self.useBBL = IntVar()
        self.useBBL.set(0)

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        self.maxMean = DoubleVar()
        self.maxMean.set(conf.get_option('maxmean', 1000.0))
        self.maxStddev = DoubleVar()
        self.maxStddev.set(conf.get_option('maxstddev', 500.0))

        self.replaceNaN = IntVar()
        self.replaceNaN.set(conf.get_option('replace-nan', 0, type_=int))

        self.applyOffset = IntVar()
        self.applyOffset.set(conf.get_option('apply-offset', 1, type_=int))

        self.smallKernel = IntVar()
        self.smallKernel.set(conf.get_option('small-kernel', 0, type_=int))

        row = 0

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
        
        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=0, column=0, sticky=W)
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=1, column=0, sticky=W)

        row = row + 1

        # input and output file names
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(1, weight=1)

        frow = 0

        Label(frame, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_input).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="Offset").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOffset, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_offset).grid(row=frow, column=2, sticky=W)

        row = row + 1

        # options
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Label(frame, text="Use small kernel: ").grid(row=0, column=0, sticky=W)
        Checkbutton(frame, text="", variable=self.smallKernel).grid(row=0, column=1, sticky=W)

        Label(frame, text="Max mean difference: ").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.maxMean, width=10).grid(row=1, column=1, sticky=W)
        
        Label(frame, text="Max stddev of diff.: ").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self.maxStddev, width=10).grid(row=2, column=1, sticky=W)

        Label(frame, text="Apply offset: ").grid(row=3, column=0, sticky=W)
        Checkbutton(frame, text="", variable=self.applyOffset).grid(row=3, column=1, sticky=W)

        Label(frame, text="Replace bad pixels: ").grid(row=4, column=0, sticky=W)
        Checkbutton(frame, text="", variable=self.replaceNaN).grid(row=4, column=1, sticky=W)

        row = row + 1

        # frame 2
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        Button(frame,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(frame,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # Text frame
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+S+W+E)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        
        self.text = Text(frame, width=40, height=10)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        self.scroll=Scrollbar(frame)
        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.text.yview)
        self.scroll.grid(row=0, column=1, sticky=N+S)
        
        # allow column=1 and row=... to stretch
        self.columnconfigure(0, weight=1)
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

conf.set_option('maxmean', app.maxMean.get())
conf.set_option('maxstddev', app.maxStddev.get())
conf.set_option('apply-offset', app.applyOffset.get())
conf.set_option('replace-nan', app.replaceNaN.get())

conf.set_option('small-kernel', app.smallKernel.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
