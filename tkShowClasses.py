#!/usr/bin/python3
#
#     tkShowClasses.py
#
#   Created: WHB 20230104
#   Modified: ...
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
from tkinter.colorchooser import askcolor
import tkinter.messagebox

try:
    import conf
    import about
    import envi2
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = "Show Classes"

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

    def do_exit(self):
        root.quit()

    def pick_input(self):
        idir = conf.get_option('input-dir')
        name = askopenfilename(title='Open Classification Image',
                                   initialdir=idir,
                                   initialfile='')
        if name:
            conf.set_option('input-dir', os.path.dirname(name))
            self.nameIn.set(name)

            # set up thresholds...
            for widgets in self.frame5.winfo_children():
                widgets.destroy()
            self.frame5['height'] = 1 # force frame5 to resize...
            
            try:
                im = envi2.Open(name)
            except:
                tkinter.messagebox.showerror(title='IOError', message='No Image Found')
                return

            if hasattr(im.header, 'file_type') and im.header.file_type == envi2.ENVI_Classification:
                a = im.header.class_lookup
                class_lookup = list(zip(a[::3], a[1::3], a[2::3]))
                brightness = [sum(t) // 3 for t in class_lookup]
                class_lookup = colors_rgb_to_hex(class_lookup)

                class_names = im.header.class_names
            
                self.buttonlist = list()

                row = 0
                for i, class_name in enumerate(class_names):
                    but = Button(self.frame5, text=class_name, bg=class_lookup[i],
                                 fg='#000000' if brightness[i] > 127 else '#ffffff')
                    but['command'] = self.color_picker_func(but, class_lookup[i])
                    but.grid(row=row, column=0, sticky=E+W)
                    self.buttonlist.append(but)
                    
                    row = row + 1
            else:
                tkinter.messagebox.showerror(title='IOError', message='No Classes Found')

    def color_picker_func(self, but, col):
        def color_picker():
            color = askcolor(color=col, title="Class color picker")[1]
            if color:
                but['bg'] = color
                brightness = sum(color_hex_to_rgb(color)) // 3
                but['fg'] = '#000000' if brightness > 127 else '#ffffff'
        return color_picker

    def makeWindow(self):
        # variables
        self.nameIn = StringVar()

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

        row = row + 1

        # frame 5, thresholds
        self.frame5 = Frame(self)
        self.frame5.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame5.columnconfigure(0, weight=1)
        self.frame5.rowconfigure(0, weight=1)

        row = row + 1

        # allow column=... and row=... to stretch
        self.columnconfigure(0, weight=1)
        self.rowconfigure(row, weight=1)

root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

root.destroy()
