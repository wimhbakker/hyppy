#!/usr/bin/python3
#
#     tkResampleSpecLib.py
##  Created 20190207 WHB reample spectral library
##
## Copyright (C) 2018 Wim Bakker
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
import traceback
from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import envi2
    import resamplespeclib
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Convert/Resample SpecLib"

POSTFIX = None

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
        self.message("Resampling, please wait...")
        try:
            if self.to_envispeclib:
                resamplespeclib.resample_speclib_to_envi(self.nameIn.get(),
                                to_spec=self.toSpec.get(),
                                  enviout=self.nameOut.get(),
                                  message=self.message,
                                    sort_wavelengths=self.sortWav.get(),
                                    use_bbl=self.useBBL.get(),
                                recursive=self.recursive.get(),
                                wmultiplier=self.wMultiplier.get(),
                                    progress=self.progressBar)
            else:
                resamplespeclib.resample_speclib(self.nameIn.get(),
                                to_spec=self.toSpec.get(),
                                  dirout=self.nameOut.get(),
                                  message=self.message,
                                    sort_wavelengths=self.sortWav.get(),
                                    use_bbl=self.useBBL.get(),
                                recursive=self.recursive.get(),
                                wmultiplier=self.wMultiplier.get(),
                                    progress=self.progressBar)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))
            traceback.print_exc(file=sys.stdout)

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)

    def pick_input_dir(self):
        self.message("Pick input directory.")
        idir = conf.get_option('input-dir')
        name = askdirectory(title='Open Input Directory',
                                   initialdir=idir)
        if name:
            conf.set_option('input-dir', name)
            self.nameIn.set(name)

    def pick_tospec(self):
        self.message("Pick Resample To Image or Spectrum File.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Resample Image or Spectrum',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.toSpec.set(name)

    def pick_output_dir(self):
        self.message("Pick output directory.")
        odir = conf.get_option('output-dir')
        name = askdirectory(title='Open Output Directory',
                                   initialdir=odir,
                                   mustexist=False)
        if name:
            conf.set_option('output-dir', name)
            self.nameOut.set(name)
            self.to_envispeclib = False

    def pick_output_envi(self):
        self.message("Pick output ENVI speclib file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output ENVI Speclib file',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)
            self.to_envispeclib = True

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
        self.toSpec = StringVar()
        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL = IntVar()
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        self.recursive = IntVar()
        self.recursive.set(conf.get_option('recursive', 0, type_=int))

        self.wMultiplier = DoubleVar()
        self.wMultiplier.set(conf.get_option('wmultiplier', 1.0, type_=float))

        row = 0

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

##        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=0, column=0, sticky=W)
##        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=1, column=0, sticky=W)

        Checkbutton(frame, text="Recursively scan input dirs", variable=self.recursive).grid(row=0, column=0, sticky=W)

        Label(frame, text="Input wavelength multiplier").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self.wMultiplier, width=10).grid(row=2, column=1, sticky=W+E)

        row = row + 1

        # frame 1
        self.frame1 = Frame(self, bd=2, relief=GROOVE)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(1, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        Label(self.frame1, text="Input SpecLib").grid(row=0, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn).grid(row=0, column=1, sticky=W+E)
        Button(self.frame1, text='file', command=self.pick_input).grid(row=0, column=2, sticky=W+E)
        Button(self.frame1, text='dir', command=self.pick_input_dir).grid(row=0, column=3, sticky=W+E)

        row = row + 1

        Label(self.frame1, text="Resample To").grid(row=row, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.toSpec).grid(row=row, column=1, sticky=W+E)
        Button(self.frame1, text='file', command=self.pick_tospec).grid(row=row, column=2, sticky=W+E)

        row = row + 1

        Label(self.frame1, text="Output File or Dir").grid(row=row, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameOut, state=DISABLED).grid(row=row, column=1, sticky=W+E)
        Button(self.frame1, text='ENVI', command=self.pick_output_envi).grid(row=row, column=2, sticky=W+E)
        Button(self.frame1, text='ASCII', command=self.pick_output_dir).grid(row=row, column=3, sticky=W+E)

        row = row + 1

        # frame 2
        self.frame2 = Frame(self, bd=2, relief=GROOVE)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)
        self.frame2.rowconfigure(0, weight=1)
        
        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

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
        
##        #pack everything
##        self.text.pack(side=LEFT)
##        self.scroll.pack(side=RIGHT,fill=Y)

        # allow column=... and row=... to stretch
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

conf.set_option('sort-wavelength', app.sortWav.get())
conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('recursive', app.recursive.get())
conf.set_option('wmultiplier', app.wMultiplier.get())

root.destroy()
