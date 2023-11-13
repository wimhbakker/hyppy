########################################################################
#
# envilist.py
#
#   Modified WHB 20090513, refactoring
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


def find_matching_bracket(s, start=0):
    i = start
    c = 0
    while True:
        if s[i] == '{':
            c = c + 1
        elif s[i] == '}':
            c = c - 1
        if c == 0:
            return i
        i = i + 1

def to_python_list(s):
    result = []
    s = s.strip()   # strip whitespace
    s = s[1:-1]     # strip { and }
    s = s.strip()
    while s:
        s = s.strip()
        if s[0] == '{':
            m = find_matching_bracket(s)
            result.append(to_python_list(s[:m+1]))
            # skip beyond the matching '}'
            s = s[m+1:].strip()
            if s and s[0] == ',':
                s = s[1:]
        else:
            a = s.find(',')
            if a == -1:
                elem = s
                s = ''
            elif a == 0:
                elem = ''
                s = s[1:]
            else:
                elem = s.split(',', 1)[0]
                s = s[a + 1:]
            try:
                result.append(int(elem))
            except:
                try:
                    result.append(float(elem))
                except:
                    result.append(elem)
    return result

def to_envi_list(l):
    result = '{'
    i = 0
    for i in range(len(l)):
        elem = l[i]
        if type(elem) == list:
            selem = to_envi_list(elem)
        elif type(elem) == str:
            selem = elem
        elif type(elem) == float:
            selem = str(elem)
        elif type(elem) == int:
            selem = str(elem)
        else:
            selem = str(elem)
##            print type(elem)
##            raise ValueError
        if i < len(l)-1:
            result = result + selem + ','
        else:
            result = result + selem
    result = result + '}'
    return result


if __name__ == '__main__':
    # for testing
    s='{1,2,3,{4,5,6,{8,9,10},11,12},13,{14,15},16}'
    print(s)
    l = to_python_list(s)
    print(l)
    print(to_envi_list(l))
    print()

    s='{1,2,3,{4,5,6,{8.,9,10},11,12},13,{14,15},16}'
    print(s)
    l = to_python_list(s)
    print(l)
    print(to_envi_list(l))
    print()


    s='{1,2,3,{4,5,6,{8.0,9,10},hello world,12},13,{14,15},16}'
    print(s)
    l = to_python_list(s)
    print(l)
    print(to_envi_list(l))
    print()


    s='{1,2,3,{4,5,6,{8.0,9,10},hello world,,,,12},13,{14,15},16}'
    print(s)
    l = to_python_list(s)
    print(l)
    print(to_envi_list(l))
    print()

    s='{ }'
    print(s)
    l = to_python_list(s)
    print(l)
    print(to_envi_list(l))
    print()

    s='{{}, {    }, {{{}}}}'
    print(s)
    l = to_python_list(s)
    print(l)
    print(to_envi_list(l))
    print()

