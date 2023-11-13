#!/usr/bin/python3
#
#     tkSpecLib.py
#
#   Created:  WHB 20081204
#   Modified: WHB 20091116
#   Modified: WHB 20121211, work on spectral math
#   Modified: WHB 20150323, fixed loading of ASCII files
#   Modified: WHB 20171222, added recursive loading of ASCII files
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
import collections
import numpy
import sys

from scipy.interpolate import interp1d, UnivariateSpline

from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import envi2
    import tkValueViewer

    from matplotlib import rcParams
    rcParams['legend.fontsize'] = 8

    from pylab import plot, xlabel, legend, ion, close, draw, array, clf

    from quickhull2d import hull_resampled

    import ascspeclib
    import conf
    from spectrum import Spectrum
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

ion()

HELPFILE = 'Docs/spectrum.pdf'
PYTHON = sys.executable     # where's Python?
PDFREADER = 'evince'        # for Linux

def make_command(action):
    '''Trick to remember the action'''
    return lambda: command(action)

def command(action):
    '''Execute menu button command'''
    if action.lower().endswith('.py'):        
        return os.spawnv(os.P_NOWAIT, PYTHON, [PYTHON, action])
    if action.lower().endswith('.pdf'):
        thePDF = os.path.join(os.getcwd(), action)
        try:
            return os.spawnvp(os.P_NOWAIT, PDFREADER, [PDFREADER, thePDF])
        except AttributeError:  # Good Grief! We're on Windows???
            return os.startfile(thePDF)

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
        self.message("Spectral Library Viewer.")
    
    def do_exit(self):
        root.quit()

    def load_spectra(self, event):
        nameIn = self.nameIn.get()
        if nameIn:
            self.listbox.delete(0, END)
            if os.path.isdir(nameIn):
                self.speclib = ascspeclib.AscSpeclib(nameIn, recursive=(self.speclibAsc.get()=='ascdirrecursive'))
            else:
                try:
                    self.speclib = envi2.Speclib(nameIn)
                except (AttributeError, ValueError):
                    self.speclib = ascspeclib.AscSpeclib(nameIn, recursive=(self.speclibAsc.get()=='ascdirrecursive'))
            for sname in self.speclib.names():
                self.listbox.insert(END, sname)
            
    def pick_input(self):
        self.message("Pick input file.")
##        name = self.nameIn.get()
##        if name:
##            initialdir = os.path.dirname(name)
##        else:
##            initialdir = r'D:'
        initialdir = conf.get_option('input-dir')
            
        if 'ascdir' in self.speclibAsc.get():
            name = askdirectory(title='Open Directory',
                                       initialdir=initialdir)
        else:
            name = askopenfilename(title='Open Input File',
                                       initialdir=initialdir,
                                       initialfile='')
        if name:
            if os.path.isdir(name):
                conf.set_option('input-dir', name)
            else:
                conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)
            self.load_spectra(None)
            self.description.delete("1.0", END) 

    def pick_spec(self, i):
##        i = self.listbox.nearest(event.y)
        s = self.speclib.spectrum(i)
        label = str(self.speclib.name(i))
        description = self.speclib.description(i)
        w = self.speclib.wavelength(i)
        if not w is None:
##            w = self.speclib.wavelength(i)
##            plot(h.wavelength, self.speclib.get_spectrum(i), label=h.spectra_names[i])
            units = self.speclib.wavelength_units(i)
            if units:
                xlabel('wavelength (%s)' % (units,))
            else:
                xlabel('wavelength')
##            self.legend = legend()
        else:
            w = list(range(len(s)))
##            plot(self.speclib.get_spectrum(i), label=h.spectra_names[i])
            xlabel('band')

##        if self.removeHull.get():
##            hull = hull_resampled(array(list(zip(w, s))))
##            # continuum removed, first divide, then subtract
##            if self.choiceHull.get()=='div':
##                w = hull[:,0]
##                s = s/hull[:,1]
##                label = label + ' / CH'
##            else:
##                w = hull[:,0]
##                s = 1+(s-hull[:,1])
##                label = label + ' - CH + 1'

        S = Spectrum(wavelength=w, spectrum=s, name=label)
        if self.removeHull.get():
            S = S.nohull(mode=self.choiceHull.get())
            if self.choiceHull.get()=='div':
                label = label + ' / CH'
            else:
                label = label + ' - CH + 1'

        w = S.w
        s = S.s

        plot(w, s, label=label)
        self.legend = legend(loc=0)
        self.legend_state()
        return                      #  <======  !!!
        if description:
            self.description.delete("1.0", END) 
            self.description.insert("1.0", description)
            self.description.see("1.0")

        self.valueviewer.clear()
        self.valueviewer.add('# %s (%s)\n' % (self.nameIn.get(), label))
        if self.removeHull.get():
            self.valueviewer.add('# Continuum removed (%s)\n' % (self.choiceHull.get(),))
        for cx, cy in zip(w, s):
            self.valueviewer.add('%f %f\n' % (cx, cy))
        
    def plot(self):
        clf()
        specs = self.listbox.curselection()
        for spec in specs:
            self.pick_spec(int(spec))

    def in_viewer(self, i):
        s = self.speclib.spectrum(i)
        label = str(self.speclib.name(i))
        description = self.speclib.description(i)
        w = self.speclib.wavelength(i)
        if w is None:
            w = list(range(len(s)))

##        if self.removeHull.get():
##            hull = hull_resampled(array(list(zip(w, s))))
##            # continuum removed, first divide, then subtract
##            if self.choiceHull.get()=='div':
##                w = hull[:,0]
##                s = s/hull[:,1]
##                label = label + ' / CH'
##            else:
##                w = hull[:,0]
##                s = 1+(s-hull[:,1])
##                label = label + ' - CH + 1'

        S = Spectrum(wavelength=w, spectrum=s, name=label)
        if self.removeHull.get():
            S = S.nohull(mode=self.choiceHull.get())
            if self.choiceHull.get()=='div':
                label = label + ' / CH'
            else:
                label = label + ' - CH + 1'

        w = S.w
        s = S.s

        valueviewer = tkValueViewer.ValueViewer(self, title=label, destroy_on_close=True)
        valueviewer.clear()
        valueviewer.add('# %s (%s)\n' % (self.nameIn.get(), label))
        if self.removeHull.get():
            valueviewer.add('# Continuum removed (%s)\n' % (self.choiceHull.get(),))
        for cx, cy in zip(w, s):
            valueviewer.add('%f %f\n' % (cx, cy))

    def view_values(self):
        specs = self.listbox.curselection()
        for spec in specs:
            self.in_viewer(int(spec))

    def get_spec_list(self, spec_ids):
        # get spectra as a list of Spectrum objects
        Slist = []
        Sall = Slist # alias
        for i in spec_ids:
            spec = self.speclib.spectrum(i)
            label = str(self.speclib.name(i))

            w = self.speclib.wavelength(i)
            if w is None:
                w = list(range(len(spec)))

            S = Spectrum(wavelength=w, spectrum=spec, name=label)
            if self.removeHull.get():
                S = S.nohull(mode=self.choiceHull.get())

            Slist.append(S)

        return Slist

    def bandmath_spec(self, spec_ids, exp):
        Slist = self.get_spec_list(spec_ids)

        # go for it!
        self.valueviewer.clear()
        self.valueviewer.deiconify()
        self.valueviewer.add('# %s\n' % (self.nameIn.get(),))
        self.valueviewer.add('# Expression: %s\n' % (exp,))

        if self.removeHull.get():
            self.valueviewer.add('# Continuum removed (%s)\n' % (self.choiceHull.get(),))

        for S in Slist:
            try:
                result = eval(exp)
            except Exception as err:
                tkinter.messagebox.showerror(title='Error', message=str(err))
                raise

            if isinstance(result, str):
                pass
            elif isinstance(result, Spectrum):
                result = str(result)
            elif isinstance(result, collections.abc.Iterable):
                result = ' '.join(map(str, result))
            else:
                result = str(result)
            
            self.valueviewer.add('%s %s\n' % (S.name, result))

    def bandmath(self, event=None):
        spec_ids = list(map(int, self.listbox.curselection()))
        exp = self.expression.get()

        self.bandmath_spec(spec_ids, exp)

    def average_spec(self, spec_ids):
        Slist = self.get_spec_list(spec_ids)

        # go for it!
        valueviewer = tkValueViewer.ValueViewer(self, title='Average', destroy_on_close=True)
        valueviewer.clear()
        valueviewer.deiconify()
        valueviewer.add('# %s\n' % (self.nameIn.get(),))
        valueviewer.add('# Average of:\n')

        if self.removeHull.get():
            self.valueviewer.add('# Continuum removed (%s)\n' % (self.choiceHull.get(),))

        for i in range(len(Slist)):
            valueviewer.add('# %s\n' % (Slist[i].name,))
            if i == 0:
                result = Slist[i]
            else:
                try:
                    result = result + Slist[i]
                except Exception as err:
                    tkinter.messagebox.showerror(title='Error', message=str(err))
                    raise

        result = result / len(Slist)

        w = result.w
        s = result.s

        for cx, cy in zip(w, s):
            valueviewer.add('%f %f\n' % (cx, cy))

        self.plot()
        plot(w, s, label='Average')
        self.legend = legend(loc=0)
        self.legend_state()

    def average(self, event=None):
        spec_ids = list(map(int, self.listbox.curselection()))

        if spec_ids:
            self.average_spec(spec_ids)

    def message(self, s):
        pass

    def legend_state(self):
        if hasattr(self, 'legend'):
            self.legend.set_visible(self.legendSwitch.get())
            draw()

    def create_valueviewer(self):
        if not hasattr(self, 'valueviewer'):
            self.valueviewer = tkValueViewer.ValueViewer(self, title='View Values', command=self.value_window_returns, width=60)
            self.valueviewer.withdraw()

    def toggle_valueviewer(self):
        if self.viewValuesWindow.get():
            self.valueviewer.deiconify()
        else:
            self.valueviewer.withdraw()

    def value_window_returns(self, value):
        self.viewValuesWindow.set(0)

    def dummy(self, *args):
        pass

    def makeWindow(self, master):
        # variables
        self.nameIn = StringVar()
        self.legendSwitch = IntVar(value=conf.get_option('legend', 1, type_=int))
        
        self.speclibAsc = StringVar()

        self.removeHull = IntVar(value=conf.get_option('remove-hull', 0, type_=int))
        self.choiceHull = StringVar(value=conf.get_option('hull-option', 'div'))

        self.viewValuesWindow = IntVar(value=0)

        self.expression = StringVar()
        self.expression.set(conf.get_option('expression', ''))

        row = 0

        # Legend switch...
        frame = Frame(master=self)
        frame.grid(row=row, column=0, columnspan=2, sticky=W+E)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        row = 0
        Radiobutton(frame, text='ENVI Speclib', variable=self.speclibAsc, value='envi').grid(row=row, column=0, sticky=W)
        row = row + 1
        Radiobutton(frame, text='ASCII directory', variable=self.speclibAsc, value='ascdir').grid(row=row, column=0, sticky=W)
        row = row + 1
        Radiobutton(frame, text='ASCII directory recursive', variable=self.speclibAsc, value='ascdirrecursive').grid(row=row, column=0, sticky=W)
        row = row + 1
        Radiobutton(frame, text='ASCII file', variable=self.speclibAsc, value='ascfile').grid(row=row, column=0, sticky=W)
        self.speclibAsc.set(conf.get_option('speclib-type', 'envi'))

        row = row + 1

        # Label, File Entry, Button...
        frame = Frame(master=self)
        frame.grid(row=row, column=0, columnspan=2, sticky=W+E)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="Input").grid(row=0, column=0, sticky=W)
        e = Entry(frame, textvariable=self.nameIn)
        e.grid(row=0, column=1, sticky=W+E)
        e.bind('<Key-Return>', self.load_spectra)
        Button(frame, text='Browse', command=self.pick_input).grid(row=0, column=2, sticky=W)

        row = row + 1

        # Remove Convex Hull stuff...
        frame = Frame(master=self)
        frame.grid(row=row, column=0, columnspan=2, sticky=W+E)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(0, weight=1)

        Checkbutton(frame, text='Remove Convex Hull', variable=self.removeHull).grid(row=0, column=0, sticky=W+E)
        Radiobutton(frame, text='divide', variable=self.choiceHull, value='div').grid(row=0, column=1, sticky=W+E)
        Radiobutton(frame, text='subtract', variable=self.choiceHull, value='sub').grid(row=0, column=2, sticky=W+E)
        
        row = row + 1

        # ListBox & Scrollbars
        stretchrow = row
        self.yScroll = Scrollbar(self, orient=VERTICAL)
        self.yScroll.grid(row=row, column=1, sticky=N+S)
        
        self.xScroll = Scrollbar(self, orient=HORIZONTAL)
        self.xScroll.grid(row=row+1, column=0, sticky=E+W)
        
        self.listbox = Listbox(self, width=40, height=30,
                               selectmode=EXTENDED,
                            xscrollcommand=self.xScroll.set,
                            yscrollcommand=self.yScroll.set)
        self.listbox.bind("<Button-1>", self.dummy)
        self.listbox.grid(row=row, column=0, sticky=N+S+E+W)
        
        self.xScroll["command"] = self.listbox.xview
        self.yScroll["command"] = self.listbox.yview

        row = row + 1

        # frame for description text box
        frame = Frame(master=self)
        frame.grid(row=row, column=0, columnspan=2, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        self.description = Text(frame, width=30, height=4)
        self.description.grid(row=0, column=0, sticky=N+E+S+W)

        # scrollbar
        scroll=Scrollbar(frame)
        # attach text to scrollbar and vice versa
        self.description.configure(yscrollcommand=scroll.set)
        scroll.config(command=self.description.yview)
        scroll.grid(row=0, column=1, sticky=N+S)

        row = row + 1

        # Legend switch...
        frame = Frame(master=self)
        frame.grid(row=row, column=0, columnspan=2, sticky=W+E)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Radiobutton(frame, text='legend on', variable=self.legendSwitch, value=1, command=self.legend_state).grid(row=0, column=0, sticky=W+E)
        Radiobutton(frame, text='legend off', variable=self.legendSwitch, value=0, command=self.legend_state).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # Value Viewer...
        frame = Frame(master=self)
        frame.grid(row=row, column=0, columnspan=2, sticky=W+E)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Button(frame, text='Plot', command=self.plot).grid(row=0, column=0, sticky=W+E)
        Button(frame, text='View Values', command=self.view_values).grid(row=0, column=1, sticky=W+E)
        Button(frame, text='Average', command=self.average).grid(row=0, column=2, sticky=W+E)
        Button(frame,text="Exit",command=root.quit).grid(row=0, column=3, sticky=W+E)

        self.create_valueviewer()
##        Checkbutton(frame, text='View Values Window', variable=self.viewValuesWindow, command=self.toggle_valueviewer).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # Label, Expresion...
        frame = Frame(self, bd=2, relief=GROOVE)
        frame.grid(row=row, column=0, columnspan=2, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        Label(frame, text="Math Expression on Spectrum S:").grid(row=0, column=0, sticky=W)
        e = Entry(frame, textvariable=self.expression)
        e.grid(row=1, column=0, sticky=W+E)
        e.bind('<Key-Return>', self.bandmath)
        Button(frame, text='Go', command=self.bandmath).grid(row=1, column=1, sticky=E)
        Button(frame, text='?', command=make_command(HELPFILE)).grid(row=1, column=2, sticky=E)

        # allow column=1 and row=1 to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(stretchrow, weight=1)


root = Tk()
app = Application(root)
root.title("SpecLib Viewer")
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('legend', app.legendSwitch.get())
conf.set_option('remove-hull', app.removeHull.get())
conf.set_option('hull-option', app.choiceHull.get())
conf.set_option('speclib-type', app.speclibAsc.get())

conf.set_option('expression', app.expression.get())

root.destroy()

# close all figures
close('all')
