#!/usr/bin/python3
#
#     tkSITConvert.py
#
#   Created: WHB 20110712
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
    import sitformat
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Convert SIT format"

class Application(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.grid(sticky=N+E+S+W)
        top=self.winfo_toplevel()

        # allow toplevel to stretch
        top.columnconfigure(0, weight=1)
        top.rowconfigure(2, weight=1)

        self.makeWindow(master)
        self.message(DESCRIPTION)
        self.message(about.about)
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Running, please wait...")
        try:
            if sitformat.is_sit_format(self.nameIn.get()):
                self.message("Looks like a known SIT format...")
            else:
                self.message("""
WARNING: unknown SIT format!
Things may not work as expected.
Proceeding anyway...
""")
            self.message("Writing TIR into 16-bit TIF...")
            sitformat.sit_format_TIR(self.nameIn.get())
            self.message("Writing TIR to JPEG...")
            sitformat.sit_format_TIR_jpeg(self.nameIn.get())
            self.message("Writing VIS to JPEG...")
            sitformat.sit_format_VIS(self.nameIn.get())
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
        
    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
        else:
            self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self, master=None):
        # variables
        self.nameIn = StringVar()

        row = 0

        # frame 1
        self.frame1 = Frame(master)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(1, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        Label(self.frame1, text="Input").grid(row=1, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn, width=30).grid(row=1, column=1, sticky=W+E)
        Button(self.frame1, text='...', command=self.pick_input).grid(row=1, column=2, sticky=W)

        row = row + 1

        # frame 2
        self.frame2 = Frame(master)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)
        self.frame2.rowconfigure(0, weight=1)

        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # frame 3
        self.frame3 = Frame(master)
        self.frame3.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame3.columnconfigure(0, weight=1)
        self.frame3.rowconfigure(0, weight=1)
        
        self.text = Text(self.frame3, width=30, height=10)
        self.text.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        self.scroll=Scrollbar(self.frame3)
        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.text.yview)
        self.scroll.grid(row=0, column=1, sticky=N+S)
        
        # allow column=... and row=... to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)

        row = row + 1

        self.progressBar = ProgressBar(master)
        self.progressBar.grid(row=row, column=0, sticky=W+E)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

##conf.set_option('use-bbl', app.useBBL.get())

root.destroy()
