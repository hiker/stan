#!/usr/bin/env python

# Stores the information in a Fortran file

import string
from   UserList            import UserList

from   Tools.Error         import FatalError
from   AOR.Subroutine      import Subroutine
from   AOR.Module          import Module
from   AOR.Function        import Function
from   AOR.Blockdata       import Blockdata
from   AOR.BasicStatement  import BasicRepr
from   Stylesheets.f77     import f77
from   Stylesheets.Default import DefaultStylesheet

# The order of base clases is important, because BasicRepr's __repr__ 
# method must be called.
class File(BasicRepr, UserList):

    # Constructor for File object. Parameters:
    #
    # sFilename -- Filename, including path
    #
    # sFormat   -- Format of the file: 'fix' or 'free'
    #
    def __init__(self, sFilename, sFormat):
        # The list stores all information contained in the file
        UserList.__init__(self)
        self.sFilename  = sFilename
        self.sFormat    = sFormat
        self.stylesheet = None
        assert self.sFormat in ["fixed","free"]

    # --------------------------------------------------------------------------
    def sGetFilename(self): return self.sFilename
    
    # --------------------------------------------------------------------------
    def sGetFormat(self): return self.sFormat
    
    # --------------------------------------------------------------------------
    # Returns a string representation of the object, which is suitable for
    # the format in which this file was written (fixed/free).
    def sFormatObject(self, obj, bIgnoreAttributes=0, stylesheet=None):
        if not stylesheet:
            # avoid creating a stylesheet over and over again
            if not self.stylesheet:
                if self.sFormat=="fixed":
                    self.stylesheet=f77()
                else:
                    self.stylesheet=DefaultStylesheet()
            stylesheet=self.stylesheet
        return stylesheet.ToString(obj, bIgnoreAttributes)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        for i in self:
            stylesheet.ToList(i, l)
    # --------------------------------------------------------------------------
    dType2Class = {'subroutine' : Subroutine,
                   'function'   : Function,
                   'module'     : Module,
                   'blockdata'  : Blockdata }
    def GetIdentifier(self, sId, sType):
        c = File.dType2Class.get(sType.lower(),None)
        if not c:
            raise FatalError("Type '%s' undefined in File.bHasIdentifier"%sType)
        s = sId.lower()
        for i in self:
            if isinstance(i,c) and i.sGetName().lower()==s:
                return i
        return None
            
    # --------------------------------------------------------------------------
    # Returns a list of all statements of a certain class. Parameter:
    #
    # class -- Class to which all returned object should belong
    def GetAllProgUnits(self, c):
        return filter(lambda x,c=c: isinstance(x,c), self)
    # --------------------------------------------------------------------------
    # Returns a list of all subroutines
    def GetAllSubroutines(self): return self.GetAllProgUnits(Subroutine)
    # --------------------------------------------------------------------------
    # Returns a list of all funcions
    def GetAllFunctions(self): return self.GetAllProgUnits(Function)
    # --------------------------------------------------------------------------
    # Returns a list of all Program(s)
    def GetAllPrograms(self): return self.GetAllProgUnits(Program)
        
# ==============================================================================
