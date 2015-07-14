#!/usr/bin/env python

from Tools.Test     import TestCase, TestSuite
from AOR.ProgUnit   import ProgUnit
from AOR.Statements import Call
from AOR.If         import If, IfOnly
from Grammar.Parser import ParserClass

class ProgUnitTest(TestCase):
    def __init__(self):
        TestCase.__init__(self, 'ProgUnit Test')
        self.lProgram = ['''\
       SUBROUTINE Test()

       integer a
!cdir directive
#ifdef COMPILER_DIRECTIVE
#endif
!there is an empty line following!
       if(a.eq.1) call sub()
       END SUBROUTINE Test
''']
        
    # --------------------------------------------------------------------------
    def GetNumberOfTests(self): return 7
    # --------------------------------------------------------------------------
    def RunTests(self):
        parser   = ParserClass(bTestOnly=1, sInput=self.lProgram[0])
        tok, sub = parser.ParseSubroutine([], parser.GetNextToken())

        l        = sub.lGetStatements([Call])
        self.AssertEqual(len(l),1,"Wrong length of returned list")
        self.AssertEqual(l[0].__class__, Call, "Returned element is not Call")
        
        l        = sub.lGetStatements([IfOnly, Call])
        self.AssertEqual(len(l),1,"Wrong length of returned list")
        self.AssertEqual(l[0].__class__, IfOnly, "Returned element is not Call")
        
        l        = sub.lGetStatements([Call], bExtractIfOnly=0)
        self.AssertEqual(len(l),0,"Wrong length of returned list")
        
        l        = sub.lGetStatements([IfOnly, Call], bExtractIfOnly=0)
        self.AssertEqual(len(l),1,"Wrong length of returned list")
        self.AssertEqual(l[0].__class__, IfOnly, "Returned element is not Call")
        
        
                   
# ==============================================================================
def CreateTestSuite():
    ts = TestSuite("ProgUnit", bIsMain=1)
    ts.AddTest(ProgUnitTest())
    return ts
# ==============================================================================
def RunAllTests():
    ts = CreateTestSuite()
    ts.RunAllTests()
# ==============================================================================

if __name__=="__main__":
    RunAllTests()
