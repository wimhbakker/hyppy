#!/usr/bin/python3
#
#     tkWMSget.py
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
from tkinter import *
from tkinter.filedialog import *
import tkinter.messagebox

try:
    import wmsget
    import conf
    import about
except ImportError as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

DESCRIPTION = 'WMS get'

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
        self.message("Out: " + self.nameOut.get())
        self.message("Running, please wait...")
        style = self.style.get() if self.style.get() else None
        try:
            wmsget.wmsget(self.urlWMS.get(), self.layer.get(), self.srs.get(),
                      (self.centerX.get(), self.centerY.get()),
                      self.resolution.get(), self.imformat.get(),
                      (self.sizeX.get(), self.sizeY.get()),
                      self.nameOut.get(), style=style,
                          enviout=self.enviout.get(), message=self.message)
            self.message("Completed!")
        except Exception as err:
            self.message('Exception: %s' % (str(err),))

    def do_exit(self):
        root.quit()

    def pick_input(self):
        self.message("Pick input file.")
        name = askopenfilename(title='Open Input File',
                                   initialdir=r'D:',
                                   initialfile='')
        if name:
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

    def combobox_create(self, frame, text):
        mb = Menubutton(frame, text=text, relief=RAISED)
        mb.menu = Menu(mb, tearoff=0)
        mb["menu"] = mb.menu

        return mb

    def combobox_set(self, mb, options, variable, command):
        mb.menu.delete(0, END)
        variable.set('')
        for option in options:
            mb.menu.add_radiobutton(label=option, value=option,
                                    variable=variable, command=command)

    def connect(self):
        self.wms = wmsget.wms_connect(self.urlWMS.get())
        if not self.wms:
            self.message('Connection failed!')
            return

        self.message('Connected.')
        
        self.combobox_set(self.cb_layer, wmsget.wms_contents(self.wms),
                          self.layer, self.select_layer)

        self.combobox_set(self.cb_imformat, wmsget.wms_formats(self.wms),
                          self.imformat, self.select_imformat)

    def select_layer(self):
        self.message('Layer: %s' % (self.layer.get()))
        self.message('Bounding Box: %s' % (str(wmsget.wms_layer_bbox(self.wms, self.layer.get())),))

        styles = wmsget.wms_layer_styles(self.wms, self.layer.get())
        if styles:
            self.cb_style.configure(state=NORMAL)
            self.combobox_set(self.cb_style, styles,
                              self.style, self.select_style)
        else:
            self.cb_style.configure(state=DISABLED)
            self.message('Layer has no styles defined')

        self.combobox_set(self.cb_srs, wmsget.wms_layer_refs(self.wms, self.layer.get()),
                          self.srs, self.select_srs)

    def select_style(self):
        self.message('Style: %s' % (self.style.get()))

    def select_srs(self):
        self.message('SRS: %s' % (self.srs.get()))

    def select_imformat(self):
        self.message('Format: %s' % (self.imformat.get()))

    def makeWindow(self):
        # variables
        self.urlWMS = StringVar()
        url = conf.get_option('url-wms')
        if url:
            self.urlWMS.set(url)
        
        self.layer = StringVar()
        self.style = StringVar()
        self.srs = StringVar()
        self.imformat = StringVar()

        self.centerX = DoubleVar()
        self.centerY = DoubleVar()
        self.sizeX = IntVar()
        self.sizeY = IntVar()
        self.resolution = DoubleVar()
        
        self.nameOut = StringVar()
        self.enviout = IntVar()
        self.enviout.set(conf.get_option('envi-out', 0))

        row = 0

        # frame
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="WMS").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.urlWMS, width=30).grid(row=0, column=1, sticky=W+E)

        row = row + 1

        # frame: connect, layer, imformat, style, srs
        self.frame1 = Frame(self, bd=1, relief=GROOVE)
        self.frame1.grid(row=row, column=0, sticky=N+E+S+W)
        self.frame1.columnconfigure(0, weight=1)
        self.frame1.rowconfigure(0, weight=1)

        Button(self.frame1, text="Connect", command=self.connect).grid(row=0, column=0, sticky=W+E)
        
        self.cb_layer = self.combobox_create(self.frame1, "Select Layer")
        self.cb_layer.grid(row=1, column=0, sticky=W+E)

        self.cb_imformat = self.combobox_create(self.frame1, "Select Image Format")
        self.cb_imformat.grid(row=2, column=0, sticky=W+E)

        self.cb_style = self.combobox_create(self.frame1, "Select Style")
        self.cb_style.grid(row=3, column=0, sticky=W+E)

        self.cb_srs = self.combobox_create(self.frame1, "Select Spatial Reference")
        self.cb_srs.grid(row=4, column=0, sticky=W+E)

        row = row + 1

        # frame: coordinates, center, size, resolution
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(0, weight=1)

        frow = 0

        Label(frame, text="Center coord.").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.centerX, width=10).grid(row=frow, column=1, sticky=W+E)
        Entry(frame, textvariable=self.centerY, width=10).grid(row=frow, column=2, sticky=W+E)
        self.centerX.set(conf.get_option('center-x', '0'))
        self.centerY.set(conf.get_option('center-y', '0'))

        frow += 1

        Label(frame, text="Size (pixels)").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.sizeX, width=10).grid(row=frow, column=1, sticky=W+E)
        Entry(frame, textvariable=self.sizeY, width=10).grid(row=frow, column=2, sticky=W+E)
        self.sizeX.set(conf.get_option('size-x', 1000))
        self.sizeY.set(conf.get_option('size-y', 1000))

        frow += 1

        Label(frame, text="Resolution").grid(row=frow, column=0, sticky=W)
        Entry(frame, textvariable=self.resolution, width=10).grid(row=frow, column=1, sticky=W+E)
        Label(frame, text="[units]").grid(row=frow, column=2, sticky=W)
        self.resolution.set(conf.get_option('resolution', 1.0))

        row = row + 1

        # frame: output
        frame = Frame(self, bd=1, relief=GROOVE)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)

        Label(frame, text="Output").grid(row=0, column=0, sticky=W)
        Entry(frame, textvariable=self.nameOut).grid(row=0, column=1, sticky=W+E)
        Button(frame, text='...', command=self.pick_output).grid(row=0, column=2, sticky=W)

        Checkbutton(frame, text='also generate ENVI image', variable=self.enviout).grid(row=1, column=1, sticky=W)

        row = row + 1

        # frame 2
        frame = Frame(self)
        frame.grid(row=row, column=0, sticky=N+E+S+W)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        
        Button(frame,text="Run",command=self.do_run).grid(row=0, column=0, sticky=W+E)
        Button(frame,text="Exit",command=self.do_exit).grid(row=0, column=1, sticky=W+E)

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
        self.rowconfigure(5, weight=1)


root = Tk()
app = Application(root)
root.title(DESCRIPTION)
# handle the X button
root.protocol("WM_DELETE_WINDOW", root.quit)
root.mainloop()

conf.set_option('url-wms', app.urlWMS.get())

conf.set_option('center-x', app.centerX.get())
conf.set_option('center-y', app.centerY.get())
conf.set_option('size-x', app.sizeX.get())
conf.set_option('size-y', app.sizeY.get())
conf.set_option('resolution', app.resolution.get())

conf.set_option('envi-out', app.enviout.get())

root.destroy()
