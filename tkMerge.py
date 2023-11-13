#!/usr/bin/python3
#
#     tkMerge.py
#
#   Created: WHB 20091028
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

#import glob
import os
import re

from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import envi2
    import envi2.constants
    import about
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = 'Merge files'

curdir = os.path.expanduser('~')

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
    
    def do_exit(self):
        root.quit()

    def do_run(self):
        try:
            fnames = self.listbox.get(0, END)
            biglist = []
            hdr = None
            for fname in fnames:
                im = envi2.Open(fname,
                                sort_wavelengths=self.sortWav.get(),
                                use_bbl=self.useBBL.get())

                if hdr == None:      # copy header info from first image...
                    hdr = im.header.copy()
                    
                for band in range(im.bands):
                    wl = 0
                    if hasattr(im, 'wavelength'):
                        wl = im.wavelength[band]
                    if hasattr(im, 'band_names'):
                        bn = im.band_names[band]
                    else:
                        bn = "Band %d" % (band,)
                    biglist.append((wl, fname, band, bn))

                del im

            if self.sortWav.get():
                biglist.sort()
    ##        print biglist

            bands = len(biglist)

            wavelength = [x[0] for x in biglist]
            if wavelength[0] == 0:
                wavelength = None
                
            band_names = [x[3] for x in biglist]        

            imout = envi2.New(self.nameOut.get(),
                              hdr=hdr,
                              bands=bands,
                              wavelength=wavelength,
                              bbl=None,
                              band_names=band_names,
                              fwhm=None,
                              interleave='bsq')

            i = 0
            for wav, fname, band, bn in biglist:
    #            print wav, fname, band
                im = envi2.Open(fname,
                                sort_wavelengths=self.sortWav.get(),
                                use_bbl=self.useBBL.get())
    ##            if im.bands==1:
    ##                imout[i] = im[...]
    ##            else:
    ##                imout[i] = im[band]
                imout[i] = im[band]
                i = i+1
                del im

            del imout
        except Exception as err:
            tkinter.messagebox.showerror(title='Exception', message=str(err))
            raise

    def pick_input(self):
        global curdir
        self.message("Pick input files.")
        names = askopenfilenames(title='Open Input Files',
                                   initialdir=curdir,
                                   initialfile='')

        if names:
            if not isinstance(names, tuple): # for Windows!
                if '{' in names:
                    names = re.findall('\{([^\}]*)\}', names)
                else:
                    names = [names]
            curdir = os.path.dirname(names[0])
            for fname in names:
                self.listbox.insert(END, fname)
            self.listbox.see(END)
            
    def pick_output(self):
        global curdir
        self.message("Pick output file.")
        self.nameOut.set(asksaveasfilename(title='Open Output File',
                                   initialdir=curdir,
                                   initialfile=''))

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
        pass

    def makeWindow(self, master):
        # variables
        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.sortWav.set(1)
        self.useBBL = IntVar()
        self.useBBL.set(1)

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
        
        self.listbox = Listbox(self.frame1, width=40, height=30,
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
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(1, weight=1)
        self.frame2.rowconfigure(0, weight=1)
        
        Label(self.frame2, text="Output:").grid(row=0, column=0, sticky=W)
        Entry(self.frame2, textvariable=self.nameOut).grid(row=0, column=1, sticky=W+E)
        Button(self.frame2, text='Browse', command=self.pick_output).grid(row=0, column=2, sticky=W)

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

        # allow column=1 and row=1 to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(rowlistbox, weight=1)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()
root.destroy()
