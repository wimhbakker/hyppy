#!/usr/bin/python3
#
#     tkProgressBar.py
#
#   Created: WHB 20110627
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

import tkinter.font
from tkinter import *

PROGRESSFONT = 'TkDefaultFont'
PROGRESSSIZE = 10
PROGRESSCHAR = '\u2589'
PROGRESSCOLOR = '#2255ff'

class ProgressBar(Frame):
    def __init__(self, master):
        Frame.__init__(self, master)
        self.columnconfigure(0, weight=1)
        self.label = Label(self, bd=1, relief=SUNKEN, anchor=W, font=(PROGRESSFONT,PROGRESSSIZE), foreground=PROGRESSCOLOR)
        self.label.grid(row=0, column=0, sticky=W+E)
        self.charwidth = tkinter.font.Font(font=(PROGRESSFONT,PROGRESSSIZE)).measure(PROGRESSCHAR)
        self.previous = 0

    def __call__(self, progress):
        progress = max(progress, 0.0)
        progress = min(progress, 1.0)
        pixwidth = self.label.winfo_width()
        newsize = int(progress * (pixwidth/self.charwidth))
        if newsize != self.previous:
            self.label.config(text=newsize * PROGRESSCHAR)
            self.previous = newsize
##            # This works for Unix
##            self.label.update_idletasks()
            # This works for wind-OW!-s
            self.label.update()
