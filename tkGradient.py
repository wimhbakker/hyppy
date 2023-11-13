#!/usr/bin/python3
#
#     tkGradient.py
#       Bug fix 20100521 WHB, X gradient didn't work
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

DESCRIPTION = "Hyperspectral Gradient"

import os
from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import gradient
    import conf
    import about
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

POSTFIX = '_grad'

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

    def get_choices(self):
        result = []
        if self.choiceX.get():
            result.append('X')
        if self.choiceY.get():
            result.append('Y')
        if self.choiceXY.get():
            result.append('XY')
        if self.choiceU.get():
            result.append('U')
        if self.choiceD.get():
            result.append('D')
        if self.choiceUD.get():
            result.append('UD')
        if self.choiceXYUD.get():
            result.append('XYUD')
        if self.choiceE4.get():
            result.append('E4')
        if self.choiceE8.get():
            result.append('E8')
        if self.choiceSOBX.get():
            result.append('SOBX')
        if self.choiceSOBY.get():
            result.append('SOBY')
        if self.choiceSOBEL.get():
            result.append('SOBEL')
        return result
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            gradient.gradient(self.nameIn.get(), self.nameOut.get(),
                          mode=self.choice.get(), message=self.message,
                          sort_wavelengths=self.sortWav.get(),
                          use_bbl=self.useBBL.get(),
                          choices=self.get_choices(),
                          nansafe=self.nanSafe.get(),
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
        self.choice = StringVar()
        self.nameIn = StringVar()
        self.nameOut = StringVar()

        self.sortWav = IntVar()
        self.useBBL = IntVar()
        self.nanSafe = IntVar()

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 0, type_=int))
        self.nanSafe.set(conf.get_option('nan-safe', 0, type_=int))

        self.choiceX =     IntVar(value=conf.get_option('option-x', 0, type_=int))
        self.choiceY =     IntVar(value=conf.get_option('option-y', 0, type_=int))
        self.choiceXY =    IntVar(value=conf.get_option('option-xy', 0, type_=int))
        self.choiceU =     IntVar(value=conf.get_option('option-u', 0, type_=int))
        self.choiceD =     IntVar(value=conf.get_option('option-d', 0, type_=int))
        self.choiceUD =    IntVar(value=conf.get_option('option-ud', 0, type_=int))
        self.choiceXYUD =  IntVar(value=conf.get_option('option-xyud', 1, type_=int))
        self.choiceE4 =    IntVar(value=conf.get_option('option-edgy-4', 0, type_=int))
        self.choiceE8 =    IntVar(value=conf.get_option('option-edgy-8', 0, type_=int))
        self.choiceSOBX =  IntVar(value=conf.get_option('option-sobel-x', 0, type_=int))
        self.choiceSOBY =  IntVar(value=conf.get_option('option-sobel-y', 0, type_=int))
        self.choiceSOBEL = IntVar(value=conf.get_option('option-sobel', 0, type_=int))

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav).grid(row=row, column=0, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=row, column=0, sticky=W)

        row = row + 1

        # frame 1
        self.frame1 = Frame(self)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(1, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        Label(self.frame1, text="Input").grid(row=0, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn).grid(row=0, column=1, sticky=W+E)
        Button(self.frame1, text='...', command=self.pick_input).grid(row=0, column=2, sticky=W)

        Label(self.frame1, text="Output").grid(row=1, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameOut).grid(row=1, column=1, sticky=W+E)
        Button(self.frame1, text='...', command=self.pick_output).grid(row=1, column=2, sticky=W)

        row = row + 1

        # frame 0
        self.frame0 = Frame(self, bd=1, relief=GROOVE)
        self.frame0.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame0.columnconfigure(0, weight=1)
        self.frame0.rowconfigure(0, weight=1)

        Radiobutton(self.frame0, variable=self.choice, value='SAM', text='Spectral Angle').grid(row=0, column=0, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='ID', text='Intensity Differrence').grid(row=1, column=0, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='ED', text='Euclidean Distance').grid(row=2, column=0, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='BC', text='Bray-Curtis Distance').grid(row=3, column=0, sticky=W)
        Radiobutton(self.frame0, variable=self.choice, value='SID', text='Spectral Information Divergence').grid(row=4, column=0, sticky=W)
        self.choice.set(conf.get_option('mode', "SAM"))

        Checkbutton(self.frame0, variable=self.nanSafe, text='Use NaN-safe functions').grid(row=5, column=0, sticky=W)

        row = row + 1

        # choices
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)

        sframe = Frame(frame)
        sframe.grid(row=0, column=0)
        Checkbutton(sframe, text='X grad.', variable=self.choiceX).grid(row=0, column=0, sticky=W)
        Checkbutton(sframe, text='Y grad.', variable=self.choiceY).grid(row=1, column=0, sticky=W)
        Checkbutton(sframe, text='X+Y', variable=self.choiceXY).grid(row=2, column=0, sticky=W)

        sframe = Frame(frame)
        sframe.grid(row=0, column=1)
        Checkbutton(sframe, text='Up diag.', variable=self.choiceU).grid(row=0, column=0, sticky=W)
        Checkbutton(sframe, text='Down diag.', variable=self.choiceD).grid(row=1, column=0, sticky=W)
        Checkbutton(sframe, text='U+D', variable=self.choiceUD).grid(row=2, column=0, sticky=W)

        sframe = Frame(frame)
        sframe.grid(row=0, column=2)
        Checkbutton(sframe, text='2X+2Y+U+D', variable=self.choiceXYUD).grid(row=0, column=0, sticky=W)
        Checkbutton(sframe, text='Edgy 4-neigh.', variable=self.choiceE4).grid(row=1, column=0, sticky=W)
        Checkbutton(sframe, text='Edgy 8-neigh.', variable=self.choiceE8).grid(row=2, column=0, sticky=W)

        sframe = Frame(frame)
        sframe.grid(row=0, column=3)
        Checkbutton(sframe, text='Sobel X', variable=self.choiceSOBX).grid(row=0, column=0, sticky=W)
        Checkbutton(sframe, text='Sobel Y', variable=self.choiceSOBY).grid(row=1, column=0, sticky=W)
        Checkbutton(sframe, text='Sobel', variable=self.choiceSOBEL).grid(row=2, column=0, sticky=W)

        row = row + 1

        # frame 2
        self.frame2 = Frame(self)
        self.frame2.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame2.columnconfigure(0, weight=1)
        self.frame2.columnconfigure(1, weight=1)
        self.frame2.rowconfigure(0, weight=1)
        
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

        
##        #pack everything
##        self.text.pack(side=LEFT)
##        self.scroll.pack(side=RIGHT,fill=Y)

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

conf.set_option('mode', app.choice.get())

conf.set_option('option-x',       app.choiceX.get())
conf.set_option('option-y',       app.choiceY.get())
conf.set_option('option-xy',      app.choiceXY.get())
conf.set_option('option-u',       app.choiceU.get())
conf.set_option('option-d',       app.choiceD.get())
conf.set_option('option-ud',      app.choiceUD.get())
conf.set_option('option-xyud',    app.choiceXYUD.get())
conf.set_option('option-edgy-4',  app.choiceE4.get())
conf.set_option('option-edgy-8',  app.choiceE8.get())
conf.set_option('option-sobel-x', app.choiceSOBX.get())
conf.set_option('option-sobel-y', app.choiceSOBY.get())
conf.set_option('option-sobel',   app.choiceSOBEL.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())
conf.set_option('nan-safe', app.nanSafe.get())

root.destroy()
