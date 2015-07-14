#!/usr/bin/env python

import string

from   AOR.BasicStatement import BasicNamedStatement, BasicStatement
from   AOR.DoubleList     import DoubleList

class Select(BasicNamedStatement):

    # Stores a select statement
    #
    # sLabel -- Label of the select statement (this is NOT the label
    #           used in the DO loop, e.g.: 100 DO 200 i=1, 10
    #           This is the label 100, not the label 200
    #
    # sName -- Name of the do statement
    #
    def __init__(self, sLabel=None, sName=None, loc=None,
                 sSelect="SELECT", sCase="CASE", sParOpen='(',
                 exp=None, sParClose=')', nIndent=0):
        BasicNamedStatement.__init__(self, sLabel, sName, loc, nIndent,
                                     isDeclaration=0)
        self.sSelect   = sSelect
        self.sCase     = sCase
        self.sParOpen  = sParOpen
        self.exp       = exp
        self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicNamedStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sSelect), nIndentNext=1)
        l.append(stylesheet.sKeyword(self.sCase),   nIndentNext=1)
        l.append(self.sParOpen)
        self.exp.ToList(stylesheet, l)
        l.append(self.sParClose)
 
# ==============================================================================
class Case(BasicStatement):

    # Stores a Case statement 
    #
    def __init__(self, sLabel=None, loc=None, sCase='CASE',  nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sCase     = sCase
        self.sName     = None
        self.sDefault  = None           # for DEFAULT
        self.sParOpen  = None
        self.sParClose = None
        self.lSelector = DoubleList()
    # --------------------------------------------------------------------------
    def SetName(self, sName): self.sName = sName
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen='('): self.sParOpen=sParOpen
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose=')'): self.sParClose=sParClose
    # --------------------------------------------------------------------------
    # Sets either the selector to 'DEFAULT' or to '(obj)'.
    def AddSelector(self, obj=None, sComma=None, sDefault=None):
        if sDefault:
            self.sDefault = sDefault
        else:
            self.lSelector.append(obj, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(self.sCase, nIndentNext=1)
        if self.sDefault:
            l.append(self.sDefault)
        else:
            l.append(self.sParOpen)
            self.lSelector.ToList(stylesheet, l)
            l.append(self.sParClose)
        if self.sName: l.append(self.sName, nIndentNext=1)
# ==============================================================================
class EndSelect(BasicStatement):

    # Stores an EndSelect statement which can have a select-construct name
    #
    # sLabel -- Label of the statement (5 digit number as a string)
    #
    def __init__(self, sLabel=None, loc=None, sEnd='END', sSelect='CASE',  nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.lEndCase  = [sEnd, sSelect]
        self.sName     = None
    # --------------------------------------------------------------------------
    def SetName(self, sName): self.sName = sName
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.lEndCase[0]), nIndentNext=1)
        l.append(stylesheet.sKeyword(self.lEndCase[1]))
        if self.sName:
            l.append(self.sName, nIndent=1)
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.SelectTest import RunTest
    RunTest()
