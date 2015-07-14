#!/usr/bin/env python

# This file contains all test classes for unit testing.

import sys
import string
from   traceback import print_exception


class Verbosity:
    # Constants for setting verbosity
    verbNOTHING  = 0   # print only statistics for main testsuite
    verbFAILURES = 1   # as above, plus print failures (default)
    verbNAME     = 2   # as above, plus statistics and name of each testsuite
                       #                           and testcase
    verbSUCCESS  = 3   # as above, plus one line for each successful run
    verbALL      = 4   # as above, plus details about each successful run
    
class TestCase(Verbosity):
    
    def __init__(self, sName, nIndent=0):
        self.sName    = sName
        self.nNumber  = 0
        self.nCount   = 0
        self.nFail    = 0
        self.nSuccess = 0
        self.nVerbose = self.verbFAILURES
        self.sIndent  = " "*nIndent

    # --------------------------------------------------------------------
    # Set verbosity of test
    def SetVerbose(self, nVerbose):
        self.nVerbose=nVerbose
    # --------------------------------------------------------------------
    # Set verbosity of test
    def SetIndent(self, nIndent):
        self.sIndent  = " "*nIndent
    # --------------------------------------------------------------------
    # Run all tests, should be overwritten
    def RunTests(self):
        print "RunTests method should be overwritten"
    # --------------------------------------------------------------------
    # Run all tests, including output. This function is called by a
    # testsuite and basically calls RunTests
    def RunAllTests(self):
        if self.nVerbose>=self.verbNAME:
            print "%sRunning"%self.sIndent,self.sName
            print "%s%s"%(self.sIndent, "-"*(8+len(self.sName)) )
        self.RunTests()
        if self.nVerbose>=self.verbNAME:
            print "%s%s finished. Tests: %d, failed: %d, successful: %d\n"%\
                  (self.sIndent, self.sName,self.nCount,self.nFail,
                   self.nSuccess)
        return (self.nCount,self.nFail, self.nSuccess)
    # --------------------------------------------------------------------
    # Return number of tests, should be overwritten
    def GetNumberOfTests(self): 
        return self.nNumber
    # --------------------------------------------------------------------
    # Test for equality
    def AssertEqual(self, test, correct, sComment=None):
        self.nCount=self.nCount+1
        # A temporary fix: ignore spaces when comparing results.
        # This is used for testing nesting with (f77 style) labels,
        # since the current output routines intend these labels (incorrectly)
        # Once we have a separate output object, this should be corrected and
        # the new object should be used for the tests.
        #if test==correct:
        if type(test)==type(""):
            test_no_space    = string.replace(test, " ","")
            correct_no_space = string.replace(correct, " ","")
        else:
            test_no_space    = test
            correct_no_space = correct
        if test_no_space==correct_no_space:
            self.nSuccess=self.nSuccess+1
            if self.nVerbose>=self.verbALL:
                print "[%s]\n==\n[%s] \t(%d/%d)\n"%(test,correct,
                                                    self.nCount,
                                                    self.GetNumberOfTests())
            elif self.nVerbose>=self.verbSUCCESS:
                print "%sSuccessfull %d/%d"%(self.sIndent, self.nCount,
                                             self.GetNumberOfTests())
        else:
            self.nFail=self.nFail+1
            if self.nVerbose>=self.verbFAILURES:
                print "%sFailure  %d/%d:"%(self.sIndent, self.nCount,
                                           self.GetNumberOfTests())
                print "%sCorrect:\n%s\n"%(self.sIndent, correct)
                print "%sIs     :\n%s"%(self.sIndent, test)
                if sComment:
                    print sComment
                    print '-'*len(sComment)

    # --------------------------------------------------------------------
    # Tests if a certain exception is raised. If a different exception
    # occurs or none at all, this is considered to be a failure. Parameters:
    #
    # f -- Function to call
    #
    # lParameters -- parameters of the function
    #
    # Exception -- Anticipated exception
    #
    # sDesc -- String describing this test.
    def AssertException(self, f, lParameters, Exception, sDesc):
        self.nCount=self.nCount+1
        try:
            apply(f, lParameters)
        except Exception:
            self.nSuccess=self.nSuccess+1
            if self.nVerbose>=self.verbALL:
                print "%sSuccessfull exception %s for %s: %d/%d" %\
                      (self.sIndent, Exception, sDesc, self.nCount,
                       self.GetNumberOfTests())
            return
        except:
            self.nFail=self.nFail+1
            if self.nVerbose>=self.verbFAILURES:
                excp, value, tb = sys.exc_info()
                print "%sFailure  %d/%d: %s raised wrong exception: %s" %\
                      (self.sIndent,self.nCount, self.GetNumberOfTests(),
                       sDesc, excp)
                print_exception(excp, value, tb)
            return
        self.nFail=self.nFail+1
        if self.nVerbose>=self.verbFAILURES:
            print "%sFailure  %d/%d: %s didn't raise an error" %\
                  (self.sIndent, self.nCount, self.GetNumberOfTests(), sDesc)

# =============================================================================

class TestSuite(Verbosity):
    # Constructor for a set of tests. Parameters:
    #
    # sName -- Name of this testsuite
    #
    # bIsMain -- If true, this is the main test which will display
    #            all collected statistics
    def  __init__(self, sName, bIsMain=0):
        self.lTests   = []
        self.sName    = sName
        self.nNumber  = 0
        self.bIsMain  = bIsMain
        self.nVerbose = self.verbFAILURES
        self.SetIndent(0)
        for i in range(len(sys.argv)):
            if sys.argv[i]=="-v":
                try:
                    # try to convert the next argument to a number
                    # (if an error occurs, just increase the
                    # verbosity by 1).
                    n = string.atoi(sys.argv[i+1])
                    self.nVerbose=n
                except:
                    self.nVerbose=self.nVerbose+1
    # --------------------------------------------------------------------
    # Set verbosity of this test suite (and therefore of all included tests)
    def SetVerbose(self, nVerbose):
        self.nVerbose=nVerbose
        for i in self.lTests:
            i.SetVerbose(nVerbose)
    # --------------------------------------------------------------------
    # Set verbosity of test
    def SetIndent(self, nIndent):
        self.nIndent  = nIndent
        self.sIndent  = " "*nIndent
        for i in self.lTests:
            i.SetIndent(nIndent+2)
    # --------------------------------------------------------------------
    def GetNumberOfTests(self): 
        return self.nNumber
    # --------------------------------------------------------------------
    # Add a test case or a test suite to this test suite!!
    def AddTest(self, t): 
        self.lTests.append(t)
        t.SetVerbose(self.nVerbose)
        t.SetIndent(self.nIndent+2)
        self.nNumber = self.nNumber + t.GetNumberOfTests()

    # --------------------------------------------------------------------
    def RunAllTests(self):
        if self.nVerbose>=self.verbNAME or self.bIsMain:
            print "\n%sRunning %s"%(self.sIndent, self.sName)
            print "%s%s"%(self.sIndent, "="*(8+len(self.sName)))
        nCount   = 0
        nFail    = 0
        nSuccess = 0
        for i in self.lTests:
            c,f,s    = i.RunAllTests()
            nCount   = nCount   + c
            nFail    = nFail    + f
            nSuccess = nSuccess + s
        if self.nVerbose>=self.verbNAME or self.bIsMain:
            print "%s%s finished"%(self.sIndent, self.sName)
        if self.nVerbose>=self.verbNAME or self.bIsMain:
            print "%s============================================="%\
                  self.sIndent
            print "%sTests ran: %d, failed: %d, successful: %d\n"%\
                  (self.sIndent, nCount,nFail, nSuccess)
        return (nCount, nFail, nSuccess)
