#
# tkStretchValueWindow.py
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

from tkinter import *
##from tkinter.filedialog import asksaveasfilename
##
##import os
##import conf

class StretchValueWindow(Toplevel):

    def __init__(self, master=None, title='Stretch Values',
                 command=None, destroy_on_close=False,
                 width=30, height=30):
        Toplevel.__init__(self, master)

        # create the thing, resizable
        self.grid()
        self.title(title)
##        self.transient(master)
        self.master = master
        self.command = command
        self.destroy_on_close = destroy_on_close
        self.width = width
        self.height = height

        # allow toplevel to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # handle the 'X' button
        self.protocol("WM_DELETE_WINDOW", self.close)

        self.makeWindow(master)

    def close(self):
        if self.destroy_on_close:
            self.destroy()
        else:
            self.withdraw()
        if self.command:
            self.command()

    def makeWindow(self, master):
        self.graymin = DoubleVar()
        self.graymax = DoubleVar()
        self.graymax.set(255.0)
        
        self.redmin = DoubleVar()
        self.redmax = DoubleVar()
        self.redmax.set(255.0)
        self.greenmin = DoubleVar()
        self.greenmax = DoubleVar()
        self.greenmax.set(255.0)
        self.bluemin = DoubleVar()
        self.bluemax = DoubleVar()
        self.bluemax.set(255.0)

        row = 0

        # Textbox & scrollbar
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="gray ").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.graymin, width=10).grid(row=0, column=1, sticky=W+E)
        Entry(frame, textvariable=self.graymax, width=10).grid(row=0, column=2, sticky=W+E)

        row = row + 1

        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="red  ").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.redmin, width=10).grid(row=0, column=1, sticky=W+E)
        Entry(frame, textvariable=self.redmax, width=10).grid(row=0, column=2, sticky=W+E)

        Label(frame, text="green").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.greenmin, width=10).grid(row=1, column=1, sticky=W+E)
        Entry(frame, textvariable=self.greenmax, width=10).grid(row=1, column=2, sticky=W+E)

        Label(frame, text="blue ").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self.bluemin, width=10).grid(row=2, column=1, sticky=W+E)
        Entry(frame, textvariable=self.bluemax, width=10).grid(row=2, column=2, sticky=W+E)

##        self.text = Text(frame, width=self.width, height=self.height)
##        self.text.grid(row=0, column=0, sticky=N+E+S+W)
##
##        self.yscroll=Scrollbar(frame, orient=VERTICAL)
##        self.xscroll=Scrollbar(frame, orient=HORIZONTAL)
##
##        # attach text to scrollbar and vice versa
##        self.text.configure(yscrollcommand=self.yscroll.set)
##        self.yscroll.config(command=self.text.yview)
##        self.yscroll.grid(row=0, column=1, sticky=N+S)
##
##        self.text.configure(xscrollcommand=self.xscroll.set)
##        self.xscroll.config(command=self.text.xview)
##        self.xscroll.grid(row=1, column=0, sticky=W+E)

        row = row + 1

        # Run and Exit buttons...
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
##        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        
        Button(frame, text='OK', command=self.close).grid(row=0, column=0, sticky=W+E)

        row = row + 1

##        # allow stretching
##        self.columnconfigure(0, weight=1)
##        self.rowconfigure(0, weight=1)
        
