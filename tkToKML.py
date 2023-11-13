#!/usr/bin/python3
#
#     tkToKML.py
#
#   Created: WHB 20100324
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
    import tokml
    import conf
    import about
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = 'Convert to KML'

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
        self.message('''Bands can be wavelength or band number
 (starting at 0).''')
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
#        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            tokml.tokml(self.nameIn.get(),
                        red=self.redBand.get(),
                        green=self.greenBand.get(),
                        blue=self.blueBand.get(),
                        stretch_mode=self.stretch.get(),
                        strip_edges=self.stripEdges.get(),
                        strip_zeros=self.stripZeros.get(),
                        sort_wavelengths=self.sortWav.get(),
                        use_bbl=self.useBBL.get(),
                        target=self.target.get(),
                        message=self.message)
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
#        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        self.redBand = DoubleVar()
##        self.redBand.set(5.09)
        self.redBand.set(conf.get_option('red', 5.09))
        self.greenBand = DoubleVar()
##        self.greenBand.set(1.9)
        self.greenBand.set(conf.get_option('green', 1.9))
        self.blueBand = DoubleVar()
##        self.blueBand.set(0.64)
        self.blueBand.set(conf.get_option('blue', 0.64))

        self.stripEdges = IntVar()
        self.stripEdges.set(conf.get_option('strip-edges', 0))

        self.stripZeros = IntVar()
        self.stripZeros.set(conf.get_option('strip-zeros', 0))

        self.stretch = StringVar()

        self.target = StringVar()

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav).grid(row=row, column=1, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=row, column=1, sticky=W)

        row = row + 1


        Label(self, text="Input").grid(row=row, column=0, sticky=W)
        Entry(self, textvariable=self.nameIn, width=30).grid(row=row, column=1, sticky=W+E)
        Button(self, text='...', command=self.pick_input).grid(row=row, column=2, sticky=W)

        row = row + 1

        # frame with band choice
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, columnspan=3, sticky=W+E)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)
        frame.columnconfigure(5, weight=1)

        Label(frame, text="Red:").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.redBand, width=5).grid(row=0, column=1, sticky=W+E)
        Label(frame, text="Green:").grid(row=0, column=2, sticky=W)
        Entry(frame, textvariable=self.greenBand, width=5).grid(row=0, column=3, sticky=W+E)
        Label(frame, text="Blue:").grid(row=0, column=4, sticky=W)
        Entry(frame, textvariable=self.blueBand, width=5).grid(row=0, column=5, sticky=W+E)
        
        row = row + 1

        # frame with stretch choice
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, columnspan=3, sticky=W+E)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.columnconfigure(3, weight=1)

        Radiobutton(frame, text='No Stretch', value='NO', variable=self.stretch).grid(row=0, column=0, sticky=W+E)
        Radiobutton(frame, text='Min-Max', value='MM', variable=self.stretch).grid(row=0, column=1, sticky=W+E)
        Radiobutton(frame, text='1%-99%', value='1P', variable=self.stretch).grid(row=0, column=2, sticky=W+E)
        Radiobutton(frame, text='2 Std. Dev.', value='SD', variable=self.stretch).grid(row=0, column=3, sticky=W+E)
        self.stretch.set(conf.get_option('stretch', "1P"))

        row = row + 1

        # frame with choice
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, columnspan=3, sticky=W+E)
        frame.columnconfigure(0, weight=1)

        Checkbutton(frame, text="Strip Edges (make any NaN transparent)", variable=self.stripEdges).grid(row=0, column=0, sticky=W+E)
        Checkbutton(frame, text="Strip Zeros (make zeros transparent)", variable=self.stripZeros).grid(row=1, column=0, sticky=W+E)
        
        row = row + 1

        # frame with target
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, columnspan=3, sticky=W+E)
        frame.columnconfigure(0, weight=1)

        Label(frame, text='Target:').grid(row=0, column=0, sticky=W)
        fcol = 1
        for target in tokml.TARGETS:
            Radiobutton(frame, variable=self.target, value=target, text=target).grid(row=0, column=fcol, sticky=W+E)
            frame.columnconfigure(fcol, weight=1)
            fcol = fcol + 1
        self.target.set(conf.get_option('target', tokml.TARGET_MARS))
        
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


root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('red', app.redBand.get())
conf.set_option('green', app.greenBand.get())
conf.set_option('blue', app.blueBand.get())

conf.set_option('stretch', app.stretch.get())
conf.set_option('target', app.target.get())
conf.set_option('strip-edges', app.stripEdges.get())
conf.set_option('strip-zeros', app.stripZeros.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
