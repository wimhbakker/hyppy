#!/usr/bin/python3
#
#     tkMnfstats.py
#
#   Created: WHB 20090403
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
import mnfstats

POSTFIX = '_mnfstats'

class Application(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.pack()
        self.makeWindow(master)
        self.message("MNF stats.")
        self.message("Converts an MNF statistics (.txt) file into a 3-band ENVI image.")
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        try:
            mnfstats.mnfstats(self.nameIn.get(), self.nameOut.get(), self.message)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input file.")
        name = self.nameIn.get()
        if name:
            idir = os.path.dirname(name)
        else:
            idir = r'D:'
        name = askopenfilename(title='Open Input File',
                               filetypes=(('Text Files', '*.txt'), ('All Files', '*')),
                                   initialdir=idir,
                                   initialfile='')
        if name:
            self.nameIn.set(name)
            # generate output name
#            if self.nameOut.get() == "":
            if not name.endswith('.txt'):
                self.nameOut.set(name + POSTFIX)
            else:
                names = name.rsplit('.', 1)
                self.nameOut.set(names[0] + POSTFIX)
        
    def pick_output(self):
        self.message("Pick output file.")
        self.nameOut.set(asksaveasfilename(title='Open Output File',
                                   initialdir=r'D:',
                                   initialfile=''))

    def message(self, s):
        self.text.insert(END, s + '\n')
        self.text.see(END)
        self.text.update()

    def makeWindow(self, master):
        # variables
        self.nameIn = StringVar()
        self.nameOut = StringVar()

        # frame 1
        self.frame1 = Frame(master)
        self.frame1.pack()

        Label(self.frame1, text="Input").grid(row=0, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn, width=40).grid(row=0, column=1, sticky=W)
        Button(self.frame1, text='...', command=self.pick_input).grid(row=0, column=2, sticky=W)

        Label(self.frame1, text="Output").grid(row=1, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameOut, width=40).grid(row=1, column=1, sticky=W)
        Button(self.frame1, text='...', command=self.pick_output).grid(row=1, column=2, sticky=W)

        # frame 2
        self.frame2 = Frame(master)
        self.frame2.pack()
        Button(self.frame2,text="Run",command=self.do_run).grid(row=0, column=0)
        Button(self.frame2,text="Exit",command=self.do_exit).grid(row=0, column=1)

        # frame 3
        self.frame3 = Frame(master)
        self.frame3.pack()
        self.text = Text(self.frame3, width=50, height=10)

        # scrollbar
        self.scroll=Scrollbar(self.frame3)
        # attach text to scrollbar and vice versa
        self.text.configure(yscrollcommand=self.scroll.set)
        self.scroll.config(command=self.text.yview)
        
        #pack everything
        self.text.pack(side=LEFT)
        self.scroll.pack(side=RIGHT,fill=Y)


root = Tk()
app = Application(root)
root.title("MNF stats")
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()
root.destroy()
