#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#     tkAtmoCorrection.py
#
#   Estimates optical thickness and does atmospheric correction
#
#   Created: WHB 20100209
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
    import atmo_correction
    import postfix
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_Acor'
ALPHAFIX = '_alpha'
#LOGEXT = '.log'

DESCRIPTION = "Atmospheric Correction"

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
        self.message("NO correction is attempted above 3.5 micron!")
    
    def do_run(self) :
#        self.logFile = self.nameOut.get() + LOGEXT
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Alpha Out: " + self.alphaOut.get())
        self.message("Running, please wait...")
        try:
            atmo_correction.atmo_correction(self.nameIn.get(),
                      self.nameAtmos.get(),
                      self.nameOut.get(),
                      self.alphaOut.get(),
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
            self.nameOut.set(postfix.insert(name, POSTFIX))
            self.alphaOut.set(postfix.insert(name, ALPHAFIX))

    def pick_atmos(self):
        self.message("Pick atmospheric transmission file.")
##        name = self.nameAtmos.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
        name = conf.get_option('transmission-file', os.path.expanduser('~/transmission.dat'))
        
        name = askopenfilename(title='Open Atmospheric Transmission File',
                                   initialdir=os.path.dirname(name),
                                   initialfile=os.path.basename(name))
        if name:
            conf.set_option('transmission-file', name)
            self.nameAtmos.set(name)

    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def pick_alpha(self):
        self.message("Pick alpha output file.")
        odir = conf.get_option('alpha-dir', conf.get_option('output-dir'))
        name = asksaveasfilename(title='Open Alpha Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('alpha-dir', os.path.dirname(name))
            self.alphaOut.set(name)

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
        self.nameAtmos = StringVar()
        self.nameOut = StringVar()
        self.alphaOut = StringVar()

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

        # atmospheric transmission file
        Label(self, text="Atm. trans.").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameAtmos, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_atmos).grid(row=row, column=2, sticky=W)

        row = row + 1

        # output file
        Label(self, text="Output").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameOut, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output).grid(row=row, column=2, sticky=W)

        row = row + 1

        # "optical thicknes", alpha, output file
        Label(self, text="Alpha").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.alphaOut, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_alpha).grid(row=row, column=2, sticky=W)

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

conf.set_option('use-bbl', app.useBBL.get())

root.destroy()
