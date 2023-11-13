#!/usr/bin/python3
#
#     tkFilter.py
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

DESCRIPTION = "Linear Filter"

POSTFIX = '_filt'

try:
    import convolve
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

KERNEL = conf.get_option('kernel', [[1 for i in range(3)] for j in range(3)],
                         type_=list)

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
        self.message("""Note: NaN's not taken into account!""")
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())

        kernel = ''
        self.message("Kernel:")
        for j in range(3):
            m = ''
            for i in range(3):
                m = m + ("%7.2f" % (self.kernel[j][i].get(),))
                kernel = kernel + ' ' + str(self.kernel[j][i].get())
            self.message(m)
        kernel = kernel.strip()

        self.message("Bias  : %f" % (self.bias.get(),))
        self.message("Offset: %f" % (self.offset.get(),))

        self.message("Running, please wait...")
        try:
            convolve.fast_convolve(self.nameIn.get(), self.nameOut.get(),
                                   kernel=kernel,
                                   bias=self.bias.get(),
                                   offset=self.offset.get(),
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
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))

        self.kernel = [[DoubleVar() for i in range(3)] for j in range(3)]

        self.bias = DoubleVar()
        self.bias.set(conf.get_option('bias', 1.0, type_=float))
        
        self.offset = DoubleVar()
        self.offset.set(conf.get_option('offset', 0.0, type_=float))
        
        row = 0

        # frame 1
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        frow = 0

        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=frow, column=1, sticky=W)
        frow += 1
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=frow, column=1, sticky=W)
        frow += 1

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
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="Kernel:").grid(row=0, column=0, sticky=W)
        for j in range(3):
            for i in range(3):
                self.kernel[j][i].set(KERNEL[j][i])
                Entry(frame, textvariable=self.kernel[j][i], width=5, justify=RIGHT).grid(row=j+1, column=i, sticky=W+E)

        row = row + 1

        # frame
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)

        Label(frame, text="Bias:").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.bias, width=5, justify=RIGHT).grid(row=0, column=1, sticky=W+E)

        Label(frame, text="Offset:").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.offset, width=5, justify=RIGHT).grid(row=1, column=1, sticky=W+E)

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

KERNEL = [[app.kernel[j][i].get() for i in range(3)] for j in range(3)]
conf.set_option('kernel', KERNEL)

conf.set_option('bias', app.bias.get())
conf.set_option('offset', app.offset.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
