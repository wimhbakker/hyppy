import xml.dom.minidom

class Manifest(object):
    pass

def get_manifest(f):
    doc = xml.dom.minidom.parse(f)
 
    manifest = Manifest()
    for node in doc.getElementsByTagName('file'):
        typ = node.getAttribute('type')
        ext = node.getAttribute('extension')
        dat = node.childNodes[0].data
        if ext=='raw':
            setattr(manifest, typ, dat)

    return manifest

