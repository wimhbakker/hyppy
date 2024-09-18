#!/usr/bin/python3
#
#     tkBandMath.py
#
#   Created: WHB 20111216
#   Modified: WHB 20121210, fixed bug adding files on windows
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

#import glob
import os
import re

from numpy import *

from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import conf
    import envi2
    import envi2.constants
    import about
    import bandmath
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = 'Band Math'

class Application(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)

        # create the frame, resizable
        self.grid(sticky=N+E+S+W)
        top=self.winfo_toplevel()

        # allow toplevel to stretch
        top.columnconfigure(0, weight=1)
        top.rowconfigure(0, weight=1)

        self.makeWindow(master)
        self.message(DESCRIPTION)
        self.message(about.about)

        self.message('Images are numbered i1, i2, i3, ..., i20.')
        self.message('Bands can be indicated by band number (e.g. i1[70]), or by wavelength: (e.g. i2(2.0113)).')
        self.message('''Expressions must follow Python/NumPy syntax, e.g.:
-log(i1(2.6310)/i1(2.5922))/i2[0]
''')
    
    def do_exit(self):
        root.quit()

    def do_run(self, event=None):
        fnames = self.listbox.get(0, END)
        try:
            bandmath.bandmath(fnames, self.nameOut.get(), self.expression.get(),
                              message=self.message,
                              sort_wavelengths=self.sortWav.get(),
                              use_bbl=self.useBBL.get())
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

    def pick_input(self):
        self.message("Pick input files.")
        idir = conf.get_option('input-dir')
        names = askopenfilenames(title='Open Input Files',
                                   initialdir=idir,
                                   initialfile='')

        if names:
            if not isinstance(names, tuple): # for Windows!
                if '{' in names:
                    names = re.findall(r'\{([^\}]*)\}', names)
                else:
                    names = [names]
            conf.set_option('input-dir', os.path.dirname(names[0]))
            for fname in names:
                self.listbox.insert(END, fname)
            self.listbox.see(END)
            
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')

        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def delete(self):
        for i in self.listbox.curselection()[::-1]:
            self.listbox.delete(i)

    def up(self):
        cursel = self.listbox.curselection()
        if '0' in cursel:
            return
        for i in cursel:
            text = self.listbox.get(i)
            self.listbox.delete(i)
            new_i = str(int(i)-1)
            self.listbox.insert(new_i, text)
            self.listbox.selection_set(new_i)

    def down(self):
        cursel = self.listbox.curselection()[::-1]
        if str(self.listbox.size()-1) in cursel:
            return
        for i in cursel:
            text = self.listbox.get(i)
            self.listbox.delete(i)
            new_i = str(int(i)+1)
            self.listbox.insert(new_i, text)
            self.listbox.selection_set(new_i)

    def dummy(self, *args):
        pass

    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
        else:
            self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self, master):
        # variables
        self.nameOut = StringVar()

        self.expression = StringVar()
        self.expression.set(conf.get_option('expression', '', type_=str))

        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 1, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav).grid(row=row, column=0, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=row, column=0, sticky=W)

        row = row + 1

        # ListBox & Scrollbars
        rowlistbox = row
        
        self.frame1 = Frame(self)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(0, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        self.yScroll = Scrollbar(self.frame1, orient=VERTICAL)
        self.yScroll.grid(row=0, column=1, sticky=N+S)
        
        self.xScroll = Scrollbar(self.frame1, orient=HORIZONTAL)
        self.xScroll.grid(row=1, column=0, sticky=E+W)
        
        self.listbox = Listbox(self.frame1, width=40, height=10,
                               selectmode=EXTENDED,
                            xscrollcommand=self.xScroll.set,
                            yscrollcommand=self.yScroll.set)
        self.listbox.bind("<Button>", self.dummy)
        self.listbox.grid(row=0, column=0, sticky=N+S+E+W)
        
        self.xScroll["command"] = self.listbox.xview
        self.yScroll["command"] = self.listbox.yview

        row = row + 1

        # Buttons for managing listbox...
        self.frame3 = Frame(self)
        self.frame3.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.columnconfigure(1, weight=1)
        self.frame3.columnconfigure(2, weight=1)
        self.frame3.columnconfigure(3, weight=1)
        self.frame3.rowconfigure(0, weight=1)
        
        Button(self.frame3, text='Add', command=self.pick_input).grid(row=0, column=0, sticky=W+E)
        Button(self.frame3, text='Delete', command=self.delete).grid(row=0, column=1, sticky=W+E)
        Button(self.frame3, text='Up', command=self.up).grid(row=0, column=2, sticky=W+E)
        Button(self.frame3, text='Down', command=self.down).grid(row=0, column=3, sticky=W+E)

        row = row + 1

        # Label, File Entry, Button...
        self.frame2 = Frame(self, bd=1, relief=GROOVE)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(1, weight=1)
        self.frame2.rowconfigure(0, weight=1)
        
        Label(self.frame2, text="Output:").grid(row=0, column=0, sticky=W)
        Entry(self.frame2, textvariable=self.nameOut).grid(row=0, column=1, sticky=W+E)
        Button(self.frame2, text='Browse', command=self.pick_output).grid(row=0, column=2, sticky=W)

        row = row + 1

        # Label, Expresion...
        self.frame5 = Frame(self, bd=1, relief=GROOVE)
        self.frame5.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame5.columnconfigure(0, weight=1)
        self.frame5.rowconfigure(0, weight=1)
        
        Label(self.frame5, text="Expression:").grid(row=0, column=0, sticky=W)
        e = Entry(self.frame5, textvariable=self.expression)
        e.grid(row=1, column=0, sticky=W+E)
        e.bind('<Key-Return>', self.do_run)

        row = row + 1

        # Run and Exit buttons...
        self.frame4 = Frame(self)
        self.frame4.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame4.columnconfigure(0, weight=1)
        self.frame4.columnconfigure(1, weight=1)
        self.frame4.rowconfigure(0, weight=1)
        
        Button(self.frame4, text='Run', command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame4, text='Exit', command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # frame, text box
        self.frame6 = Frame(self)
        self.frame6.grid(row=row, column=0, columnspan=3, sticky=E+W+N+S)
        self.frame6.columnconfigure(0, weight=1)
        self.frame6.rowconfigure(0, weight=1)

        self.text = Text(self.frame6, width=30, height=10)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        self.scroll=Scrollbar(self.frame6)
        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.text.yview)
        self.scroll.grid(row=0, column=1, sticky=N+S)

        # allow column=1 and row=1 to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('expression', app.expression.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
