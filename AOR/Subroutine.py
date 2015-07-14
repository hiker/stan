#!/usr/bin/env python

import string
from   AOR.ProgUnit       import ProgUnit
from   AOR.BasicStatement import BasicStatement
from   AOR.DoubleList     import DoubleList

class Subroutine(ProgUnit):
    # Constructor for a subroutine object. Parameter:
    #
    # sSubName -- Name of function
    #
    def __init__(self, subStatement=None):
        ProgUnit.__init__(self, subStatement)
    
# ==============================================================================
class SubroutineStatement(BasicStatement):
    def __init__(self, loc=None, lPrefix=[], sSub="SUBROUTINE", sName="",
                 nIndent=0, oSub = None):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.lPrefix     = lPrefix
        self.sSub        = sSub
        self.sName       = sName
        self.lArgs       = DoubleList()
        self.sParOpen    = None
        self.sParClose   = None
        self.oSub        = oSub
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen): self.sParOpen = sParOpen
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def GetName(self): return self.sName
    # --------------------------------------------------------------------------
    def GetPrefix(self): return self.lPrefix
    # --------------------------------------------------------------------------
    def GetArguments(self): return self.lArgs.GetMainList()
    # --------------------------------------------------------------------------
    def AddArgument(self, sName, sComma=None, d=None):
        if self.sParOpen==None: self.sParOpen="("
        self.sParClose = ")"
        if sComma==None and \
               len(self.lArgs.lGetSecondaryList())==len(self.lArgs)-1:
            self.lArgs.append(",", sName)
        else:
            self.lArgs.append(sName, sComma)
            
        if self.oSub:
            self.oSub.AddArgument(sName, sComma=sComma, d=d)
            
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        for i in self.lPrefix:
            l.append(stylesheet.sKeyword(i), nIndentNext=1)
        l.append(stylesheet.sKeyword(self.sSub), nIndentNext=1)
        l.append(self.sName)
        if not self.sParOpen:
            return 
        l.append(self.sParOpen)
        self.lArgs.ToList(stylesheet, l)
        l.append(self.sParClose)
                 
    # --------------------------------------------------------------------------
  
     

# ==============================================================================

if __name__=="__main__":
    from AOR.Test.SubroutineTest import RunTest
    RunTest()
