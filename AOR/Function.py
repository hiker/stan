#!/usr/bin/env python

import string
from   AOR.ProgUnit        import ProgUnit
from   AOR.BasicStatement  import BasicStatement
from   AOR.DoubleList      import DoubleList
from   AOR.Declaration     import Type

class Function(ProgUnit):
    # Constructor for a subroutine object. Parameter:
    #
    # sSubName -- Name of function
    #
    def __init__(self, FuncStatement):
        ProgUnit.__init__(self, FuncStatement)
    
# ==============================================================================
class FunctionStatement(BasicStatement):
    def __init__(self, loc=None, nIndent=0, lType=None, sFunc="FUNCTION", sName="",
                 oFunc = None):
        BasicStatement.__init__(self, None, loc, nIndent, isDeclaration=0)
        self.sFunc       = sFunc
        self.sName       = sName
        self.lArgs       = DoubleList()
        self.sParOpen    = None
        self.sParClose   = None
        self.lType       = lType
        self.oFunc       = oFunc
        self.lResult     = []
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen  ): self.sParOpen  = sParOpen
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def GetName(self): return self.sName
    # --------------------------------------------------------------------------
    def GetType(self): return self.lType
    # --------------------------------------------------------------------------
    def GetArguments(self): return self.lArgs.GetMainList()
    # --------------------------------------------------------------------------
    def AddArgument(self, sName, sComma=None, d=None):
        self.lArgs.append(sName, sComma)
        if self.oFunc:
            self.oFunc.AddArgument(sName, sComma=sComma, d=d)
    # --------------------------------------------------------------------------
    def SetResult(self, sResult, sParOpen, sName, sParClose):
        self.lResult = [sResult, sParOpen, sName, sParClose]
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        for i in self.lType:
            if i.__class__==Type:
                i.ToList(stylesheet, l)
            else:
                l.append(stylesheet.sKeyword(i))
            l.indent(1)
        l.append(stylesheet.sKeyword(self.sFunc), nIndentNext=1)
        l.append(self.sName)
        if not self.sParOpen:
            return
        l.append(self.sParOpen)
        self.lArgs.ToList(stylesheet, l)
        l.append(self.sParClose)
        if self.lResult:
            l.indent(1)
            l.extend(self.lResult)
                 
    # --------------------------------------------------------------------------
  
     

# ==============================================================================

if __name__=="__main__":
    from AOR.Test.FunctionTest import RunTest
    RunTest()
