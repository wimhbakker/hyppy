#!/usr/bin/python3
#
#     tkGLT.py
##  Created 20180424 WHB geocorrection using GLT
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
from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import envi2
    import glt
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "GLT geocorrection"

POSTFIX = '_glt'

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
            if self.mode.get()=='forward':
                glt.forward(self.nameIn.get(), self.nameGLT.get(), self.nameOut.get(),
                                    message=self.message,
                                    sort_wavelengths=self.sortWav.get(),
                                    use_bbl=self.useBBL.get(),
                                    progress=self.progressBar)
            else:
                glt.backward(self.nameIn.get(), self.nameGLT.get(), self.nameOut.get(),
                                    message=self.message,
                                    sort_wavelengths=self.sortWav.get(),
                                    use_bbl=self.useBBL.get(),
                                    progress=self.progressBar)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

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

            # generate output name
            if self.nameOut.get() == "":
                if name[-4] != '.':
                    self.nameOut.set(name + POSTFIX)
                else:
                    names = name.rsplit('.', 1)
                    self.nameOut.set(names[0] + POSTFIX + '.' + names[1])
        
    def pick_GLT(self):
        self.message("Pick input GLT file.")
        idir = conf.get_option('glt-dir')
        name = askopenfilename(title='Open Input GLT File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('glt-dir', os.path.dirname(name))
            self.nameGLT.set(name)

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
        self.mode = StringVar()
        self.nameIn = StringVar()
        self.nameOut = StringVar()
        self.nameGLT = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL = IntVar()
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        row = 0

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=0, column=0, sticky=W)
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=1, column=0, sticky=W)

        row = row + 1

        # frame 1
        self.frame1 = Frame(self, bd=2, relief=GROOVE)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(1, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        row = 0
        
        Label(self.frame1, text="Input").grid(row=row, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn).grid(row=row, column=1, sticky=W+E)
        Button(self.frame1, text='...', command=self.pick_input).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self.frame1, text="Input GLT ").grid(row=row, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameGLT).grid(row=row, column=1, sticky=W+E)
        Button(self.frame1, text='...', command=self.pick_GLT).grid(row=row, column=2, sticky=W)

        row = row + 1

        Label(self.frame1, text="Output").grid(row=row, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameOut).grid(row=row, column=1, sticky=W+E)
        Button(self.frame1, text='...', command=self.pick_output).grid(row=row, column=2, sticky=W)

        row = row + 1

        # frame 0
        self.frame0 = Frame(self, bd=2, relief=GROOVE)
        self.frame0.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame0.columnconfigure(2, weight=1)
        self.frame0.rowconfigure(0, weight=1)

        Label(self.frame0, text="Mode:").grid(row=0, column=0, sticky=E)
        Radiobutton(self.frame0, variable=self.mode, value='forward', text='forward').grid(row=0, column=1, sticky=W)
        Radiobutton(self.frame0, variable=self.mode, value='backward', text='backward').grid(row=0, column=2, sticky=W)
        self.mode.set(conf.get_option('mode', "forward"))

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

conf.set_option('mode', app.mode.get())

conf.set_option('sort-wavelength', app.sortWav.get())
conf.set_option('use-bbl', app.useBBL.get())

root.destroy()
