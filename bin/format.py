#!/usr/bin/env python

import string
from Stylesheets.Default   import DefaultStylesheet

class MyStyle(DefaultStylesheet):
    
    def __init__(self):
        DefaultStylesheet.__init__(self, 'free')
        self['keywordcase'   ] = 'upper'
        self['variablecase'  ] = 'lower'
        self['contlinemarker'] = '>'
        self["maxcols"       ] = 72
     
# ==============================================================================

if __name__=="__main__":
    import sys
    from Tools.Project import Project

    project = Project()
    ssheet  = MyStyle()
    for i in sys.argv[1:]:
        o = project.oGetObjectForIdentifier(i, "file")
        print ssheet.ToString(o)
    
