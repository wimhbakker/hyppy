#!/usr/bin/python3
#
#     tkThermalCorrection.py
#
#   Estimates temperature and does a thermal correction
#
#   Created: WHB 20090515
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
    import thermal_correction
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_Tcor'
THERMFIX = '_T'
#LOGEXT = '.log'

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
        self.message("Thermal Correction.")
        self.message(about.about)
    
    def do_run(self) :
#        self.logFile = self.nameOut.get() + LOGEXT
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Thermal Out: " + self.thermOut.get())
        self.message("Running, please wait...")
        try:
            thermal_correction.thermal_correction(self.nameIn.get(),
                      self.nameOut.get(),
                      self.thermOut.get(),
                      sort_wavelengths=self.sortWav.get(),
                      use_bbl=self.useBBL.get(),
                      message=self.message,
                      progress=self.progressBar)
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
                self.thermOut.set(name + THERMFIX)
            else:
                names = name.rsplit('.', 1)
                self.nameOut.set(names[0] + POSTFIX + '.' + names[1])
                self.thermOut.set(names[0] + THERMFIX + '.' + names[1])

##    def pick_continuum(self):
##        self.message("Pick continuum removed image.")
##        name = self.nameIn.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
##        name = askopenfilename(title='Open Continuum Removed',
##                                   initialdir=idir,
##                                   initialfile='')
##        if name:
##            self.nameHull.set(name)
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def pick_thermal(self):
        self.message("Pick thermal output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Thermal Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.thermOut.set(name)

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
        self.nameHull = StringVar()
        self.nameOut = StringVar()
        self.thermOut = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(1)
        self.useBBL = IntVar()
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav, state=DISABLED).grid(row=row, column=1, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=row, column=1, sticky=W)

        row = row + 1

        # input file
        Label(self, text="Input").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameIn, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_input).grid(row=row, column=2, sticky=W)

        row = row + 1

        # output file
        Label(self, text="Output").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameOut, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output).grid(row=row, column=2, sticky=W)

        row = row + 1

        # thermal output file
        Label(self, text="Thermal").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.thermOut, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_thermal).grid(row=row, column=2, sticky=W)

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
root.title("Thermal Correction")
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('use-bbl', app.useBBL.get())

root.destroy()
