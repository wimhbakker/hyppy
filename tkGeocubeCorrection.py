#!/usr/bin/python3
#
#     tkGeoCorrection.py
#
#   Reads Mars JDAT spectrum plus geocube and produces
#   a geocoded image.
#
#   Created: WHB 20100322
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
    import geo_correction
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_Gcor'
#LOGEXT = '.log'

DESCRIPTION = "OMEGA Geometric Correction"

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
        self.message("Using Geocube file")
    
    def do_run(self) :
#        self.logFile = self.nameOut.get() + LOGEXT
        self.message("In: " + self.nameIn.get())
        self.message("GeoCube: " + self.nameGeoCube.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Use Polar Projection: " + str(self.polar.get()))
        self.message("Running, please wait...")
        try:
            geo_correction.omega_geo_correction(self.nameIn.get(),
                      self.nameOut.get(),
                      geocube=self.nameGeoCube.get(),
                      polar=self.polar.get(),
                      sort_wavelengths=self.sortWav.get(),
                      use_bbl=self.useBBL.get(),
                      message=self.message, progress=self.progressBar)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

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
            # generate output name
#            if self.nameOut.get() == "":
            if name[-4] != '.':
                self.nameOut.set(name + POSTFIX)
            else:
                names = name.rsplit('.', 1)
                self.nameOut.set(names[0] + POSTFIX + '.' + names[1])

    def pick_geocube_spectrum(self):
        self.message("Pick GeoCube file.")
        self.message("Usually ends with '_geocube'")
##        name = self.nameIn.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open GeoCube file',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameGeoCube.set(name)
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def toLogFile(self, s):
        if hasattr(self, 'logFile'):
            f = open(self.logFile, 'a')
            f.write(s)
            f.close()

    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
            self.toLogFile(s)
        else:
            self.text.insert(END, s + '\n')
            self.toLogFile(s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self):
        # variables
        self.choice = StringVar()
        self.nameIn = StringVar()
        self.nameGeoCube = StringVar()
        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(0)
        self.useBBL = IntVar()
        self.useBBL.set(0)
        self.polar = IntVar()
        self.polar.set(0)

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav, state=DISABLED).grid(row=row, column=1, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL, state=DISABLED).grid(row=row, column=1, sticky=W)

        row = row + 1

        # input file
        Label(self, text="Input").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameIn, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_input).grid(row=row, column=2, sticky=W)

        row = row + 1

        # input geocube file
        Label(self, text="GeoCube").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameGeoCube, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_geocube_spectrum).grid(row=row, column=2, sticky=W)

        row = row + 1

        # output file
        Label(self, text="Output").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameOut, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output).grid(row=row, column=2, sticky=W)

        row = row + 1

##        # checkbutton
        Checkbutton(self, text="Use polar projection", variable=self.polar).grid(row=row, column=1, sticky=W)
        
        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, columnspan=3, sticky=W+E)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)

        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # text frame
        frame = Frame(self)
        frame.grid(row=row, column=0, columnspan=3, sticky=N+S+W+E)
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
        self.progressBar.grid(row=row, column=0, columnspan=3, sticky=W+E)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()
root.destroy()
