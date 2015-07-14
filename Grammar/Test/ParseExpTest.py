#!/usr/bin/env python

from Tools.Test          import TestCase, TestSuite
from Scanner.Scanner     import ScannerFactory
from Grammar.Parser      import Parser
from ParseTestBaseClass  import ParseTestBaseClass
from Grammar.Test.ParseSpecificationTest import TestSpecificationBase

# ==============================================================================
class ParseArraySpecTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "ArraySpec",
                                       ["(1)",    "(1:2)",    "(1:)",  "(:)",
                                        "(1,2,3)","(1:2,3:4)","(1:,2:)",
                                        "(*)",    "(1:*,*)",  "(1,2:*)" ])
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
         return parser.ParseArraySpec(tok)[1]
        
# ==============================================================================
class ParseArrayTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "ParseArray",
                                ["a(1:2:3)", "a(::3)", "a(1:2)", "a(:2)",
                                 "a(1::3)", "a(1:)", "a(:2:3)", "a(1:2:3,1)",
                                 "a(::3,1)","a(1:2,1)","a(:2,1)", "a(1::3,1)",
                                 "a(1:,1)","a(:2:3,1)", "a(:)",  "a(1)",
                                 "a(:,1)", "a(1,1)","a(i,j,k)"])
        self.lAssert = []
    # --------------------------------------------------------------------------
    def GetNumberOfTests(self): 
        return len(self.lTests)+len(self.lAssert)
    # --------------------------------------------------------------------------
    def Test(self, parser, token):
        return parser.ParsePrimary(token)[1]
    # --------------------------------------------------------------------------
    def RunTests(self):
        ParseTestBaseClass.RunTests(self)
            
        for i in self.lAssert:
            sInput  = "a(%s)"%i
            scanner = ScannerFactory(lines=["      %s\n"%sInput])
            parser  = Parser(scanner=scanner, bTestOnly=1)
            token   = scanner.GetNextToken()
            self.AssertException(f=parser.ParsePrimary,
                                 lParameters=[token],
                                 Exception=AssertionError,
                                 sDesc=sInput)
            del parser, scanner
        
# ==============================================================================
class ParseDataRefTest(ParseTestBaseClass):
    def __init__(self):
        # a(i)%b(i)(1:2) is a substring expression
        ParseTestBaseClass.__init__(self, "ParseDataRef",
                                ["a%b","a(i)%b","a%b(i)","a(i)%b(i)",
                                 "a(i)%b(i)(1:2)", "a%b%c",
                                 "a(1*2+3:2:3)%b(1,2,3)%c",'a(1,2)(3:4)'])
    # --------------------------------------------------------------------------
    def Test(self, parser, token): 
        return parser.ParsePrimary(token)[1]
# ==============================================================================
class ParseComplexConstTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "ParseComplexConst",
                                    ["(1,2)", "(1+2*3, 4+5*6)"])
    # --------------------------------------------------------------------------
    def Test(self, parser, token): 
        return parser.ParsePrimary(token)[1]
# ==============================================================================
class ParseLogicalTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "ParseLogicalTest",
                                    [".NOT. a",".NOT. .NOT. b", ".TRUE.",
                                     ".FALSE.", "f .AND. .TRUE.",
                                     "1.eq.2", "nn. eq .2",
                                     "a.eq.0. and. b", "1 == 2"])
    # --------------------------------------------------------------------------
    def Test(self, parser, token):
        return parser.ParseExpression(token)[1]
            
# ==============================================================================
class ParseArrayConstructor(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "ParseArrayConstructor",
                                    ["(/1, 2, 3/)",
                                     "(/'jan','feb'/)",
                                     "(/(i,i=1,6)/)",
                                     "(/(i,i=1,7, 2)/)",
                                     "(/(1.0/a(i),i=1,6)/)",
                                     "(/((i+j,i=1,3),j=1,2)/)",
                                     "(/a(i,2:4),a(1:5:2,i+3)/)"
                                     ])
    # --------------------------------------------------------------------------
    def Test(self, parser, token):
        return parser.ParseExpression(token)[1]
            
# ==============================================================================
class ParseKindConst(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "ParseComplexConst",
                                    ["1.0_2", "1_2", "0.0_KIND","5_ABC"])
    # --------------------------------------------------------------------------
    def Test(self, parser, token): 
        return parser.ParsePrimary(token)[1]
# ==============================================================================
class ParseComplicatedExpressionTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "ParseComplicatedExpression",
                                    ["1+2+3","(nlats+1)*12*(myrn-1979)"])
    # --------------------------------------------------------------------------
    def Test(self, parser, token):
        return parser.ParseExpression(token)[1]
            
# ==============================================================================
def CreateTestSuite():
    ts = TestSuite("Expression", bIsMain=1)
    ts.AddTest(ParseArraySpecTest())
    ts.AddTest(ParseArrayTest())
    ts.AddTest(ParseDataRefTest())
    ts.AddTest(ParseLogicalTest())
    ts.AddTest(ParseComplexConstTest())
    ts.AddTest(ParseArrayConstructor())
    ts.AddTest(ParseKindConst())
    ts.AddTest(ParseComplicatedExpressionTest())
    return ts
# ==============================================================================
def RunAllTests():
    ts = CreateTestSuite()
    ts.RunAllTests()
# ==============================================================================

if __name__=="__main__":
    RunAllTests()
