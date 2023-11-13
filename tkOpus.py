#!/usr/bin/python
#
#     tkOpus.py
#
#   Created: WHB 20090706
#   Modified: Chris Hecker 20110622
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
import glob
import time
import sys

from tkinter import *
from tkinter.filedialog import *
import opus4
import numpy
import about

from matplotlib import rcParams
rcParams['legend.fontsize'] = 8

from pylab import plot, legend, save, load, title, xlabel, ylabel, ion, close, figure
ion()

import envi2

OPUS_DATATYPES = ['Refl', 'AB', 'TR', 'IgSm', 'PhSm', 'ScSm', 'IgRf', 'ScRf']

#POSTFIX = '_refl'

DESCRIPTION = "Opus Converter"

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

        if ':' in sys.executable:
            self.message("""
WARNING: you seem to be on Windows.
Due to a bug in Python and/or Tk you may
experience problems when using directories
and/or files that contain spaces in the names.
Copy your files to a directory with no
spaces in the name and/or rename your files.
We apologize for the inconvenience!""")

    def set_textin(self):
        if hasattr(self, 'fnames') and self.fnames:
            if len(self.fnames)==1:
                self.nameIn.set(str(self.fnames[0]))
            else:
                self.nameIn.set(str(self.fnames))

    def to_speclib(self, fname, alldata, x, dxu, spectra_names):
##        bands = 1                   # always 1
##        lines = len(alldata)        # number of spectra
##        samples = len(alldata[0])   # number of bands, THANK YOU ENVI!

        samples = 1                   # always 1
        lines = len(alldata)        # number of spectra
        bands = len(alldata[0])   # number of bands, bands and samples are twisted in the ENVI header!
        wavelength = x

        if dxu == 'WN':
            wavelength_units = 'Wavenumber'
            if self.enforceMicrons.get():
                wavelength = 10000.0 / wavelength
                wavelength_units = 'Micrometers'
        elif dxu == 'MI':
            wavelength_units = 'Micrometers'
        else:
            wavelength_units = 'Unknown'

        description = [time.strftime('tkOpus.py [%a %b %d %H:%M:%S %Y]')]
        if self.descr.get():
            description.insert(0, self.descr.get())
        
        sl = envi2.Speclib(fname, 'w', decsription=description,
                           bands=bands, lines=lines, samples=samples,
                           spectra_names=spectra_names,
                           wavelength_units=wavelength_units,
                           wavelength=wavelength, data_type='f',
                           byte_order=0)

        for i in range(len(alldata)):
            sl[i] = alldata[i]

        sl.flush()
        del sl

    def to_textfile(self, fname, ext, x, y):
        name = fname + '.' + ext
        if not os.path.exists(name):
            f = open(name, 'w')
            for i in range(len(x)):
                f.write('%f %f\n' % (x[i], y[i]))
            f.close()

    def do_all(self, fnames):
        alldata = []
        spectra_names = []
        x = None
        header = None
        
        for fname in sorted(fnames):
            self.message('\n########## OPUS File: %s ##########' % (fname,))
            try:
                dataset, header = opus4.get_opus_data(fname, self.choice.get(), message=self.message)
            except ValueError as errtext:
                self.message('Error: %s' % (errtext,))
                continue
            if not dataset or not header:
                self.message('Dataset %s not found in file' % (self.choice.get()))
                return None, None, None, None
            data = numpy.array(dataset) * header.yscale()
            spectra_name = os.path.basename(fname)
            alldata.append(data)
            spectra_names.append(spectra_name)

            x = header.xvalues()

            if self.makePlot.get():
                figure(1)
                plot(x, data, label=spectra_name)

            if self.toText.get():
                self.to_textfile(fname, self.choice.get(), x, data)

        if self.makePlot.get():
            figure(1)
            title(self.choice.get())
            legend()

        return alldata, x, getattr(header, 'DXU', None), spectra_names

    def do_average(self, fnames):
        alldata = []
        spectra_names = []
        x = None
        header = None
        
        bases = set()
        for fname in fnames:
            bases.add(os.path.splitext(fname)[0])

        for base in bases:
            fnames = glob.glob(base+'.[0-9]') + glob.glob(base+'.[0-9][0-9]') + glob.glob(base+'.[0-9][0-9][0-9]')
            if not fnames:
                continue
            
            n = 0
            sum_x = 0
            sum_xx = 0

            for fname in sorted(fnames):
                self.message('\n########## OPUS File: %s ##########' % (fname,))
                try:
                    dataset, header = opus4.get_opus_data(fname, self.choice.get(), message=self.message)
                except ValueError as errtext:
                    self.message('Error: %s' % (errtext,))
                    continue
                if not dataset or not header:
                    self.message('Dataset %s not found in file' % (self.choice.get()))
                    return None, None, None, None
                data = numpy.array(dataset) * header.yscale()
                n = n + 1
                sum_x = sum_x + data
                sum_xx = sum_xx + data*data

            x = header.xvalues()
            s = numpy.sqrt(n * sum_xx - sum_x * sum_x) / n
            m = sum_x / n
            spectra_name = os.path.basename(base+'.*')

            if self.makePlot.get():
                figure(1)
                plot(x, m, label=spectra_name)

            if self.plotStdev.get():
                figure(2)
                plot(x, s, label=spectra_name)

            if self.toText.get():
                self.to_textfile(base, self.choice.get(), x, data)

            # modified by CH
            if self.makePlot.get():
                alldata.append(m)
                spectra_names.append(spectra_name)

            # modified by CH
            if self.plotStdev.get():
                alldata.append(s)
                spectra_name = (spectra_name +'_stdev')
                spectra_names.append(spectra_name)

        if self.makePlot.get():
            figure(1)
            title('Average ' + self.choice.get())
            legend()

        if self.plotStdev.get():
            figure(2)
            title('Stdev ' + self.choice.get())
            legend()

        return alldata, x, getattr(header, 'DXU', None), spectra_names

    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")

        try:
            if hasattr(self, 'fnames') and self.fnames:
                fnames = self.fnames
            else:
                fnames = glob.glob(self.nameIn.get())
            fnames = sorted(fnames)  # NEW 2013
        
            if self.average.get():
                alldata, x, dxu, spectra_names = self.do_average(fnames)
            else:
                alldata, x, dxu, spectra_names = self.do_all(fnames)

            if self.nameOut.get() and alldata:
                self.message('Writing spectral library: %s' % (self.nameOut.get(),))
                self.to_speclib(self.nameOut.get(), alldata, x, dxu, spectra_names)
        
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

        self.message("Completed!")

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input files.")
        fnames = askopenfilenames(title='Open Input File',
                                   initialdir='.',
                                   initialfile='')
        if fnames:
            if not isinstance(fnames, tuple):
                self.fnames = fnames.split()
            else:
                self.fnames = fnames
            self.set_textin()
        
    def pick_output(self):
        self.message("Pick output file.")
        self.nameOut.set(asksaveasfilename(title='Open Output File',
                                   initialdir=r'.',
                                   initialfile=''))

    def message(self, s):
        if type(s) != str:
            s = str(s)
        if len(s)==1:
            self.text.insert(END, s)
        else:
            self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def keypress(self, ev):
        # 'Reset fnames'
        if ev.char in ['\r', '\n']:
            self.do_run()
        elif hasattr(self, 'fnames'):
            self.fnames = None

    def save_logfile(self):
        self.message("Pick Logfile.")
        fname = asksaveasfilename(title='Open Output Logile',
                                   initialdir=r'.',
                                   initialfile='')
        if fname:
            f = open(fname, 'w')
            f.write(self.text.get('1.0', END))
            f.close()
            self.message('Logfile saved.')

    def makeWindow(self):
        # variables
        self.choice = StringVar()
        self.nameIn = StringVar()
        self.nameOut = StringVar()
        self.average = IntVar()
        self.average.set(0)
        self.makePlot = IntVar()
        self.makePlot.set(0)
        self.plotStdev = IntVar()
        self.plotStdev.set(0)
        self.toText = IntVar()
        self.toText.set(0)
        self.enforceMicrons = IntVar()
        self.enforceMicrons.set(0)
        self.descr = StringVar()

        row = 0

        bigframe = Frame(self, bd=2, relief=GROOVE)
        bigframe.grid(row=row, column=0, sticky=W+E)
        bigframe.columnconfigure(0, weight=1)

        brow = 0

        # input and output file names
        frame = Frame(bigframe)
        frame.grid(row=brow, column=0, sticky=W+E)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="Input:").grid(row=0, column=0, sticky=W)
        self.textIn = Entry(frame, textvariable=self.nameIn, width=40)
        self.textIn.grid(row=0, column=1, sticky=W+E)
        self.textIn.bind('<KeyPress>', self.keypress)
        Button(frame, text='...', command=self.pick_input).grid(row=0, column=2, sticky=W)

        brow = brow + 1

        # Radio buttons for OPUS data types
        frame = Frame(bigframe)
        frame.grid(row=brow, column=0, sticky=W+E)

        Label(frame, text="Dataset:").grid(row=0, column=0, sticky=W)
        col = 1
        for opus_datatype in OPUS_DATATYPES:
            frame.columnconfigure(col, weight=1)
            Radiobutton(frame, variable=self.choice, value=opus_datatype, text=opus_datatype).grid(row=0, column=col, sticky=W+E)
            col = col + 1
        self.choice.set(OPUS_DATATYPES[0])

        row = row + 1

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)

        frow = 0

        Label(frame, text="Options:").grid(row=frow, column=0, sticky=W)
        
        Checkbutton(frame, text="Average Spectra by Basename", variable=self.average).grid(row=frow, column=1, sticky=W)
        
        frow = frow + 1

        # checkbutton
        Checkbutton(frame, text="Plot Spectra", variable=self.makePlot).grid(row=frow, column=1, sticky=W)
        
        frow = frow + 1

        # checkbutton
        Checkbutton(frame, text="Plot Stdev of Spectra", variable=self.plotStdev).grid(row=frow, column=1, sticky=W)
        
        frow = frow + 1

        # checkbutton
        Checkbutton(frame, text="Write Data to Text File", variable=self.toText).grid(row=frow, column=1, sticky=W)
        
        frow = frow + 1

        # checkbutton
        
        row = row + 1

        # output spectral library
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.columnconfigure(1, weight=1)

        frow = 0

        Label(frame, text="Speclib:").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut, width=40).grid(row=frow, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        # description spectral library
        Label(frame, text="Descr:").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.descr, width=40).grid(row=frow, column=1, sticky=W+E)

        frow = frow + 1
        
        Checkbutton(frame, text="Enforce Micrometers in Speclib", variable=self.enforceMicrons).grid(row=frow, column=1, sticky=W)

        row = row + 1

        # frame 2
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        
        Button(frame,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(frame,text="Save Logfile",command=self.save_logfile).grid(row=0, column=1, sticky=W+E)
        Button(frame,text="Exit",command=self.do_exit).grid(row=0, column=2, sticky=W+E)

        row = row + 1

        # frame with textbox
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.text = Text(frame, width=80, height=25)
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

close('all')
