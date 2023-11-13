#!/usr/bin/python3
#
#     tkMeteosat.py
#
#   Created: WHB 20091209
#
# Converts a set of Meteosat TIFFs into a single ENVI image
# Converts DN -> Radiance -> Brightness Temperature
# Output in Kelvin
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
    import meteosat
    import conf
    import about
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = 'Convert Meteosat'

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
        self.message("Pattern: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            meteosat.convert_meteosat(self.nameIn.get(), self.nameOut.get(),
                           message=self.message)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input file.")
        name = self.nameIn.get()
        if name:
            idir = os.path.dirname(name)
        else:
            idir = r'D:'
        name = askopenfilename(title='Open Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            self.nameIn.set(name)
            self.nameOut.set(os.path.splitext(name)[0])
        
    def pick_output(self):
        self.message("Pick output file.")
##        name = self.nameOut.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
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
        self.nameIn.set(conf.get_option('pattern', ''))
        self.nameOut = StringVar()

        row = 0

        # frame
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(1, weight=1)
        
        Label(frame, text="Pattern").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn, width=30).grid(row=0, column=1, sticky=W+E)
##        Button(frame, text='...', command=self.pick_input).grid(row=0, column=2, sticky=W)

        Label(frame, text="Output").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=30).grid(row=1, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=1, column=2, sticky=W)

        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, sticky=W+E)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)

        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # text frame
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+S+W+E)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.text = Text(frame, width=30, height=7)
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


root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()
root.destroy()
conf.set_option('pattern', app.nameIn.get())
