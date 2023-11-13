#!/usr/bin/python3
import os
import sys
import subprocess

from tkinter import *
##import tkFileDialog

import tkinter.messagebox

import readconfig
import conf

DESCRIPTION = "HypPy3 Hyperspectral Python"

try:
    HYPPYCONFIG = conf.get_option('menu-config-file', 'hyppymenu.cfg')
except Exception as errtext:
    Tk().withdraw()
    tkinter.messagebox.showerror(title='Error', message=errtext)
    raise

PYTHON = sys.executable     # where's Python?
#PDFREADER = 'evince'        # for Linux
PDFREADER = 'xdg-open'        # for Linux

##HORIZONTAL = True           # Toplevel menu structure
##TEAROFF = True              # create menus 'tearoff'able

HORIZONTAL = conf.get_option('horizontal', True, type_=bool)
TEAROFF = conf.get_option('tear-off', True, type_=bool)

# Menu structure
# You can also creat submenus subsubmenus ect.
# Every (sub)menu MUST end with None, '', 0, or (,), except the last one
menustruct = (('Viewers', 'Menu'),
                  ('Display Image', 'tkDisplay2.py'),
                  ('Spectral Library Viewer', 'tkSpecLib.py'),
                  None,
              ('Band Tools', 'Menu'),
                  ('Sort Channels by Wav.', 'tkSortChannels.py'),
                  ('Stack ENVI Images', 'tkMerge.py'),
                  ('Split Bands into JPEGs', 'tkSplit.py'),
                  None,                    
              ('Spectral Tools', 'Menu'),
                  ('Convex Hull Removal', 'tkConvexHull.py'),
                  ('Normalize', 'tkNormalize.py'),
                  ('Kwik Residuals', 'tkLogResiduals.py'),
                  ('Band Ratios', 'tkRatios.py'),
                  ('Band Depths', 'tkSpijkers.py'),
                  ('Wavelength of Minimum', 'tkMinWavelength.py'),
                  None,
              ('Spectral Filters', 'Menu'),
                  ('Spectral Edge Filter', 'tkEdgy.py'),
                  ('Spectral Gradient Filters', 'tkGradient.py'),
                  ('Spectral Median Filter', 'tkMedian.py'),
                  None,
              ('Classification', 'Menu'),
                  ('Spectral Mapper', 'tkSAM.py'),
                  ('Rule Image Classifier', 'tkClassify.py'),
                  None,
              ('Mars Tools', 'Menu'),
                  ('Thermal Correction', 'tkThermalCorrection.py'),
                  ('Solar Correction', 'tkSolarCorrection.py'),
                  ('Summary Products', 'tkSummaryProducts.py'),
                  None,
              ('Help', 'Menu'),
                  ('Manual', 'manual.pdf'),
                  None
              )

def make_command(action):
    '''Trick to remember the action'''
    return lambda: command(action)

def command(action):
    '''Execute menu button command'''
    if action.lower().endswith('.py'):        
##        return os.spawnv(os.P_NOWAIT, PYTHON, [PYTHON, action])
        return subprocess.Popen([PYTHON, action])
    if action.lower().startswith('http://') or action.lower().startswith('https://'):
        if not 'win' in sys.platform:
##            return os.spawnvp(os.P_NOWAIT, PDFREADER, [PDFREADER, thePDF])
            return subprocess.Popen([PDFREADER, action])
        else:  # Good Grief! What's going on???
            return os.startfile(action)
    if action.lower().endswith('.pdf') or action.lower().endswith('.html'):
        thePDF = os.path.join(os.getcwd(), action)
        if not 'win' in sys.platform:
##            return os.spawnvp(os.P_NOWAIT, PDFREADER, [PDFREADER, thePDF])
            return subprocess.Popen([PDFREADER, thePDF])
        else:  # Good Grief! What's going on???
            return os.startfile(thePDF)

class Application(Frame):

    def __init__(self, master=None):
        # call superclass constructor
        Frame.__init__(self, master)
        self.grid()

        # do not allow toplevel to stretch H+V
        top=self.winfo_toplevel()
        top.resizable(False, False)

        # create window contents
        self.makeWindow()

    def read_menu(self, mb):
        '''Creates Menus'''
        menu = Menu(mb, tearoff=TEAROFF)
        try:
            item = self.menu_item.__next__()
            while item:
                name, action = item
                if action.lower()=='menu':
                    menu.add_cascade(label=name, menu=self.read_menu(menu))
                elif action.lower()=='separator':
                    menu.add_separator()
                else:
                    menu.add_command(label=name, command=make_command(action))
                item = self.menu_item.__next__()
        except StopIteration:
            return menu
       
        return menu

    def makeWindow(self):
        '''Set up application window'''
        column = 0
        row = 0

        # Read config file formenu structure
        menustruct_fromconfig = readconfig.read_config(HYPPYCONFIG)
        if menustruct_fromconfig:
            self.menu_item = iter(menustruct_fromconfig)
        else:       
            self.menu_item = iter(menustruct)

        # Create Menubuttons                  
        try:
            item = self.menu_item.__next__()
            while item:
                name, action = item
                mb = Menubutton(self, text=name)
                mb.grid(row=row, column=column, sticky=W)

                mb.menu = self.read_menu(mb)
                mb["menu"] = mb.menu
                if HORIZONTAL:
                    column = column + 1
                else:
                    row = row + 1
                item = self.menu_item.__next__()
        except StopIteration:
            return
        
# create the root
root = Tk()
# create the application
app = Application(root)
# set title
root.title(DESCRIPTION)
# move to upper right corner of the screen
root.geometry('-0+0')
# handle the 'X' button
root.protocol("WM_DELETE_WINDOW", root.quit)
# start event loop
root.mainloop()
# destroy application after event loop ends
root.destroy()

conf.set_option('horizontal', HORIZONTAL)
conf.set_option('tear-off', TEAROFF)
conf.set_option('menu-config-file', HYPPYCONFIG)
