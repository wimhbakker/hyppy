#!/usr/bin/python3
## opus4.py
##
## Copyright (C) 2010 Wim Bakker
##
##  modified: 20130205 WHB, added two headers new in Opus version 7.0
##  modified: 20140127 WHB, bug-fix for length of record and NPT in record
##  modified: 20151120 WHB, bug-fix for splitting bytes etc.
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

from struct import unpack
from numpy import array

# Tag data type
tdict = {0:'h', 1:'f', 2:'s', 3:'bool', 4:'code?'}

# Index Table bytes
byte1 = {96:'Optical parameters',
         64:'FT parameters',
         48:'Acquisition parameters',
         160:'Sample parameters',
         7:'Sm',
         23:'Sm', #header
         0:'short header', #header
         15:'', #Refl
         40:'Instrument parameters Rf',
         104:'Optical parameters Rf',
         11:'Rf',
         27:'Rf', #header
         31:'', #Refl header
         32:'Instrument parameters',
         56:'Acquisition parameters Rf', # header new in Opus version 7.0
         72:'FT parameters Rf' # header new in Opus version 7.0
         }

byte2 = {0:'',
         4:'Sc',
         8:'Ig',
         12:'Ph',
         16:'AB',
         20:'TR',
         48:'Refl'}

byte3 = {0:'',
         104:'(flag104)'}

byte4 = {0:'',
         64:'(flag64)'}

# Class OPUSheader
class OPUSheader:
    def __init__(self, info, data):
        self.taglist = []
        self.info = info
        self.get_header(data)

    def __repr__(self):
        result = 'Description: ' + self.info + '\n'
        for tag in self.taglist:
            result = result + tag + ': ' + str(getattr(self, tag)) + '\n'
        return result

    def __str__(self):
        return self.__repr__()

    def add_tag(self, tag, value):
        setattr(self, tag, value)
        self.taglist.append(tag)

    def get_tag_data(self, t, l, data):
        if l:
            if t==0: # short
                (d,) = unpack('h', data[:2])
                return d
            elif t==1: # double
                (d,) = unpack('d', data[:8])
                return d
            elif t in [2, 3, 4]: # string / mode / code
                d = data[:2*l].split(b'\0')[0]
                return d.decode()
            else:
                print("UNKNOWN TAG TYPE: %d" % (t,))
                return None
        else:
            return None

    def get_tag(self, data):
        (a, b, c, d, t, l) = unpack('cccchh', data[:8])
##        tag = '%s%s%s' % (a, b, c)
        tag = (a + b + c).decode()
        taglen = 8+l*2
        value = self.get_tag_data(t, l, data[8:])
        return tag, taglen, value

    def get_header(self, data):
        i = 0
        while i<len(data):
            tag, taglen, value = self.get_tag(data[i:])
            self.add_tag(tag, value)
            i = i + taglen
            if tag == 'END':
                break

    def xvalues(header):
        delta = (header.LXV-header.FXV)/(header.NPT-1)
        return array([header.FXV + x * delta for x in range(header.NPT)])

    def yscale(header):
        if hasattr(header, 'CSF'):
            return header.CSF
        else:
            return 1.0

def message(s):
    print(s)

def silent(s):
    pass

def get_index_table(data):
    itable = []

    magic, w2, w3, w4, w5, itablen, w7, w8, w9 = unpack('9I', data[:36])

    if magic not in [4278061578]:
        raise ValueError('bad magic %d' % (magic,))
    
    i = 36
    isdata = False
    oldinfo = ''
    while itablen>0:
        b1, b2, b3, b4, lng, idx = unpack('BBBBii', data[i:i+12])
        info = byte2[b2] + byte1[b1]
        if idx == 0:
            break
        if b1==0 and b2==0:
            typ = 'HISTORY'
            isdata = False
        elif b2==0 or b1 in [23, 31, 27, 56, 72, 0]:
            typ = 'HEADER'
            isdata = False
            if b1==0:
                info = oldinfo
        else:
            typ = 'DATA'
            isdata = True
            oldinfo = info
            
        itable.append((idx, 4*lng, typ, info))
        i = i + 12
        itablen = itablen - 1

    return itable

def get_data(data):
    thedata = unpack('<%df'%(len(data)//4,), data)
    return thedata

def get_opus(fname, message=message):
    f = open(fname, 'rb')
    data = f.read()
    f.close()

    message("========== Header Index Table ==========")
    itable = get_index_table(data)
    message(itable)
    message('\n')

    message("Retrieving Headers & Data")
    datasources = []
    for i in range(len(itable)):
        idx, lng, typ, info = itable[i]
        if typ=='HISTORY':
            message("\n========== Index: %d, HISTORY: %d bytes ==========" % (idx, lng))
            message(data[idx:idx+lng])
        elif typ=='HEADER':
            message('\n========== Index: %d, HEADER: %s ==========' % (idx, info))
            header = OPUSheader(info, data[idx:idx+lng])
            message(str(header))
##            if info=='ScRf':
##                message(data[idx:idx+lng])
        elif typ=='DATA':
            message("\n========== Index: %d, DATA: %s (%d bytes) ==========" % (idx, info, lng))
            ds = get_data(data[idx:idx+lng])
            message(ds[:10])
            datasources.append(ds)

    return datasources

def get_opus_data(fname, datatype, message=message):
    f = open(fname, 'rb')
    data = f.read()
    f.close()

    message("========== Header Index Table ==========")
    itable = get_index_table(data)
    message(itable)
    message('\n')

    message("Retrieving Headers & Data")
    datasource = None
    header = None
    for i in range(len(itable)):
        idx, lng, typ, info = itable[i]
        if typ=='HISTORY':
            message("\n========== Index: %d, HISTORY: %d bytes ==========" % (idx, lng))
            message(data[idx:idx+lng])
        elif typ=='HEADER':
            message('\n========== Index: %d, HEADER: %s ==========' % (idx, info))
            h = OPUSheader(info, data[idx:idx+lng])
            message(str(h))
            if info == datatype:
                header = h
        elif typ=='DATA':
            message("\n========== Index: %d, DATA: %s (%d bytes) ==========" % (idx, info, lng))
            ds = get_data(data[idx:idx+lng])
            message(ds[:10])
            if info == datatype:
                datasource = ds

    # sometimes the length of the record does not correspond with the
    # number of points in the record?
    if datasource and (len(datasource) != header.NPT):
        datasource = datasource[:header.NPT]
        
    return datasource, header


################################ MAIN program ###############################
if __name__ == '__main__':
#    fname = 'mindertroep_opus/test30_empty_wet_a.0'
#    fname = 'mindertroep_opus/test30_SiC_wet_a.0'
#    fname = 'testfiles/Alunite1_Globar_KBr.0'
#    fname = 'testfiles/Micasheet.0'
    fname = 'testfiles/Prehnite_powder.0'
    
    datasources = get_opus(fname)

    # Plotting Reflectance spectrum
    from pylab import *

##    for i in range(len(datasources)):
##        figure(i)
##        plot(datasources[i])


# Get one dataset from OPUS file
    data, header = get_opus_data(fname, 'TR', message=silent)
    print("Number of points:", header.NPT)
    print("First X:", header.FXV)
    print("Last X:", header.LXV)
    print("Scale factor Y", header.CSF)
    x = header.xvalues()
    x = 10000.0 / x
    
    plot(x, array(data) * header.CSF)
