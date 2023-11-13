#!/usr/bin/python3
#
#     tkClassifier.py
#
#   Created: WHB 20091113
#   Modified: WHB 20220922, adding thresholds
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
import numpy
from numpy.random import randint
from tkinter import *
from tkinter.filedialog import *
from tkinter.colorchooser import askcolor
import tkinter.messagebox

try:
    import sam
    import conf
    import about
    import envi2
    from tkProgressBar import *
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Rule Classifier"

POSTCLASS = '_class'
POSTQUALITY = '_qual'

def color_hex_to_rgb(color):
    return tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

def color_rgb_to_hex(rgb):
    return "#%02x%02x%02x" % rgb

def colors_hex_to_rgb(colors):
    if colors:
        return [color_hex_to_rgb(c) for c in colors]

def colors_rgb_to_hex(rgbs):
    if rgbs:
        return [color_rgb_to_hex(rgb) for rgb in rgbs]
 
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
        self.message("""For no threshold set Threshold to:
+inf or inf (for minimum)
-inf (for maximum)
""")
    
    def do_run(self) :
        self.message("In: " + self.nameIn.get())
        self.message("Out: " + self.nameClass.get())

        if hasattr(self, 'thresholdlist'):
            thresholds = [var.get() for var in self.thresholdlist]
        else:
            thresholds = None

        if hasattr(self, 'buttonlist'):
            class_lookup = [but['bg'] for but in self.buttonlist]
        else:
            class_lookup = None

        self.message("Classifying rule images...")
        try:
            sam.classify(self.nameIn.get(), self.nameClass.get(),
                         self.nameQuality.get(),
                         mode=self.choice.get(),
                         message=self.message,
                         progress=self.progressBar,
                         threshold=self.threshold.get(),
                         thresholds=thresholds,
                         class_lookup=colors_hex_to_rgb(class_lookup))

            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input file.")
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Input Rule Image',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)
            # generate output names
            if name[-4] != '.':
                self.nameClass.set(name + POSTCLASS)
                self.nameQuality.set(name + POSTQUALITY)
            else:
                names = name.rsplit('.', 1)
                self.nameClass.set(names[0] + POSTCLASS + '.' + names[1])
                self.nameQuality.set(names[0] + POSTQUALITY + '.' + names[1])

            # set up thresholds...
            for widgets in self.frame5.winfo_children():
                widgets.destroy()
            self.frame5['height'] = 1 # force frame5 to resize...
##            if hasattr(self, 'thresholdlist') and self.thresholdlist:
##                for lab, ent, var in self.thresholdlist:
##                    lab.destroy()
##                    ent.destroy()
##                del self.thresholdlist
            im = envi2.Open(name)
            if hasattr(im, 'band_names'):
                # color lookup table with random colors... first is unclassified class...
                class_lookup = ((0,0,0),) + tuple(((randint(64, 256), randint(64, 256), randint(64, 256)) for i in range(im.bands)))
##                print(class_lookup)
##                print(colors_rgb_to_hex(class_lookup))
                brightness = [sum(t) // 3 for t in class_lookup]
                class_lookup = colors_rgb_to_hex(class_lookup)
                
                Button(self.frame5, text='Set all thresholds', command=self.set_all).grid(row=0, column=0, sticky=E)
                Entry(self.frame5, textvariable=self.threshold, width=6).grid(row=0, column=1, sticky=W)
                band_names = im.band_names
                row = 1
                self.thresholdlist = list()
                self.buttonlist = list()

                lab = Label(self.frame5, text='Unclassified') # does not have a threshold...
                lab.grid(row=row, column=0, sticky=E)

                but = Button(self.frame5, text='Set color', bg=class_lookup[0],
                                 fg='#000000' if brightness[0] > 127 else '#ffffff')
                but['command'] = self.color_picker_func(but, class_lookup[0])
                but.grid(row=row, column=2, sticky=E)
                self.buttonlist.append(but)
                
                row = row + 1

                for i, band_name in enumerate(band_names):
                    lab = Label(self.frame5, text=band_name)
                    lab.grid(row=row, column=0, sticky=E)

                    var = DoubleVar()
                    var.set(numpy.inf)
                    ent = Entry(self.frame5, textvariable=var, width=6)
                    ent.grid(row=row, column=1, sticky=W)
                    self.thresholdlist.append(var)

                    but = Button(self.frame5, text='Set color', bg=class_lookup[i+1],
                                 fg='#000000' if brightness[i+1] > 127 else '#ffffff')
                    but['command'] = self.color_picker_func(but, class_lookup[i+1])
                    but.grid(row=row, column=2, sticky=E)
                    self.buttonlist.append(but)
                    
                    row = row + 1

    def color_picker_func(self, but, col):
        def color_picker():
            color = askcolor(color=col, title="Class color picker")[1]
            if color:
##                print(color, tuple(int(color[i:i+2], 16) for i in (1, 3, 5)))
                but['bg'] = color
                brightness = sum(color_hex_to_rgb(color)) // 3
                but['fg'] = '#000000' if brightness > 127 else '#ffffff'
        return color_picker

##    def color_picker(self):
##        color = askcolor(title="Class color picker")
##        print(color)

    def set_all(self):
        if hasattr(self, 'thresholdlist') and self.thresholdlist:
            for var in self.thresholdlist:
                var.set(self.threshold.get())
        
    def pick_class(self):
        self.message("Pick output classification file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output Classification',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', s.path.dirname(name))
            self.nameClass.set(name)

    def pick_quality(self):
        self.message("Pick output quality file.")
        odir = conf.get_option('output-dir')
        name = asksaveasfilename(title='Open Output Quality File',
                                   initialdir=odir,
                                   initialfile='')
        if name:
            conf.set_option('output-dir', s.path.dirname(name))
            self.nameQuality.set(name)

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
        self.nameClass = StringVar()
        self.nameQuality = StringVar()
        
        self.threshold = DoubleVar()
        self.threshold.set(conf.get_option('threshold', numpy.inf))

        row = 0

        # frame 1
        self.frame1 = Frame(self)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(1, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        frow = 0

        Label(self.frame1, text="Input").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameIn).grid(row=frow, column=1, sticky=W+E)
        Button(self.frame1, text='Browse', command=self.pick_input).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(self.frame1, text="Class").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameClass).grid(row=frow, column=1, sticky=W+E)
        Button(self.frame1, text='Browse', command=self.pick_class).grid(row=frow, column=2, sticky=W)

        frow = frow + 1

        Label(self.frame1, text="Quality").grid(row=frow, column=0, sticky=W)
        Entry(self.frame1, textvariable=self.nameQuality).grid(row=frow, column=1, sticky=W+E)
        Button(self.frame1, text='Browse', command=self.pick_quality).grid(row=frow, column=2, sticky=W)

        row = row + 1

        # frame 4
        self.frame4 = Frame(self)
        self.frame4.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame4.columnconfigure(0, weight=1)
        self.frame4.columnconfigure(1, weight=1)
        self.frame4.columnconfigure(2, weight=1)
        self.frame4.rowconfigure(0, weight=1)

        Label(self.frame4, text="Method:").grid(row=0, column=0, sticky=E)
        Radiobutton(self.frame4, variable=self.choice, value='min', text='minimum').grid(row=0, column=1, sticky=W)
        Radiobutton(self.frame4, variable=self.choice, value='max', text='maximum').grid(row=0, column=2, sticky=W)
        self.choice.set(conf.get_option('method', "min"))

##        Label(self.frame4, text="Thresholds: ").grid(row=1, column=0, sticky=E)
##        Button(self.frame4, text='Set all thresholds', command=self.set_all).grid(row=1, column=0, sticky=E)
##        Entry(self.frame4, textvariable=self.threshold, width=6).grid(row=1, column=2, sticky=W)

        row = row + 1

        # frame 5, thresholds
        self.frame5 = Frame(self)
        self.frame5.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame5.columnconfigure(0, weight=1)
        self.frame5.columnconfigure(1, weight=1)
        self.frame5.columnconfigure(2, weight=1)
        self.frame5.rowconfigure(0, weight=1)

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
conf.set_option('threshold', app.threshold.get())

root.destroy()
