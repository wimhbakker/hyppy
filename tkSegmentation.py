#!/usr/bin/python3
#
#     tkSegmentation.py
#
#   Hyperspectral Split & Merge 
#
#   Created: WHB 20090615
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
    import segmentation
    import postfix
    import conf
    import about
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Hyperspectral Split & Merge"

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
#        self.logFile = self.nameOut.get() + LOGEXT
        self.message("In: " + self.nameIn.get())
##        self.message("Out: " + self.nameOut.get())
##        self.message("Thermal Out: " + self.thermOut.get())
##        self.message("Running, please wait...")
        try:
            segmentation.segmentation(self.edgeMap.get(),
                                  self.nameIn.get(),
                                  filethres=self.fileThres.get(),
                                  filesalt=self.fileSalt.get(),
                                  filequad=self.fileQuad.get(),
                                  fileclust=self.fileClust.get(),
                      sort_wavelengths=self.sortWav.get(),
                      use_bbl=self.useBBL.get(),
                      split_level=self.splitLevel.get(),
                      merge_level=self.mergeLevel.get(),
                      distance_measure=self.choice.get(),
                      message=self.message)
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
            self.set_output_name(postfix.insert(name, '_segm'))

    def pick_clust(self):
        self.message("Pick segmentation output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.set_output_name(name)

    def set_output_name(self, name):
        self.fileClust.set(name)
        if name:
            self.fileThres.set(postfix.insert(name, '_thres'))
            self.fileSalt.set(postfix.insert(name, '_salt'))
            self.fileQuad.set(postfix.insert(name, '_quad'))

    def pick_thres(self):
        self.message("Pick segmentation output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.fileThres.set(name)

    def pick_salt(self):
        self.message("Pick segmentation output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.fileSalt.set(name)

    def pick_quad(self):
        self.message("Pick segmentation output file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', os.path.dirname(name))
            self.fileQuad.set(name)

    def pick_edgemap(self):
        self.message("Pick input Edge Map.")
##        name = self.edgeMap.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Edge Map',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.edgeMap.set(name)

            # calculate statistics and give hint for split & merge levels
            im = envi2.Open(name)
            a = im.data.flatten()
            a.sort()
            m = a[len(a)*0.40]
            self.message('Suggested split level: %f' % (m,))
            self.message('Suggested merge level: %f' % (0.9*m,))
            self.message('''The suggested merge level is only valid if
the split and merge phase use the same
input and distance measure!''')
##            self.splitLevel.set(m)
##            self.mergeLevel.set(m*0.9)
            del im, a

            # generate output name
#            if self.nameOut.get() == "":
##            if name[-4] != '.':
##                self.nameOut.set(name + POSTFIX)
##                self.thermOut.set(name + THERMFIX)
##            else:
##                names = name.rsplit('.', 1)
##                self.nameOut.set(names[0] + POSTFIX + '.' + names[1])
##                self.thermOut.set(names[0] + THERMFIX + '.' + names[1])

##    def pick_continuum(self):
##        self.message("Pick continuum removed image.")
##        name = self.nameIn.get()
##        if name:
##            idir = os.path.dirname(name)
##        else:
##            idir = r'D:'
##        name = askopenfilename(title='Open Continuum Removed',
##                                   initialdir=idir,
##                                   initialfile='')
##        if name:
##            self.nameHull.set(name)
        
##    def pick_output(self):
##        self.message("Pick output file.")
##        self.nameOut.set(asksaveasfilename(title='Open Output File',
##                                   initialdir=r'D:',
##                                   initialfile=''))

##    def pick_thermal(self):
##        self.message("Pick thermal output file.")
##        self.nameOut.set(asksaveasfilename(title='Open Thermal Output File',
##                                   initialdir=r'D:',
##                                   initialfile=''))

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
        self.choice = StringVar()
        self.nameIn = StringVar()
        self.edgeMap = StringVar()

        self.fileThres = StringVar()
        self.fileSalt = StringVar()
        self.fileQuad = StringVar()
        self.fileClust = StringVar()
        
##        self.nameHull = StringVar()
##        self.nameOut = StringVar()
##        self.thermOut = StringVar()

        self.splitLevel = DoubleVar()
        self.splitLevel.set(conf.get_option('split-level', segmentation.SPLIT_LEVEL,
                                            type_=float))

        self.mergeLevel = DoubleVar()
        self.mergeLevel.set(conf.get_option('merge-level', segmentation.MERGE_LEVEL,
                                            type_=float))

        self.sortWav = IntVar()
        self.useBBL = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        row = 0

        # checkbutton
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)

        Checkbutton(frame, text="Sort bands on wavelength", variable=self.sortWav).grid(row=0, column=0, sticky=W)
        Checkbutton(frame, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=1, column=0, sticky=W)

        row = row + 1

        # input file
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)

        Label(frame, text="Input:").grid(row=0, column=0, sticky=W)
        
        Label(frame, text="Edge Map").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.edgeMap, width=30).grid(row=1, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_edgemap).grid(row=1, column=2, sticky=W)

        Label(frame, text="Input file").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self.nameIn, width=30).grid(row=2, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_input).grid(row=2, column=2, sticky=W)

        row = row + 1

        # output files
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)

        Label(frame, text="Output:").grid(row=0, column=0, sticky=W)
        
        Label(frame, text="Segmented").grid(row=1, column=0, sticky=W)
        Entry(frame, textvariable=self.fileClust, width=30).grid(row=1, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_clust).grid(row=1, column=2, sticky=W)

        Label(frame, text="Threshold").grid(row=2, column=0, sticky=W)
        Entry(frame, textvariable=self.fileThres, width=30).grid(row=2, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_thres).grid(row=2, column=2, sticky=W)

        Label(frame, text="Filtered").grid(row=3, column=0, sticky=W)
        Entry(frame, textvariable=self.fileSalt, width=30).grid(row=3, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_salt).grid(row=3, column=2, sticky=W)

        Label(frame, text="Quads").grid(row=4, column=0, sticky=W)
        Entry(frame, textvariable=self.fileQuad, width=30).grid(row=4, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_quad).grid(row=4, column=2, sticky=W)

        row = row + 1

        # Split level
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)

        Label(frame, text="Split Level").grid(row=0, column=0, sticky=E)
        Entry(frame, textvariable=self.splitLevel, width=6).grid(row=0, column=1, sticky=W)

        Label(frame, text="Merge Level").grid(row=1, column=0, sticky=E)
        Entry(frame, textvariable=self.mergeLevel, width=6).grid(row=1, column=1, sticky=W)

        row = row + 1

        # next frame
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)

        Label(frame, text="Distance measure used for merging:").grid(row=0, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='SAM', text='Spectral Angle').grid(row=1, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='ID', text='Intensity difference').grid(row=2, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='ED', text='Euclidean Distance').grid(row=3, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='BC', text='Bray Curtis Distance').grid(row=4, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='SID', text='Spectral Information Divergence').grid(row=5, column=0, sticky=W)
        self.choice.set(conf.get_option('method', "SAM"))

        row = row + 1

        # frame 2
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=W+E)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        Button(frame,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(frame,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # Text box
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
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
        self.columnconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)


root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('method', app.choice.get())

conf.set_option('split-level', app.splitLevel.get())
conf.set_option('merge-level', app.mergeLevel.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
