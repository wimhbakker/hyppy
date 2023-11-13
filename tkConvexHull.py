#!/usr/bin/python3
#
#     tkConvexHull.py
#
#   A.k.a. Continuum Removed
#
#   Created: WHB 20090506
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
    import hull
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_cr'

DESCRIPTION = "Continuum Removal"

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
        self.message("Leave cutoff zero for no cutoff.")
    
    def get_cutoff(self):
        try:
            return self.cutoffWav.get()
        except ValueError:
            return None

    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            if self.choice.get()=='divide':
                hull.continuum_removal_divide(self.nameIn.get(), self.nameOut.get(),
                          cutoff=self.get_cutoff(),
                          sort_wavelengths=self.sortWav.get(),
                          use_bbl=self.useBBL.get(),
                          message=self.message, progress=self.progressBar)
            else:
                hull.continuum_removal_subtract(self.nameIn.get(), self.nameOut.get(), 
                          cutoff=self.get_cutoff(),
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
                self.nameOut.set(name + POSTFIX + self.choice.get()[0])
            else:
                names = name.rsplit('.', 1)
                self.nameOut.set(names[0] + POSTFIX + self.choice.get()[0] + '.' + names[1])
        
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
        self.choice = StringVar()
        self.nameIn = StringVar()
        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        self.cutoffWav = DoubleVar()
        co = conf.get_option('cutoff-wav', 3.5)
        if co:
            self.cutoffWav.set(co)
        else:
            self.cutoffWav.set(0)

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav).grid(row=row, column=1, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=row, column=1, sticky=W)

        row = row + 1

        # frame 0
        self.frame0 = Frame(self)
        self.frame0.grid(row=row, column=1, sticky=W)

        Radiobutton(self.frame0, variable=self.choice, value='divide', text='Divide').grid(row=0, column=0, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='subtract', text='Subtract').grid(row=0, column=1, sticky=W)
        self.choice.set(conf.get_option('method',"divide"))

        row = row + 1

        # input and output files
        Label(self, text="Input").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameIn, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_input).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self, text="Output").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameOut, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output).grid(row=row, column=2, sticky=W)

        row = row + 1

        # frame 0
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=1, columnspan=1, sticky=W+E)

        Label(frame, text="Cutoff wavelength (band)").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.cutoffWav, width=5).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, columnspan=3, sticky=W+E)
        self.frame2.rowconfigure(0, weight=1)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)
        
        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # Text frame
        stretchrow = row
        frame = Frame(self)
        frame.grid(row=row, column=0, columnspan=3, sticky=N+S+W+E)
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
        self.columnconfigure(1, weight=1)
        self.rowconfigure(stretchrow, weight=1)

        row = row + 1

        self.progressBar = ProgressBar(self)
        self.progressBar.grid(row=row, column=0, columnspan=3, sticky=W+E)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('method', app.choice.get())
conf.set_option('cutoff-wav', app.cutoffWav.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
