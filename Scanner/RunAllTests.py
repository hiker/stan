#!/usr/bin/env python

from Tools.Test import TestSuite
from Test       import ScannerTest

# ===========================================================================
def CreateScannerTestSuite():
    ts = TestSuite("All Scanner Tests", bIsMain=1)
    ts.AddTest(ScannerTest.FixedScannerTest())
    ts.AddTest(ScannerTest.FreeScannerTest() )
    return ts
# ===========================================================================

if __name__=="__main__":
    import sys
    if len(sys.argv)>1 and sys.argv[1]=="-p":
        import profile
        ts=CreateScannerTestSuite()
        profile.run("ts.RunAllTests()")
    else:
        ts=CreateScannerTestSuite()
        ts.RunAllTests()
