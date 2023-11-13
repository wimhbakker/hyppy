## tkSelector.py
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

class Selector(Toplevel):

    def __init__(self, selection=None, master=None, title='Selector',
                 command=None, single=False, width=40, height=30,
                 returnmode='index'):
        Toplevel.__init__(self, master)
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        # create the thing, resizable
        self.grid()
        self.title(title)
        self.transient(master)
        self.selection = selection
        self.master = master
        self.command = command
        self.single = single
        self.width = width
        self.height = height
        self.returnmode = returnmode

        # allow toplevel to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.makeWindow(master)

        for item in selection:
            self.add(item)

        if single:
            self.selection_first()
        else:
            self.selection_all()
    
##    def do_exit(self):
##        root.quit()

    def add(self, thing):
        self.listbox.insert(END, thing)

    def selection_clear(self):
        self.listbox.selection_clear(0, END)

    def selection_all(self):
        self.listbox.selection_set(0, END)

    def selection_first(self):
        self.listbox.selection_set(0)

##    def dummy(self, *args):
##        pass

    def close(self):
##        self.master.selection = [int(i) for i in self.listbox.curselection()]
        if self.command:
            if self.returnmode=='index':
                result = [int(i) for i in self.listbox.curselection()]
            else:
                result = [self.selection[int(i)] for i in self.listbox.curselection()]
            if self.single:
                if result:
                    result = result[0]
                else:
                    result = None
            self.command(result)

##        self.withdraw()
        self.destroy()

##    def message(self, s):
##        pass

    def makeWindow(self, master):
        # variables

        if self.single:
            selectmode = SINGLE
        else:
            selectmode = EXTENDED

        row = 0

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
        
        self.listbox = Listbox(self.frame1, width=self.width, height=self.height,
                               selectmode=selectmode,
                            xscrollcommand=self.xScroll.set,
                            yscrollcommand=self.yScroll.set)
##        self.listbox.bind("<Button>", self.dummy)
        self.listbox.grid(row=0, column=0, sticky=N+S+E+W)
        
        self.xScroll["command"] = self.listbox.xview
        self.yScroll["command"] = self.listbox.yview

        row = row + 1

        # Buttons for managing listbox...
        self.frame3 = Frame(self)
        self.frame3.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.columnconfigure(1, weight=1)
        self.frame3.rowconfigure(0, weight=1)

        if self.single:
            state = DISABLED
        else:
            state = NORMAL
        Button(self.frame3, text='Select All', command=self.selection_all, state=state).grid(row=0, column=0, sticky=W+E)
        Button(self.frame3, text='Clear All', command=self.selection_clear).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # Run and Exit buttons...
        self.frame4 = Frame(self)
        self.frame4.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame4.columnconfigure(0, weight=1)
        self.frame4.rowconfigure(0, weight=1)
        
        Button(self.frame4, text='OK', command=self.close).grid(row=0, column=0, sticky=W+E)

        row = row + 1

        # allow column=1 and row=1 to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(rowlistbox, weight=1)
        
