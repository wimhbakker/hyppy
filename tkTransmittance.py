#!/usr/bin/python3
#
#     tkTransmittance.py
#
#   Created: WHB 20110601
#
##
## Copyright (C) 2011 Wim Bakker
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
    import transmittance
    import conf
    import about
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_trans.dat'
DESCRIPTION = "Calculate Transmittance"

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
        self.message("MOLA: " + self.nameMola.get())
        self.message("Out: " + self.nameTrans.get())
        self.message("Running, please wait...")
        try:
            transmittance.transmittance(self.nameIn.get(), self.nameMola.get(),
                    self.nameTrans.get(),
                    sort_wavelengths=self.sortWav.get(),
                    use_bbl=self.useBBL.get(), message=self.message)
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
                self.nameTrans.set(name + POSTFIX)
            else:
                names = name.rsplit('.', 1)
                self.nameTrans.set(names[0] + POSTFIX)
        
    def pick_mola(self):
        self.message("Pick MOLA input file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open MOLA Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameMola.set(name)

    def pick_output(self):
        self.message("Pick transmittance output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Transmittance Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameTrans.set(name)

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
        self.nameMola = StringVar()
        self.nameTrans = StringVar()

        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 1, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

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

        Label(self, text="Input").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameIn, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_input).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self, text="MOLA").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameMola, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_mola).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self, text="Transmittance").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameTrans, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_output).grid(row=row, column=2, sticky=W)

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
