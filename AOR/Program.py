#!/usr/bin/env python

import string
from   ProgUnit   import ProgUnit
from   Subroutine import SubroutineStatement

class Program(ProgUnit):
    # Constructor for a program object. Parameter:
    #
    # sProgName -- Name of function
    #
    def __init__(self, progStatement=None):
        ProgUnit.__init__(self, progStatement)
    
# ==============================================================================
class ProgramStatement(SubroutineStatement):
    def __init__(self, loc=None, lPrefix=[], sSub="PROGRAM", sName="",
                 nIndent=0, oSub = None):
        SubroutineStatement.__init__(self, loc=loc, lPrefix=lPrefix, sSub=sSub,
                                     sName=sName, nIndent=nIndent, oSub=oSub)
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.ProgramTest import RunTest
    RunTest()
