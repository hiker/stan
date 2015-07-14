#!/usr/bin/env python

import string
from   AOR.ProgUnit       import ProgUnit
from   AOR.BasicStatement import BasicStatement
from   AOR.DoubleList     import DoubleList

class Blockdata(ProgUnit):
    # Constructor for a subroutine object. Parameter:
    #
    # sSubName -- Name of function
    #
    def __init__(self, blockdataStatement):
        ProgUnit.__init__(self, blockdataStatement)
    
# ==============================================================================
class BlockdataStatement(BasicStatement):
    def __init__(self, loc=None, sBlock='BLOCK', sData='DATA',
                 sName=None, nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sBlock = sBlock
        self.sData  = sData
        self.sName  = sName
    # --------------------------------------------------------------------------
    def GetName(self): return self.sName
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet):
        l=BasicStatement.ToList(self, stylesheet)
        l.extend([stylesheet.sKeyword(self.sBlock),
                  stylesheet.sKeyword(self.sData)])
        if self.sName:
            l.extend([' ',self.sName])
        return l
# ==============================================================================
class EndBlockdata(BasicStatement):
    def __init__(self, loc=None, sEnd='END', sBlock='BLOCK', sData='DATA',
                 sName=None, nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sEnd   = sEnd
        self.sBlock = sBlock
        self.sData  = sData
        self.sName  = sName
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet):
        l=BasicStatement.ToList(self, stylesheet)
        l.append(stylesheet.sKeyword(self.sEnd))
        if self.sBlock:
            l.extend([' ', stylesheet.sKeyword(self.sBlock),
                           stylesheet.sKeyword(self.sData)])
        if self.sName:
            l.extend([' ', self.sName])
        return l
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.SubroutineTest import RunTest
    RunTest()
