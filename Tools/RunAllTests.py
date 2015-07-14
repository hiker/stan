#!/usr/bin/env python

from Tools.Test import TestSuite
from Tools.TestDir import VarUsageTest

# ===========================================================================
def CreateToolsTestSuite():
    ts = TestSuite("All Tools Tests", bIsMain=1)
    ts.AddTest(VarUsageTest.CreateTestSuite())
    return ts
# ===========================================================================

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="-p":
        import profile
        ts = CreateToolsTestSuite()
        profile.run("ts.RunAllTests()")
    else:
        ts = CreateToolsTestSuite()
        ts.RunAllTests()
