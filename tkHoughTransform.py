#!/usr/bin/python3
#
#     tkHoughTransform.py
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

import os
from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

DESCRIPTION = "Hough Transform"

POSTFIX = '_hough'

try:
    import houghtransform
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

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

        self.message("Min. size  : %f" % (self.minsize.get(),))
        self.message("Max. size  : %f" % (self.maxsize.get(),))
        self.message("Step size  : %f" % (self.stepsize.get(),))

        self.message("Threshold  : %f" % (self.threshold.get(),))

        self.message("Running, please wait...")
        try:
            houghtransform.hough_transform(self.nameIn.get(), self.nameOut.get(),
                                   self.minsize.get(),
                                   self.maxsize.get(),
                                   self.stepsize.get(),
                                   self.threshold.get(),
                                   message=self.message,
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

        self.minsize = IntVar()
        self.minsize.set(conf.get_option('minsize', 1, type_=int))
        
        self.maxsize = IntVar()
        self.maxsize.set(conf.get_option('maxsize', 10, type_=int))
        
        self.stepsize = IntVar()
        self.stepsize.set(conf.get_option('stepsize', 1, type_=int))
        
        self.threshold = DoubleVar()
        self.threshold.set(conf.get_option('threshold', 128, type_=float))
        
        row = 0

        # frame 1
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        frow = 0

        Label(frame, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_input).grid(row=frow, column=2, sticky=W)
        frow += 1

        Label(frame, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        row = row + 1

        # frame
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)

        Label(frame, text="Minimum size in pixels:").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.minsize, width=5, justify=RIGHT).grid(row=0, column=1, sticky=W+E)

        Label(frame, text="Maximum size in pixels:").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.maxsize, width=5, justify=RIGHT).grid(row=1, column=1, sticky=W+E)

        Label(frame, text="Step size in pixels:").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self.stepsize, width=5, justify=RIGHT).grid(row=2, column=1, sticky=W+E)

        row = row + 1

        # frame
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)

        Label(frame, text="Threshold for pixel values:").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.threshold, width=5, justify=RIGHT).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)
#        self.frame2.rowconfigure(0, weight=1)
        
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

conf.set_option('minsize', app.minsize.get())
conf.set_option('maxsize', app.maxsize.get())
conf.set_option('stepsize', app.stepsize.get())

conf.set_option('threshold', app.threshold.get())

root.destroy()
