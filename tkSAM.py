#!/usr/bin/python3
#
#     tkSAM.py
#
#   Created: WHB 20091113
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
    import envi2
    import sam
    import tkSelector
    import ascspeclib
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Spectral Mapper"

POSTFIX = '_map'

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

        self.message("Generating rule images...")
        try:
            sam.sam(self.nameIn.get(), self.nameOut.get(),
                speclib=self.nameSpeclib.get(),
                mode=self.choice.get(),
                spec_selection=getattr(self, 'spec_selection', None),
                band_selection=getattr(self, 'band_selection', None),
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
        self.clear_band_selection()
        self.message("Pick input file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Input File',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)
            # generate output names
            if self.nameOut.get() == "":
                if name[-4] != '.':
                    self.nameOut.set(name + POSTFIX)
                else:
                    names = name.rsplit('.', 1)
                    self.nameOut.set(names[0] + POSTFIX + '.' + names[1])
        
    def pick_speclib(self):
        self.message("Pick input Speclib.")
        idir = conf.get_option('speclib-dir', conf.get_option('input-dir'))
        name = askopenfilename(title='Open Spectral Library',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            self.clear_spec_selection()
            conf.set_option('speclib-dir', os.path.dirname(name))
            self.nameSpeclib.set(name)

    def pick_speclib_dir(self):
        self.message("Pick input Ascii Speclib.")
        idir = conf.get_option('speclib-dir', conf.get_option('input-dir'))
        name = askdirectory(title='Open Directory',
                                   initialdir=idir)
        if name:
            self.clear_spec_selection()
            conf.set_option('speclib-dir', os.path.dirname(name))
            self.nameSpeclib.set(name)

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

    def set_spec_selection(self, spec_selection):
        self.spec_selection = spec_selection

    def clear_spec_selection(self):
        if hasattr(self, 'spec_selection'):
            del self.spec_selection

    def do_spec_select(self):
##        if hasattr(self, 'spec_selector'):
##            self.spec_selector.deiconify()
##        else:
        speclib = self.nameSpeclib.get()
        if speclib:
            if os.path.isdir(speclib):
                sl = ascspeclib.AscSpeclib(speclib)
            else:
                sl = envi2.Speclib(speclib)
            tkSelector.Selector(sl.names(),
                                master=self, title='Spectra Selector',
                                command=self.set_spec_selection)
            del sl

    def set_band_selection(self, band_selection):
        self.band_selection = band_selection

    def clear_band_selection(self):
        if hasattr(self, 'band_selection'):
            del self.band_selection

    def do_band_select(self):
##        if hasattr(self, 'band_selector'):
##            self.band_selector.deiconify()
##        else:
        nameIn = self.nameIn.get()
        if nameIn:
            im = envi2.Open(nameIn,
                        sort_wavelengths=self.sortWav.get(),
                        use_bbl=self.useBBL.get())

            tkSelector.Selector(im.wavelength,
                                master=self, title='Bands Selector',
                                command=self.set_band_selection)
            del im

    def makeWindow(self):
        # variables
        self.choice = StringVar()
        
        self.nameIn = StringVar()
        self.nameOut = StringVar()
        self.nameSpeclib = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(1)
        self.useBBL = IntVar()

        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav, state=DISABLED).grid(row=row, column=0, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL, command=self.clear_band_selection).grid(row=row, column=0, sticky=W)

        row = row + 1

        # frame 1
        self.frame1 = Frame(self)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(1, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        frow = 0

        Label(self.frame1, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn).grid(row=frow, column=1, sticky=W+E)
        Button(self.frame1, text='Browse', command=self.pick_input).grid(row=frow, column=2, sticky=W+E)

        frow = frow + 1

        Label(self.frame1, text="Speclib").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameSpeclib).grid(row=frow, column=1, sticky=W+E)

        frame = Frame(self.frame1)
        frame.grid(row=frow, column=2, sticky=W+E)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        
        Button(frame, text='Envi', command=self.pick_speclib).grid(row=0, column=0, sticky=W+E)
        Button(frame, text='Ascii', command=self.pick_speclib_dir).grid(row=0, column=1, sticky=W+E)

        frow = frow + 1

        Label(self.frame1, text="Output").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameOut).grid(row=frow, column=1, sticky=W+E)
        Button(self.frame1, text='Browse', command=self.pick_output).grid(row=frow, column=2, sticky=W+E)

        row = row + 1

        # frame 0, offer processing choices
        self.frame0 = Frame(self)
        self.frame0.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame0.columnconfigure(2, weight=1)
        self.frame0.rowconfigure(0, weight=1)

        Label(self.frame0, text="Method:").grid(row=0, column=0, sticky=E)
        Radiobutton(self.frame0, variable=self.choice, value='SAM', text='Spectral Angle Mapper').grid(row=0, column=1, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='SID', text='Spectral Information Divergence').grid(row=1, column=1, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='BC', text='Bray-Curtis Distance').grid(row=2, column=1, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='ED', text='Euclidean Distance').grid(row=3, column=1, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='ID', text='Intensity Difference').grid(row=4, column=1, sticky=W)
        self.choice.set(conf.get_option('method', "SAM"))

        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)
        self.frame2.rowconfigure(0, weight=1)
        
        Button(self.frame2,text="Select Spectra",command=self.do_spec_select).grid(row=0, column=0, columnspan=2, sticky=W+E)
        Button(self.frame2,text="Select Bands",command=self.do_band_select).grid(row=1, column=0, columnspan=2, sticky=W+E)
        Button(self.frame2,text="Run",command=self.do_run).grid(row=2, column=0, sticky=W+E)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=2, column=1, sticky=W+E)

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

conf.set_option('method', app.choice.get())

conf.set_option('use-bbl', app.useBBL.get())

root.destroy()
