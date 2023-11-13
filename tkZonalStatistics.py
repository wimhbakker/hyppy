#!/usr/bin/python3
#
#     tkZonalStatistics.py
##  Created 20200928 WHB 
##
## Copyright (C) 2020 Wim Bakker
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
from tkinter import ttk

try:
    import envi2
    import zonalstatistics
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Zonal Statistics (as table)"

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
        self.message("Zonal Statistics")
        self.message("Zones:    " + self.zones.get())
        self.message("In:       " + self.nameIn.get())
        self.message("Sort Wav: " + str(self.sortWav.get()))
        self.message("Use BBL:  " + str(self.useBBL.get()))
        self.message("Method:   " + self.method.get())

        self.message("Running, please wait...")
        try:
            zonalstatistics.zonal_statistics(self.zones.get(), self.nameIn.get(),
                                    sort_wavelengths=self.sortWav.get(),
                                    use_bbl=self.useBBL.get(),
                                    method=self.method.get(),
                                    message=self.message,
                                    progress=self.progressBar)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

    def do_exit(self):
        root.quit()

    def pick_zones(self):
        self.message("Pick zones file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Zones File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.zones.set(name)

    def pick_input(self):
        self.message("Pick input file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)

    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
        else:
            self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self):
        # variables
        self.zones = StringVar()
        self.nameIn = StringVar()

        self.method = StringVar()
        self.method.set(conf.get_option('method', 'mean', type_=str))

        self.sortWav = IntVar()
        self.sortWav.set(conf.get_option('sort-wav', 0, type_=int))
        self.useBBL = IntVar()
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        row = 0

        # frame zones
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Label(frame, text="Zones").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.zones, width=25).grid(row=0, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_zones).grid(row=0, column=2, sticky=E)

        row = row + 1

        # frame input
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="Input").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn).grid(row=0, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_input).grid(row=0, column=2, sticky=W)

        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=1, column=1, sticky=W)
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=2, column=1, sticky=W)

        row = row + 1

        # Frame method

        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="Method: ").grid(row=0, column=0, sticky=W)
        self.cb_method = ttk.Combobox(frame, values=sorted(zonalstatistics.methods.keys()),
                                      state="readonly", width=10, textvariable=self.method)
        self.cb_method.grid(row=0, column=1, sticky=W+E)
##        self.cb_method.set('mean')

        row = row + 1

        # frame run
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        
        Button(frame,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(frame,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # frame textbox
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        self.text = Text(frame, width=35, height=10)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        self.scroll=Scrollbar(frame)
        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.text.yview)
        self.scroll.grid(row=0, column=1, sticky=N+S)
        
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

# save the INIs
conf.set_option('sort-wav', app.sortWav.get())
conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('method', app.method.get())

root.destroy()
