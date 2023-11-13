#!/usr/bin/python3
#
#     tkSummaryProducts.py
#
#   Based on Pelkey et al.: Crism multispectral summary products
#
#   Created: WHB 20090506
##  Modified: WHB 20160317, added Viviano-Beck, 2014, summary products
##
##
## Copyright (C) 2016 Wim Bakker
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
    import envi2
    import summary_products
    import viviano_beck
    import otherindices
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_sp'
LOGEXT = '.log'

VIVIANO = 'Viviano-Beck'
PELKEY = 'Pelkey'
OTHER = 'Other'
            
def get_wavelength_units(name):
    '''Figure out wavelength units of input image...'''
    im = envi2.Open(name)

    result = 'Micrometers'

    if hasattr(im.header, 'wavelength_units') and im.header.wavelength_units!='Unknown':
        result = im.header.wavelength_units
    else:
        if im.wavelength[-1] > 100:
             result = 'Nanometers'
    del im

    return result

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
        self.message("Crism Multispectral Summary Products.")
        self.message(about.about)
    
    def do_run(self) :
        self.logFile = self.nameOut.get() + LOGEXT
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            if self.sumProducts.get() == VIVIANO:
                viviano_beck.products(self.nameIn.get(),
                                  self.nameOut.get(), 
                                  sort_wavelengths=self.sortWav.get(),
                                  use_bbl=self.useBBL.get(),
                                  message=self.message,
                                  wavelength_units=self.wavUnits.get(),
                                  progress=self.progressBar)
            elif self.sumProducts.get() == PELKEY:
                summary_products.products(self.nameIn.get(),
                                  self.nameHull.get(),
                                  self.nameOut.get(), 
                                  sort_wavelengths=self.sortWav.get(),
                                  use_bbl=self.useBBL.get(),
                                  message=self.message,
                                  wavelength_units=self.wavUnits.get(),
                                  progress=self.progressBar)
            else:
                otherindices.products(self.nameIn.get(),
                                  self.nameOut.get(), 
                                  sort_wavelengths=self.sortWav.get(),
                                  use_bbl=self.useBBL.get(),
                                  message=self.message,
                                  wavelength_units=self.wavUnits.get(),
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

            self.wavUnits.set(get_wavelength_units(name))

            # generate output name
#            if self.nameOut.get() == "":
            if name[-4] != '.':
                self.nameOut.set(name + POSTFIX)
            else:
                names = name.rsplit('.', 1)
                self.nameOut.set(names[0] + POSTFIX + '.' + names[1])

    def pick_continuum(self):
        self.message("Pick continuum removed image.")
##        name = self.nameIn.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
        idir = conf.get_option('hull-dir', conf.get_option('input-dir'))
        name = askopenfilename(title='Open Continuum Removed',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('hull-dir', os.path.dirname(name))
            self.nameHull.set(name)
        
    def pick_output(self):
        self.message("Pick output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.nameOut.set(name)

    def toLogFile(self, s):
        if hasattr(self, 'logFile'):
            f = open(self.logFile, 'a')
            f.write(s)
            f.close()

    def message(self, s):
        if len(s)==1:
            self.text.insert(END, s)
            self.toLogFile(s)
        else:
            self.text.insert(END, s + '\n')
            self.toLogFile(s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self):
        # variables
        self.wavUnits = StringVar()
        self.sumProducts = StringVar()
        self.nameIn = StringVar()
        self.nameHull = StringVar()
        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        row = 0

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=0, column=0, sticky=W)
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=1, column=0, sticky=W)

        row = row + 1

##        # frame 0
##        self.frame0 = Frame(self)
##        self.frame0.grid(row=row, column=1, sticky=W)
##
##        Radiobutton(self.frame0, variable=self.choice, value='divide', text='Divide').grid(row=0, column=0, sticky=W)
##        Radiobutton(self.frame0, variable=self.choice, value='subtract', text='Subtract').grid(row=0, column=1, sticky=W)
##        self.choice.set("divide")
##
##        row = row + 1

        # input and output files
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        frow = 0

        Label(frame, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_input).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        # continuum removed
        Label(frame, text="Continuum").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameHull, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_continuum).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(frame, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=30).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        row = row + 1

        # frame3
        self.frame3 = Frame(self, bd=2, relief=GROOVE)
        self.frame3.grid(row=row, column=0, columnspan=3, sticky=W+E)
        self.frame3.columnconfigure(1, weight=1)

        Label(self.frame3, text="Input wavelength units:").grid(row=0, column=0, sticky=W)
        Radiobutton(self.frame3, variable=self.wavUnits, value='Micrometers', text='Micrometers').grid(row=0, column=1, sticky=W)
        Radiobutton(self.frame3, variable=self.wavUnits, value='Nanometers', text='Nanometers').grid(row=1, column=1, sticky=W)
        self.wavUnits.set(conf.get_option('units', "Micrometers"))

        row = row + 1

        # frame4
        self.frame4 = Frame(self, bd=2, relief=GROOVE)
        self.frame4.grid(row=row, column=0, columnspan=3, sticky=W+E)
        self.frame4.columnconfigure(1, weight=1)

        Label(self.frame4, text="Summary Products:").grid(row=0, column=0, sticky=W)
        Radiobutton(self.frame4, variable=self.sumProducts, value=VIVIANO, text=VIVIANO).grid(row=0, column=1, sticky=W)
        Radiobutton(self.frame4, variable=self.sumProducts, value=PELKEY, text=PELKEY).grid(row=1, column=1, sticky=W)
        Radiobutton(self.frame4, variable=self.sumProducts, value=OTHER, text=OTHER).grid(row=2, column=1, sticky=W)
        self.sumProducts.set(conf.get_option('products', VIVIANO))

        row = row + 1

        # frame 2
        self.frame2 = Frame(self, bd=2, relief=GROOVE)
        self.frame2.grid(row=row, column=0, columnspan=3, sticky=W+E)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)

        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # Text box
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

        row = row + 1

        self.progressBar = ProgressBar(self)
        self.progressBar.grid(row=row, column=0, columnspan=3, sticky=W+E)

root = Tk()
app = Application(root)
root.title("Summary Products")
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('units', app.wavUnits.get())
conf.set_option('products', app.sumProducts.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
