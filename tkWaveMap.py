#!/usr/bin/python3
#
#     tkWaveMap.py
#
#   Created: WHB 20091208
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
    import wavemap
    import postfix
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_map'

DESCRIPTION = "Wavelength Map"

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
        self.message("Running, please wait...")
        try:
            wavemap.wavemap(self.nameIn.get(), self.nameOut.get(),
                      stretchwav1=self.stretchwav1.get(),
                      stretchwav2=self.stretchwav2.get(),
                      stretchdepth1=self.stretchdepth1.get(),
                      stretchdepth2=self.stretchdepth2.get(),
                        colortable=self.colortable.get(),
                        colorfile=self.nameColorfile.get(),
                        createlegend=self.createLegend.get(),
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
            self.nameOut.set(postfix.insert(name, POSTFIX))
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def pick_colorfile(self):
        self.message("Pick color table file.")
##        name = self.nameIn.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
        name = conf.get_option('color-file', '')
        if name:
            idir = os.path.dirname(name)
            ifile = os.path.basename(name)
        else:
            idir = conf.get_option('input-dir')
            ifile = ''
        name = askopenfilename(title='Open Color Table File',
                                   initialdir=idir,
                                   initialfile=ifile)
        if name:
            conf.set_option('color-file', name)
            self.nameColorfile.set(name)
        
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
        self.nameColorfile = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(0)
        self.useBBL = IntVar()
        self.useBBL.set(0)

        self.stretchwav1 = DoubleVar()
        self.stretchwav1.set(conf.get_option('stretch-wav1', 2100.0))
        self.stretchwav2 = DoubleVar()
        self.stretchwav2.set(conf.get_option('stretch-wav2', 2350.0))
        self.stretchdepth1 = DoubleVar()
        self.stretchdepth1.set(conf.get_option('stretch-depth1', "0.0"))
        self.stretchdepth2 = DoubleVar()
        self.stretchdepth2.set(conf.get_option('stretch-depth2', 0.2))

        self.colortable = StringVar()
        self.colortable.set(conf.get_option('color-table', 'rainbow'))

        self.createLegend = IntVar()
        self.createLegend.set(1)

        row = 0

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
        
        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav, state=DISABLED).grid(row=0, column=0, sticky=W)
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL, state=DISABLED).grid(row=1, column=0, sticky=W)

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

        Label(frame, text="Color table").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameColorfile, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_colorfile).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        row = row + 1


        # options
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Label(frame, text="Color table:").grid(row=0, column=0, sticky=W)
        Radiobutton(frame, variable=self.colortable, value='rainbow', text='rainbow').grid(row=0, column=1, sticky=W)
        Radiobutton(frame, variable=self.colortable, value='steps', text='rainbow+steps').grid(row=0, column=2, sticky=W)
        
        row = row + 1

        # options
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Label(frame, text="Stretch for Wavelength:").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.stretchwav1, width=8).grid(row=0, column=1, sticky=W+E)
        Entry(frame, textvariable=self.stretchwav2, width=8).grid(row=0, column=2, sticky=W+E)
        
##        row = row + 1
##
##        # options
##        frame = Frame(self, bd=2, relief=GROOVE)
##        frame.grid(row=row, column=0, sticky=W+E)

        Label(frame, text="Stretch for Depth:").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.stretchdepth1, width=8).grid(row=1, column=1, sticky=W+E)
        Entry(frame, textvariable=self.stretchdepth2, width=8).grid(row=1, column=2, sticky=W+E)

        row = row + 1

        # options
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Checkbutton(frame, text="Save legend in .png file", variable=self.createLegend).grid(row=0, column=0, sticky=W)

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

conf.set_option('color-table', app.colortable.get())

conf.set_option('stretch-wav1', app.stretchwav1.get())
conf.set_option('stretch-wav2', app.stretchwav2.get())
conf.set_option('stretch-depth1', app.stretchdepth1.get())
conf.set_option('stretch-depth2', app.stretchdepth2.get())

root.destroy()
