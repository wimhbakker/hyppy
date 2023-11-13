#!/usr/bin/python3
#
#     tkDestripe.py
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
    import destripe
    import postfix
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_destr'

DESCRIPTION = "Destriping / Illumination Correction"

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
            if self.speed.get()=='fast':
                destripe.destripe(self.nameIn.get(), self.nameOut.get(),
                      direction=self.direction.get(),
                      mode=self.mode.get(),
                      order=self.order.get(),
                      sort_wavelengths=self.sortWav.get(),
                      use_bbl=self.useBBL.get(), message=self.message,
                      progress=self.progressBar)
            else:
                destripe.bbb_destripe(self.nameIn.get(), self.nameOut.get(),
                      direction=self.direction.get(),
                      mode=self.mode.get(),
                      order=self.order.get(),
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

        self.sortWav = IntVar()
        self.sortWav.set(0)
        self.useBBL = IntVar()
        self.useBBL.set(0)

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        self.direction = StringVar()
        self.direction.set(conf.get_option('direction', 'hor'))
        self.mode = StringVar()
        self.mode.set(conf.get_option('mode', 'sub'))
        self.speed = StringVar()
        self.speed.set(conf.get_option('speed', 'slow'))

        self.order = IntVar()
        order = conf.get_option('order', 0)
        if order:
            self.order.set(order)
        else:
            self.order.set(0)

        row = 0

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
        
        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=0, column=0, sticky=W)
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=1, column=0, sticky=W)

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

        Label(frame, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        row = row + 1

        # options
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Label(frame, text="Direction: ").grid(row=0, column=0, sticky=W)
        Radiobutton(frame, variable=self.direction, value='hor', text='horizontal').grid(row=0, column=1, sticky=W)
        Radiobutton(frame, variable=self.direction, value='ver', text='vertical').grid(row=0, column=2, sticky=W)
        
        Label(frame, text="Correction: ").grid(row=1, column=0, sticky=W)
        Radiobutton(frame, variable=self.mode, value='sub', text='subtract').grid(row=1, column=1, sticky=W)
        Radiobutton(frame, variable=self.mode, value='div', text='divide').grid(row=1, column=2, sticky=W)
        
        Label(frame, text="Speed vs Mem: ").grid(row=2, column=0, sticky=W)
        Radiobutton(frame, variable=self.speed, value='slow', text='band-by-band').grid(row=2, column=1, sticky=W)
        Radiobutton(frame, variable=self.speed, value='fast', text='image at once').grid(row=2, column=2, sticky=W)
        
        row = row + 1

        # options
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Label(frame, text="Illumination Correction").grid(row=0, column=0, sticky=W)
        Label(frame, text="Order of smoothing: ").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.order, width=3).grid(row=1, column=1, sticky=W+E)
        Label(frame, text="(0=destriping)").grid(row=1, column=2, sticky=W)
        
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

conf.set_option('direction', app.direction.get())
conf.set_option('mode', app.mode.get())
conf.set_option('speed', app.speed.get())

conf.set_option('order', app.order.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
