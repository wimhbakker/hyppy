#!/usr/bin/python3
## decisiontree.py
##
## Copyright (C) 2018 Wim Bakker
##      Created: WHB 20181002
##      Modifeid: WHB 20190322, added lowercase ENVI keywords...
##      Modified: WHB 20240326, copy coordinates to output header...
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

import sys
import os
from functools import reduce

import envi2
import envi2.constants

idldict = {'GE':'>=', 'GT':'>', 'LE':'<=', 'LT':'<', 'EQ':'==', 'NE':'!=',
           'AND':'and', 'OR':'or', 'NOT':'not',
           'ge':'>=', 'gt':'>', 'le':'<=', 'lt':'<', 'eq':'==', 'ne':'!=',
           'and':'and', 'or':'or', 'not':'not'}

idldictarray = {'GE':'>=', 'GT':'>', 'LE':'<=', 'LT':'<', 'EQ':'==', 'NE':'!=',
                'AND':'&', 'OR':'|', 'NOT':'~',
                'ge':'>=', 'gt':'>', 'le':'<=', 'lt':'<', 'eq':'==', 'ne':'!=',
                'and':'&', 'or':'|', 'not':'~'}

#NUMVARIABLES = 9
NUMVARIABLES = 300

DEBUG = False

INDENT = 4 * ' '

def idl2python(expr):
    return ' '.join([idldict.get(e, e) for e in expr.split()])

def idl2numpy(expr):
    return ' '.join([idldictarray.get(e, e) for e in expr.split()])

class Node(object):
    def searchbylocation(self, level, position):
        if self.level==level and self.position==position:
            return self
        else:
            if hasattr(self, 'Yes'):
                node = self.Yes.searchbylocation(level, position)
                if node: return node
            if hasattr(self, 'No'):
                node = self.No.searchbylocation(level, position)
                if node: return node
        return None

    def __str__(self):
        s = "(%s, %s, %s, %s)" % (self.name, self.type, self.location, getattr(self, 'parent_name', '<none>'))
        return s

    def addnode(self, node):
        if hasattr(node, 'parent_name'):
            # parent should be one level up, and have half the position...
            parent = self.searchbylocation(node.level-1, (node.position+1)//2)
            setattr(parent, node.parent_decision, node)

    def tree_expression(self):
        if self.type=='Result':
            return self.class_value
        elif self.type=='Decision':
            s = '('
            if hasattr(self, 'Yes'):
                s = s + self.Yes.tree_expression()

            s = s + ' if %s else ' % ((idl2python(self.expression)),)
                
            if hasattr(self, 'No'):
                s = s + self.No.tree_expression()
            s = s + ')'
            return s
        else:
            raise ValueError('Unrecognized type: %s' % (self.type,))

#    def getclasses(self, d=list()):
    def getclasses(self, d=None):
        if d is None:
            d = list()
        if self.type=='Result':
            d.append((int(self.class_value), tuple(map(int, self.class_rgb.split(','))), self.name))
        elif self.type=='Decision':
            if hasattr(self, 'Yes'):
                self.Yes.getclasses(d)
            if hasattr(self, 'No'):
                self.No.getclasses(d)
        else:
            raise ValueError('Unrecognized type: %s' % (self.type,))
        return d

    def ifftree(self):
        if self.type=='Result':
            return self.class_value
        elif self.type=='Decision':
            s = 'iff('
            s = s + idl2numpy(self.expression)
            s = s + ', '
            if hasattr(self, 'Yes'):
                s = s + self.Yes.ifftree()
            s = s + ', '
            if hasattr(self, 'No'):
                s = s + self.No.ifftree()
            s = s + ')'
            return s
        else:
            raise ValueError('Unrecognized type: %s' % (self.type,))

    # print the tree depth first
    def printtree(self, level=0, file=sys.stdout):
        if self.type=='Result':
            print(level * INDENT + "class " + self.class_value + " \"" + self.name + "\" (" + self.class_rgb + ")", file=file)
        elif self.type=='Decision':
            if hasattr(self, 'Yes'):
                self.Yes.printtree(level+1, file=file)

            print(level * INDENT + "if " + idl2numpy(self.expression), file=file)

            if hasattr(self, 'No'):
                self.No.printtree(level+1, file=file)
        else:
            raise ValueError('Unrecognized type: %s' % (self.type,))

    # print the tree depth first to a DOT graph (see Graphviz)
    def dottree(self, level=0, file=sys.stdout):
        if level==0:
            print("digraph G {", file=file)
            
        if self.type=='Result':
            print("    %d [label=\"%s %s\",color=\"%s\",penwidth=\"4.0\"];" % (id(self), self.class_value, self.name, triplet2hex(self.class_rgb)), file=file)
        elif self.type=='Decision':
            if hasattr(self, 'No'):
                print("    %d -> %d [label=no];" % (id(self), id(self.No)), file=file)
                self.No.dottree(level+1, file=file)
            if hasattr(self, 'Yes'):
                print("    %d -> %d [label=yes];" % (id(self), id(self.Yes)), file=file)
                self.Yes.dottree(level+1, file=file)
            print("    %d [label=\"%s\",shape=box];" % (id(self), idl2numpy(self.expression)), file=file)
        else:
            raise ValueError('Unrecognized type: %s' % (self.type,))
        
        if level==0:
            print("}", file=file)

def triplet2hex(s):
    return "#%06X" % reduce(lambda x,y:x*256+y, map(int, s.split(',')))
           
## ENVI tree factory functions

def readnode(f):
    line = f.readline().strip()
    while not line == 'begin node':
        line = f.readline().strip()
        if not line: return None
    line = f.readline().strip()
    n = Node()
    while line != 'end node':
        key, value = [x.strip() for x in line.split('=')]
        key = key.translate(''.maketrans(' ', '_'))
        value = value.strip('"')
        setattr(n, key, value)
        if key=='location':
            n.level, n.position = map(int, value.split(','))
        line = f.readline().strip()
        
    return n

def readtree(f):
    line = f.readline().strip()
    if not line.startswith('ENVI Decision Tree'):
        raise ValueError('Not an ENVI Decision Tree')

    root = readnode(f)
    n = readnode(f)
    while n:
        if DEBUG:
            print('Adding node:', n)
        root.addnode(n)
        n = readnode(f)
    
    return root

### END ENVI TREE ###

### ASCII TREE factory functions ###

def starting_spaces(s):
    return len(s)-len(s.lstrip(' '))

def makenode(line):
    if DEBUG:
        print(line, end='')
    node = Node()
    line = line.strip()
    if line.startswith('if'):
        node.type = 'Decision'
        node.expression = line[3:]
        if DEBUG:
            print(node.type, node.expression)
    elif line.startswith('class'):
        node.type = 'Result'
        node.name = line.split('"')[1]
        node.class_value = line.split()[1]
        node.class_rgb = line.split()[-1].strip('()')
        if DEBUG:
            print(node.type, node.class_value, node.name, node.class_rgb)
    else:
        raise ValueError('Unknown node type %s' % (line,))
    return node

def maketree(lines, level=0):
    if lines:
        for i, line in enumerate(lines):
            if starting_spaces(line) == len(level * INDENT):
                root     = makenode(line)
                root.Yes = maketree(lines[:i],  level+1)
                root.No  = maketree(lines[i+1:], level+1)
                return root
        raise ValueError('Missing (sub)tree at level %d' % (level,))

def remove_empty(lines):
    remove = list()
    for i, line in enumerate(lines):
        s = line.strip()
        if len(s)==0 or s[0]=='#' or s[0]==';': # find empty lines and comment
            remove.append(i)
    for i in reversed(remove):
        s = lines.pop(i)           # remove these lines, backwards
        if DEBUG:
            print('Removing line:', i, s)

def opentree(fname):
    f = open(fname, 'r')
    lines = f.readlines()
    f.close()
    remove_empty(lines)
    return maketree(lines)

### END ASCII TREE ###

### CONVERSION ###

def converttree(intree, outtree, dot=False):
    try:
        f = open(intree, 'r')
        root = readtree(f) # ENVI tree
        f.close()
    except ValueError:
        root = opentree(intree) # ASCII tree

    f = open(outtree, 'w')
    if dot:
        root.dottree(file=f)
    else:
        root.printtree(file=f)
    f.close()

### END CONVERSION ###

# if condition C true then A else B
# numpy version, should work on arrays
def iff(C, A, B):
    return C * A + (~C) * B

def dotree(tree, variables, output):
    try:
        f = open(tree, 'r')
        root = readtree(f) # ENVI tree
        f.close()
    except ValueError:
        root = opentree(tree) # ASCII tree
    
    exp = root.ifftree()

    classes = root.getclasses()

    class_values, class_rgbs, class_names = list(zip(*sorted(classes)))

    number_of_classes = max(class_values) + 1

    if DEBUG:
        print(exp)
        print(variables)
        print(output)
        print(classes)
        print(class_values)
        print(class_rgbs)
        print(class_names)

    image = dict()
    band = dict()
    spectra_names = None
    geo_points = None
    map_info = None
    projection_info = None
    for variable in variables:
        im = envi2.Open(variables[variable][0]) # open image
        image[variable] = im
        samples = im.samples
        lines = im.lines
        if spectra_names is None and hasattr(im.header, 'spectra_names'):
            spectra_names = im.header.spectra_names
        band[variable] = int(variables[variable][1])
        # copy coordinates...
        if geo_points is None and hasattr(im.header, 'geo_points'):
            geo_points = im.header.geo_points
        if map_info is None and hasattr(im.header, 'map_info'):
            map_info = im.header.map_info
        if projection_info is None and hasattr(im.header, 'projection_info'):
            projection_info = im.header.projection_info

    if DEBUG:
        print(samples, lines)

    class_lookup = number_of_classes * [0, 0, 0] 
    envi_class_names = number_of_classes * ['Unclassified']
    for class_value, class_rgb, class_name in sorted(classes):
        class_lookup[3*class_value+0] = class_rgb[0]
        class_lookup[3*class_value+1] = class_rgb[1]
        class_lookup[3*class_value+2] = class_rgb[2]
        envi_class_names[class_value] = class_name

    if DEBUG:
        print(class_lookup)
        print(envi_class_names)

    imout = envi2.New(output, samples=samples, lines=lines,
                      file_type=envi2.constants.ENVI_Classification,
                      classes=number_of_classes,
                      class_lookup=class_lookup,
                      class_names=envi_class_names,
                      band_names=None,
                      spectra_names=spectra_names,
                      bands=1,
                      data_type='u1',
                      byte_order=0,
                      geo_ponts=geo_points,
                      map_info=map_info,
                      projection_info=projection_info)

    for variable in variables:
        locals()[variable] = image[variable][band[variable]]
#    print(exp)
    imout[:, :] = eval(exp)

#### SLOW version
##def dotree_slow(tree, variables, output):
##    f = open(tree, 'r')
##    root = readtree(f)
##    f.close()
##    
##    exp = root.tree_expression()
##
##    classes = root.getclasses()
##
##    class_values, class_rgbs, class_names = list(zip(*sorted(classes)))
##
##    number_of_classes = max(class_values) + 1
##
##    if DEBUG:
##        print(exp)
##        print(variables)
##        print(output)
##        print(classes)
##        print(class_values)
##        print(class_rgbs)
##        print(class_names)
##
##    image = dict()
##    band = dict()
##    for variable in variables:
##        im = envi2.Open(variables[variable][0]) # open image
##        image[variable] = im
##        samples = im.samples
##        lines = im.lines
##        band[variable] = int(variables[variable][1])
##
##    if DEBUG:
##        print(samples, lines)
##
##    class_lookup = number_of_classes * [0, 0, 0] 
##    envi_class_names = number_of_classes * ['Unclassified']
##    for class_value, class_rgb, class_name in sorted(classes):
##        class_lookup[3*class_value+0] = class_rgb[0]
##        class_lookup[3*class_value+1] = class_rgb[1]
##        class_lookup[3*class_value+2] = class_rgb[2]
##        envi_class_names[class_value] = class_name
##
##    if DEBUG:
##        print(class_lookup)
##        print(envi_class_names)
##
##    imout = envi2.New(output, samples=samples, lines=lines,
##                    file_type=envi2.constants.ENVI_Classification,
##                    classes=number_of_classes,
##                    class_lookup=class_lookup,
##                    class_names=envi_class_names,
##                    band_names=None,
##                    bands=1,
##                       data_type='u1',
##                       byte_order=0)
##
##    for y in range(lines):
##        for x in range(samples):
##            for variable in variables:
##                locals()[variable] = image[variable][y, x, band[variable]]
##            imout[y, x] = eval(exp)

if __name__=='__main__':
    # command line version
    import argparse
#    import os

    parser = argparse.ArgumentParser(prog='decisiontree.py',
        description='Execute ENVI Decision Tree')

    parser.add_argument('-t', dest='tree', help='input ENVI decision tree', required=True)
    parser.add_argument('-o', dest='output', help='output image file name', required=True)
    for i in range(1, NUMVARIABLES + 1):
        parser.add_argument('-b%d'%(i,), nargs=2, help='variable b%d'%(i,), metavar=('image', 'band'))

    options = parser.parse_args()

    variables = dict() # pack variables into dict...
    for i in range(1, NUMVARIABLES + 1):
        name = 'b%d'%(i,)
        value = getattr(options, name)
        if value:
            variables[name] = value

    dotree(options.tree, variables, options.output)
