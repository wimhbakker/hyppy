#!/usr/bin/python3
#
#     tkDarkWhiteRef.py
#
#   Created: WHB 20160304
#   Modified: WHB 20180116, added robust use of white reference
#
##
## Copyright (C) 2016 Wim Bakker
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
    import darkwhiteref
    import specim
    import postfix
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_dwref2'

DESCRIPTION = "Dark/White Reference"

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
        self.message("Dark / White Reference")
        self.message(about.about)
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            darkwhiteref.darkwhiteref(self.nameIn.get(), self.nameDarkRef.get(),
                  self.nameWhiteRef.get(), self.nameOut.get(),
                  robust=self.robust.get(),
                  datatype=self.dataType.get(),
                  correct_dark=self.correct_dark.get(),
                  correct_white=self.correct_white.get(),
                  message=self.message,
                  progress=self.progressBar)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))
            traceback.print_tb(sys.exc_info()[2])

    def do_exit(self):
        root.quit()

    def pick_manifest(self):
        self.message("Pick xml manifest file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Manifest',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            inputdir = os.path.dirname(name)
            conf.set_option('input-dir', inputdir)
            self.nameManifest.set(name)
            manifest = specim.get_manifest(name)
            darkref = getattr(manifest, 'darkref', '')
            whiteref = getattr(manifest, 'whiteref', '')
            capture = getattr(manifest, 'capture', '')
            if darkref:
                darkref = os.path.join(inputdir, darkref)
                self.nameDarkRef.set(darkref)
            if whiteref:
                whiteref = os.path.join(inputdir, whiteref)
                self.nameWhiteRef.set(whiteref)
            else:
                self.nameWhiteRef.set('')
            if capture:
                capture = os.path.join(inputdir, capture)
                self.nameIn.set(capture)
            self.nameOut.set(postfix.insert(os.path.join(inputdir, os.path.basename(capture)), POSTFIX))

    def pick_input(self):
        self.message("Pick input file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)
            self.nameOut.set(postfix.insert(name, POSTFIX))
        
    def pick_darkref(self):
        self.message("Pick dark reference file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Dark Reference',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameDarkRef.set(name)

    def pick_whiteref(self):
        self.message("Pick white reference file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open White Reference',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameWhiteRef.set(name)

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

    def makeWindow(self):
        # variables
        self.nameIn = StringVar()
        self.nameOut = StringVar()
        self.nameManifest = StringVar()
        self.nameDarkRef = StringVar()
        self.nameWhiteRef = StringVar()

        self.robust = IntVar()
        self.robust.set(conf.get_option('robust', 1))

        self.correct_dark = IntVar()
        self.correct_dark.set(conf.get_option('correct_dark', 0))

        self.correct_white = IntVar()
        self.correct_white.set(conf.get_option('correct_white', 0))

        self.dataType = StringVar()
        self.dataType.set(conf.get_option('data-type', 'float32'))

##        self.sortWav = IntVar()
##        self.useBBL = IntVar()
##
##        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
##        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        row = 0

##        # checkbutton
##        frame = Frame(self, bd=2, relief=GROOVE)
##        frame.grid(row=row, column=0, sticky=W+E)
##        
##        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=0, column=0, sticky=W)
##        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=1, column=0, sticky=W)
##
##        row = row + 1

        # input and output file names
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(1, weight=1)

        frow = 0

        Label(frame, text="Manifest").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameManifest, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_manifest).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="OR:").grid(row=frow, column=1, sticky=W)

        frow = frow + 1

        Label(frame, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_input).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="DarkRef").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameDarkRef, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_darkref).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="WhiteRef").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameWhiteRef, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_whiteref).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        row = row + 1

##        # options
##        frame = Frame(self, bd=2, relief=GROOVE)
##        frame.grid(row=row, column=0, sticky=W+E)
##
##        Label(frame, text="Max mean: ").grid(row=0, column=0, sticky=W)
##        Entry(frame, textvariable=self.maxMean, width=10).grid(row=0, column=1, sticky=W)
##        
##        Label(frame, text="Max stddev: ").grid(row=1, column=0, sticky=W)
##        Entry(frame, textvariable=self.maxStddev, width=10).grid(row=1, column=1, sticky=W)
##
##        Label(frame, text="Replace bad pixels: ").grid(row=2, column=0, sticky=W)
##        Checkbutton(frame, text="", variable=self.replaceNaN).grid(row=2, column=1, sticky=W)
##
##        row = row + 1

        # frame, offer output format choices
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(4, weight=1)

        Label(frame, text="Data Type:").grid(row=0, column=0, sticky=E)
        Radiobutton(frame, variable=self.dataType, value='int16', text='int16').grid(row=0, column=1, sticky=W)
        Radiobutton(frame, variable=self.dataType, value='uint16', text='uint16').grid(row=0, column=2, sticky=W)
        Radiobutton(frame, variable=self.dataType, value='float32', text='float32').grid(row=0, column=3, sticky=W)
        Radiobutton(frame, variable=self.dataType, value='float64', text='float64').grid(row=0, column=4, sticky=W)
##        self.dataType.set('float32')

        row = row + 1

        Checkbutton(self, text="Use robust white reference, use whitest 50%.", variable=self.robust).grid(row=row, column=0, sticky=W)

        row = row + 1

        Checkbutton(self, text="Correct dark reference bias.", variable=self.correct_dark).grid(row=row, column=0, sticky=W)

        row = row + 1

        Checkbutton(self, text="Correct white panel, assume 98% reflectance.", variable=self.correct_white).grid(row=row, column=0, sticky=W)

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

##conf.set_option('use-bbl', app.useBBL.get())
##conf.set_option('sort-wavelength', app.sortWav.get())
conf.set_option('data-type', app.dataType.get())
conf.set_option('robust', app.robust.get())
conf.set_option('correct_dark', app.correct_dark.get())
conf.set_option('correct_white', app.correct_white.get())

root.destroy()
