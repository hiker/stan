#!/usr/bin/env python

from Tools.Test          import TestCase, TestSuite
from ParseTestBaseClass  import ParseTestBaseClass

# ===========================================================================
class ParseSubroutineTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Subroutine",
                                ["SUBROUTINE Test",
                                 "SUBROUTINE Test(a,b,c,d)",
                                 "SUBROUTINE Test()",
                                 "RECURSIVE  SUBROUTINE test",
                                 "ELEMENTAL SUBROUTINE test",
                                 "RECURSIVE ELEMENTAL SUBROUTINE test",
                                 "RECURSIVE ELEMENTAL SUBROUTINE test()",
                                 "RECURSIVE ELEMENTAL SUBROUTINE test(a,b,c,d)",
                                 ] )
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
        res = parser.ParseFile(tok, bIsTest=1)
        return parser.sub
        
# ===========================================================================
class ParseFunctionTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Function",
                                ["FUNCTION Test()",
                                 "FUNCTION Test(a,b,c,d)",
                                 "RECURSIVE FUNCTION test()",
                                 "ELEMENTAL FUNCTION test()",
                                 "RECURSIVE ELEMENTAL FUNCTION test()",
                                 "RECURSIVE ELEMENTAL SUBROUTINE test(a,b,c,d)",
                                 "INTEGER FUNCTION anothertest()",
                                 "DOUBLE PRECISION FUNCTION mytest(a, b, c)",
                                 "RECURSIVE REAL FUNCTION fbemgamma(rbemx) RESULT(rbemgamma)"
                                 ] )
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
        res = parser.ParseFile(tok, bIsTest=1)
        return parser.sub
        
# ===========================================================================
class ParseInterfaceTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Interface",
                                [
"""INTERFACE
  SUBROUTINE sub1(x,y,n)
    INTEGER n
    DIMENSION x(n), y(n)
  END SUBROUTINE sub1
  SUBROUTINE sub2
  END SUBROUTINE sub2
  END INTERFACE""",
"""INTERFACE switch
  SUBROUTINE int_switch(x,y)
    INTEGER x,y
  END SUBROUTINE int_switch
  SUBROUTINE real_switch(x,y)
    REAL x,y
  END SUBROUTINE real_switch
END INTERFACE"""
                                 ] )
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
        parser.bIsExec = 0
        res = parser.ParseStatements(tok)
        return parser.sub
# ===========================================================================
class ParseTypeTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Types",
                                [
"""SUBROUTINE sub1(x,y,n)
   type, public :: t
     real, dimension(:), pointer :: p
     real                        :: q
    end type t""",
        ] )
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
        parser.bIsExec = 0
        res = parser.ParseStatements(tok)
        return parser.sub
        
# ===========================================================================
class ParseContainedTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Contained",
                                [
"""SUBROUTINE subouter
    INTEGER a
   CONTAINS
     SUBROUTINE sub1(x,y,n)
      INTEGER n
      DIMENSION x(n), y(n)
     END SUBROUTINE sub1
    SUBROUTINE sub2
    END SUBROUTINE sub2
  END SUBROUTINE subouter""",
"""SUBROUTINE subouter
    INTEGER a
   CONTAINS
     SUBROUTINE sub1(x,y,n)
      INTEGER n
      DIMENSION x(n), y(n)
      a=a+n
     END SUBROUTINE sub1
  END SUBROUTINE subouter""",
                                 ] )
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
        parser.bIsExec = 0
        res = parser.ParseStatements(tok)
        return parser.sub
        
# ===========================================================================
class ParseModuleTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Module",
                                [
"""MODULE test
    INTEGER a
   CONTAINS
     SUBROUTINE sub1(x,y,n)
      INTEGER n
      DIMENSION x(n), y(n)
     END SUBROUTINE sub1
    SUBROUTINE sub2
    END SUBROUTINE sub2
  END MODULE test""",
        
"""MODULE subouter
     INTEGER a
   CONTAINS
     SUBROUTINE sub1(x,y,n)
       INTEGER n
       DIMENSION x(n), y(n)
       a=a+n
     END SUBROUTINE sub1
  END SUBROUTINE subouter""",
# This tests if variables from the outer subroutine/module are handled
# correctly, e.g. if the fact that a,b,c are arrays is recognised
# If not, a(), b(), c() would be parsed as function calls, and would
# therefore fail, because "1:10" is an invalid specification in this case.
"""MODULE subouter
     INTEGER, DIMENSION(20):: a
     INTEGER               :: b(20)
     CHARACTER*(20)        :: c
     CHARACTER*20          :: d
   CONTAINS
     SUBROUTINE sub1(n)
       INTEGER n
       a(1:10)=a(1:10)+n
       b(1:10)=a(1:10)
       c(1:10)='1234567890'
       d(1:10)='1234567890'
     END SUBROUTINE sub1
  END SUBROUTINE subouter""",
                                 ] )
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
        parser.bIsExec = 0
        res = parser.ParseFile(tok)
        return parser.sub
        
# ===========================================================================
def CreateTestSuite():
    ts = TestSuite("Program Units", bIsMain=1)
    ts.AddTest( ParseSubroutineTest() )
    ts.AddTest( ParseFunctionTest()   )
    ts.AddTest( ParseInterfaceTest()  )
    ts.AddTest( ParseTypeTest()       )
    ts.AddTest( ParseContainedTest()  )
    ts.AddTest( ParseModuleTest()     )
    return ts
# ===========================================================================
def RunAllTests():
    ts = CreateTestSuite()
    ts.RunAllTests()
# ===========================================================================

if __name__=="__main__":
    RunAllTests()
