#!/usr/bin/env python

from Tools.Test   import TestSuite
from AOR.Test     import ProgUnitTest

# ===========================================================================
def CreateAORTestSuite():
    ts = TestSuite("All AOR Tests", bIsMain=1)
    ts.AddTest(ProgUnitTest.CreateTestSuite())
    return ts
# ===========================================================================

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="-p":
        import profile
        ts = CreateAORTestSuite()
        profile.run("ts.RunAllTests()")
    else:
        ts = CreateAORTestSuite()
        ts.RunAllTests()
