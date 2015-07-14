#!/usr/bin/env python

from Tools.Test   import TestSuite
from Grammar.Test import ParseExpTest
from Grammar.Test import ParseSpecificationTest 
from Grammar.Test import ParseExecutionTest
from Grammar.Test import ParseProgUnitTest

# ===========================================================================
def CreateGrammarTestSuite():
    ts = TestSuite("All Parser Tests", bIsMain=1)
    ts.AddTest(ParseExpTest.CreateTestSuite())
    ts.AddTest(ParseSpecificationTest.CreateTestSuite())
    ts.AddTest(ParseExecutionTest.CreateTestSuite())
    ts.AddTest(ParseProgUnitTest.CreateTestSuite())
    return ts
# ===========================================================================

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="-p":
        import profile
        ts=CreateGrammarTestSuite()
        profile.run("ts.RunAllTests()")
    else:
        ts=CreateGrammarTestSuite()
        ts.RunAllTests()
