#!/usr/bin/env python
# A simple command line interface for stan. If you want to add your own methods,
# please modify the usage function, add a new parameter name to getopt and
# handle this parameter.

import getopt
import sys
from   Grammar.Parser      import Parser
from   Tools.Project       import Project
from   Stylesheets.f77     import f77

# ==============================================================================
# This functions imports all Test Suites, adds them to a global test suite
# and then runs all tests. I moved all test related import statements to here.
# It shouldn't make much of a difference.
def RunAllTests():
    from   Tools.Test          import TestSuite
    from   Scanner.RunAllTests import CreateScannerTestSuite
    from   AOR.RunAllTests     import CreateAORTestSuite
    from   Grammar.RunAllTests import CreateGrammarTestSuite
    from   Tools.RunAllTests   import CreateToolsTestSuite
    ts = TestSuite('All Test', bIsMain=1)
    ts.AddTest(CreateScannerTestSuite())
    ts.AddTest(CreateAORTestSuite()    )
    ts.AddTest(CreateGrammarTestSuite())
    ts.AddTest(CreateToolsTestSuite()  )
    ts.RunAllTests()
    
# ==============================================================================

def usage():
    print "Usage: Parser.py [-o] [-i] [-c] [-T] [-P] <list of files>"
    print
    print "-o: Print the file"
    print "-i: Generate interface"
    print "-c: Generate calltree"
    print "-T: Run unit tests (no filename required). For more detailed"
    print "    options use Grammar/RunAllTests directly. You can then"
    print "    increase the verbosity by adding '-v's or '-v 4'"
    print "-P: A run with the python profiler"
    
# ------------------------------------    
if __name__=="__main__":

    bDoProfile = 0
    bDoPrint   = 0
    bDoTest    = 0
    bInterface = 0
    bCallTree  = 0

    lOpt, lArgs = getopt.getopt(sys.argv[1:],"PoTic")
    for i in lOpt:
        if i[0]=="-P":
            bDoProfile=1
        elif i[0]=="-o":
            bDoPrint=1
        elif i[0]=="-T":
            bDoTest=1
        elif i[0]=="-i":
            bInterface=1
        elif i[0]=="-c":
            bCallTree=1
            
    if bDoTest:
        RunAllTests()
        sys.exit()
        
    if len(lArgs)<1:
        usage()
        
    if not bDoProfile:
        project = Project()
        ssheet  = f77()
        for i in lArgs:
            objFile = project.oGetObjectForIdentifier(i, "file")
            if bDoPrint:
                print ssheet.ToString(objFile)
            if bInterface:
                from Analyser.Interface import GenerateInterface
                from Stylesheets.f77    import f77
                ssheet = f77()
                for i in objFile.GetAllSubroutines():
                    print GenerateInterface(i, ssheet)
            if bCallTree:
                from Analyser.CallTree import GenerateFileCallTree
                print GenerateFileCallTree(objFile,i)
    else:
        import profile
        profile.run(
"""
project = Project()
for i in lArgs:
       objFile = project.oGetObjectForIdentifier(i, "file")
""")
