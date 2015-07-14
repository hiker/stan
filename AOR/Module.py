#!/usr/bin/env python

import string
from   AOR.ProgUnit       import ProgUnit
from   AOR.BasicStatement import BasicStatement

class Module(ProgUnit):
    # Constructor for a module object. Parameter:
    #
    # modStatement -- the actual module statement
    #
    def __init__(self, modStatement=None):
        ProgUnit.__init__(self, modStatement)
    
# ==============================================================================
class ModuleStatement(BasicStatement):
    def __init__(self, loc=None, sModule="MODULE", sName="",
                 nIndent=0, oModule = None):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sModule     = sModule
        self.sName       = sName
        self.oModule     = oModule
    # --------------------------------------------------------------------------
    def GetName(self): return self.sName
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sModule), nIndentNext=1)
        l.append(self.sName)
    # --------------------------------------------------------------------------
  
     

# ==============================================================================

if __name__=="__main__":
    from AOR.Test.ModuleTest import RunTest
    RunTest()
