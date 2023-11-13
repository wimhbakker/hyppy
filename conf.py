#!/usr/bin/python3
#
#     conf.py
#
##   	Created:  WHB ???
##	Modified: WHB 20150929, set value must be string
##
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

import configparser as cp
import os
import sys

# name of the config file
CONFIGFILE = os.path.expanduser('~/hyppy.cfg')

# section name is constructed from the basename of the calling script
SECTION = os.path.basename(sys.argv[0])

def create_config_file():
    '''Create a fresh config file with a few defaults'''
    if not os.path.exists(CONFIGFILE):
        homedir = os.path.expanduser('~')
        default = {}
        default['input-dir'] = homedir
        default['output-dir'] = homedir
        config = cp.ConfigParser(default)
        config.write(open(CONFIGFILE, 'w'))

def remove_config_file():
    os.remove(CONFIGFILE)

def get_option(option, default=None, type_=str):
    create_config_file()
    config = cp.ConfigParser()
    config.read([CONFIGFILE])
    getdict = {str:config.get, bool:config.getboolean, float:config.getfloat,
               int:config.getint, list:lambda s, o: eval(config.get(s, o))}
    if config.has_section(SECTION) and config.has_option(SECTION, option):
        return getdict[type_](SECTION, option)
    elif config.has_option('DEFAULT', option):
        return getdict[type_]('DEFAULT', option)
    elif default is not None:
        return default
    else:
        return None
        
def set_option(option, value):
    create_config_file()
    config = cp.ConfigParser()
    config.read([CONFIGFILE])
    if not config.has_section(SECTION):
        config.add_section(SECTION)
    config.set(SECTION, option, str(value))
    config.write(open(CONFIGFILE, 'w'))
