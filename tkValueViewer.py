#
# tkValueViewer.py
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
from tkinter.filedialog import asksaveasfilename

import os
import conf

class ValueViewer(Toplevel):

    def __init__(self, master=None, title='View Values',
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

    def clear(self):
        self.text.delete('1.0', END)

    def view(self, thing):
        self.text.delete(0, END)
        self.text.insert(0, thing)

    def add(self, thing):
        self.text.insert(END, thing)

    def save(self):
        idir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File', initialdir=idir)
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            f = open(name, 'w')
            f.write(self.text.get('1.0', END))
            f.close()

    def close(self):
        if self.command:
            self.command(self.text.get('1.0', END))
        if self.destroy_on_close:
            self.destroy()
        else:
            self.withdraw()

    def makeWindow(self, master):
        row = 0

        # Textbox & scrollbar
        rowtext = row
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        self.text = Text(frame, width=self.width, height=self.height)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        self.yscroll=Scrollbar(frame, orient=VERTICAL)
        self.xscroll=Scrollbar(frame, orient=HORIZONTAL)

        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.yscroll.set)
        self.yscroll.config(command=self.text.yview)
        self.yscroll.grid(row=0, column=1, sticky=N+S)

        self.text.configure(xscrollcommand=self.xscroll.set)
        self.xscroll.config(command=self.text.xview)
        self.xscroll.grid(row=1, column=0, sticky=W+E)

        row = row + 1

        # Run and Exit buttons...
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        
        Button(frame, text='Save', command=self.save).grid(row=0, column=0, sticky=W+E)
        Button(frame, text='Close', command=self.close).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # allow stretching
        self.columnconfigure(0, weight=1)
        self.rowconfigure(rowtext, weight=1)
        
