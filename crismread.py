import os
##from pylab import *

keylist = ['FILE_RECORDS', 'LABEL_RECORDS', 'COLUMN_NUMBER', 'NAME', 'UNIT',
           'OBJECT']

def value_grok(v):
    if '"' in v:
        return v[1:-1]
    elif '.' in v:
        try:
            return float(v)
        except:
            return v
    else:
        try:
            return int(v)
        except:
            return v

def crism_read_spectrum(fname):
    f = open(fname)
    data = f.readlines()
    f.close()

    if 'PDS' not in data[0]:
        raise ValueError('not a CRISM file?')
    
    d = dict()
    i = 0
    while i < len(data):
        line = data[i]
        line = line.strip()
        if line == 'END':
            break
        elif '=' in line:
            key, val = line.split('=', 1)
            key = key.strip()
            while val.count('"')==1: # multi-line string?
                i = i + 1
                val = val + data[i]
            val = value_grok(val.strip())
            if key=='END_OBJECT':
                if d.get('OBJECT')=='COLUMN':
                    d[d['NAME']] = d['COLUMN_NUMBER']
            elif key in keylist or key.startswith('MRO'):
                d[key] = val
        i = i + 1

    data = data[d['LABEL_RECORDS']+1:]
    w = []
    r = []
    wi = d['WAVELENGTH'] - 1

    # Good Grief! How many ways are there to spell 'reflectance'? Right!
    if 'ABSOLUTE REFLECTANCE' in d:
        ri = d['ABSOLUTE REFLECTANCE'] - 1
    elif 'ABSOLUTE REFLECTIVITY' in d:
        ri = d['ABSOLUTE REFLECTIVITY'] - 1
    elif 'ABSOLUTE' in d:
        ri = d['ABSOLUTE'] - 1
    elif 'REFLECTANCE' in d:
        ri = d['REFLECTANCE'] - 1
    else:
        raise ValueError('reflectance column not found')

    for line in data:
        vals = line.strip().split(',')
        w.append(float(vals[wi].strip()))
        r.append(float(vals[ri].strip()))

    if len(w)!=(d['FILE_RECORDS']-(d['LABEL_RECORDS']+1)):
        raise ValueError('incorrect number of data records')

    # construct a description
    desc1 = d['MRO:SPECIMEN_CLASS_NAME']
    desc2 = d['MRO:SPECIMEN_DESC']

    if desc1=='':
        desc = desc2
    elif desc2=='':
        desc = desc1
    else:
        desc = desc1 + ', ' + desc2

    return w, r, desc

def do_dir(p):
    for f in os.listdir(p):
        fullname = os.path.join(p, f)
        if os.path.isdir(fullname):
            do_dir(fullname)
        elif os.path.isfile(fullname) and fullname.endswith('.tab'):
            print(fullname)
            w, r, desc = crism_read_spectrum(fullname)
            print(desc)
##            plot(w, r)

if __name__ == "__main__":
    do_dir('/home/bakker/CRISMspeclib')
   
