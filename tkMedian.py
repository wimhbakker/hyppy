#!/usr/bin/python3
#
#     tkMedian.py
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
    import median
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
        self.message("Hyperspectral Median/Mean Filtering.")
        self.message(about.about)
        self.message("""Note: the fast filters now do take into account
not-a-number (NaN)
""")
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            median.median(self.nameIn.get(), self.nameOut.get(), mode=self.choice.get(), message=self.message,
                      sort_wavelengths=self.sortWav.get(), use_bbl=self.useBBL.get(),
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
                    self.nameOut.set(name + '_' + self.choice.get())
                else:
                    names = name.rsplit('.', 1)
                    self.nameOut.set(names[0] + '_' + self.choice.get() + '.' + names[1])
        
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

        self.sortWav.set(conf.get_option('sort-wavelength', 0, type_=int))
        self.useBBL.set(conf.get_option('use-bbl', 1, type_=int))

        row = 0

        # checkbutton
        Checkbutton(self, text="Sort bands on wavelength", variable=self.sortWav).grid(row=row, column=0, sticky=W)
        
        row = row + 1

        # checkbutton
        Checkbutton(self, text="Use bad band list (BBL)", variable=self.useBBL).grid(row=row, column=0, sticky=W)

        row = row + 1

        # frame
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        Radiobutton(frame, variable=self.choice, value='med7', text='Median 1+5+1 neighborhood').grid(row=0, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='med27', text='Median 9+9+9 neighborhood').grid(row=1, column=0, sticky=W)

        row = row + 1

        # frame
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        Radiobutton(frame, variable=self.choice, value='fmed7', text='Fast Median 1+5+1 neighborhood').grid(row=0, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='fmed19', text='Fast Median 5+9+5 neighborhood').grid(row=1, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='fmed27', text='Fast Median 9+9+9 neighborhood').grid(row=2, column=0, sticky=W)

        row = row + 1

        # frame
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        Radiobutton(frame, variable=self.choice, value='mean7', text='Fast Mean 1+5+1 neighborhood').grid(row=0, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='mean19', text='Fast Mean 5+9+5 neighborhood').grid(row=1, column=0, sticky=W)
        Radiobutton(frame, variable=self.choice, value='mean27', text='Fast Mean 9+9+9 neighborhood').grid(row=2, column=0, sticky=W)
        self.choice.set(conf.get_option('choice', "med7"))

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
        self.progressBar.grid(row=row, column=0, columnspan=3, sticky=W+E)

root = Tk()
app = Application(root)
root.title("Hyper Filter")
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('choice', app.choice.get())

conf.set_option('use-bbl', app.useBBL.get())
conf.set_option('sort-wavelength', app.sortWav.get())

root.destroy()
