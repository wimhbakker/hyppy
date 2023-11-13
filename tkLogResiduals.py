#!/usr/bin/python3
#
#     tkLogResiduals.py
#
#   Created: WHB 20090616
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
    import logresiduals
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_lr'
POSTALBEDO = '_alb'
POSTRLUB = '_rlub'

DESCRIPTION = "Log Residuals"

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
        self.message("Running %s Residuals, please wait..." % (self.choice.get(),))
        try:
            if self.choice.get() == 'KWIK':
                logresiduals.kwikresiduals(self.nameIn.get(), self.nameOut.get(),
                                  albedo=self.nameAlbedo.get(), rlub=self.nameRLUB.get(),
                                  N=self.Nstddev.get(),
                                  sort_wavelengths=self.sortWav.get(),
                                  use_bbl=self.useBBL.get(), message=self.message,
                                  progress=self.progressBar)
            else:
                logresiduals.logresiduals(self.nameIn.get(), self.nameOut.get(),
                                  albedo=self.nameAlbedo.get(), rlub=self.nameRLUB.get(),
                                  N=self.Nstddev.get(),
                                  sort_wavelengths=self.sortWav.get(),
                                  use_bbl=self.useBBL.get(), message=self.message,
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
                self.nameAlbedo.set(name + POSTALBEDO)
                self.nameRLUB.set(name + POSTRLUB + '.txt')
            else:
                names = name.rsplit('.', 1)
                self.nameOut.set(names[0] + POSTFIX + '.' + names[1])
                self.nameAlbedo.set(name + POSTALBEDO)
                self.nameRLUB.set(name + POSTRLUB + '.txt')
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def pick_output_albedo(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameAlbedo.set(name)

    def pick_output_rlub(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameRLUB.set(name)

    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
        else:
            self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self):
        # variables
##        self.delta = IntVar()
##        self.delta.set(1)
        self.nameIn = StringVar()
        self.nameOut = StringVar()
        self.nameAlbedo = StringVar()
        self.nameRLUB = StringVar()

        self.Nstddev = DoubleVar()
        self.Nstddev.set(conf.get_option('standard-deviations', 3.0, type_=float))

        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        self.choice = StringVar()

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav).grid(row=row, column=1, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=row, column=1, sticky=W)

        row = row + 1

##        # frame 0, Delta
##        self.frame0 = Frame(self)
##        self.frame0.grid(row=row, column=1, sticky=W)
##
##        Entry(self.frame0, width=2, textvariable=self.delta).grid(row=0, column=0, sticky=W)
##        Label(self.frame0, text="Delta (band-shift between ratios)").grid(row=0, column=1, sticky=W)
##
##        row = row + 1

        # input and output file names
        Label(self, text="Input").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameIn, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_input).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self, text="Albedo").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameAlbedo, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output_albedo).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self, text="RLUB").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameRLUB, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output_rlub).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self, text="Output").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameOut, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output).grid(row=row, column=2, sticky=W)

        row = row + 1

        # input parameter N
        self.frame1 = Frame(self)
        self.frame1.grid(row=row, column=1, sticky=E+W)
        self.frame1.columnconfigure(1, weight=1)

        Label(self.frame1, text="Number of stddev's: ").grid(row=row, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.Nstddev, width=5).grid(row=row, column=1, sticky=W)

        row = row + 1

        # choices

        self.frame0 = Frame(self, bd=1, relief=GROOVE)
        self.frame0.grid(row=row, column=1, sticky=N+E+S+W)
        self.frame0.columnconfigure(0, weight=1)
        self.frame0.rowconfigure(0, weight=1)

        Radiobutton(self.frame0, variable=self.choice, value='LOG', text='LOG Residuals').grid(row=0, column=0, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='KWIK', text='KWIK Residuals').grid(row=1, column=0, sticky=W)
        self.choice.set(conf.get_option('choice', "LOG"))

        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, columnspan=3, sticky=E+W)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)

        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=E+W)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=E+W)

        row = row + 1

        # frame 3, text box
        self.frame3 = Frame(self)
        self.frame3.grid(row=row, column=0, columnspan=3, sticky=E+W+N+S)
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.rowconfigure(0, weight=1)

        self.text = Text(self.frame3, width=30, height=10)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        self.scroll=Scrollbar(self.frame3)
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

conf.set_option('choice', app.choice.get())
conf.set_option('standard-deviations', app.Nstddev.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
