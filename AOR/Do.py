#!/usr/bin/env python

import string

from   AOR.BasicStatement import BasicNamedStatement, BasicStatement

class ControlLessDo(BasicNamedStatement):
    # Stores a Do loop without loop control
    def __init__(self, sLabel=None, sName=None, loc=None,
                 sDo="DO", sDoLabel=None, nIndent=0):
        self.sDo       = sDo
        self.sDoLabel  = sDoLabel
        self.lLoopData = []
        BasicNamedStatement.__init__(self, sLabel, sName, loc, nIndent,
                                     isDeclaration=0)
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicNamedStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sDo))
        if self.sDoLabel:
            l.append(self.sDoLabel, nIndent=1)
# ==============================================================================
# Exit statement
class Exit(BasicStatement):
    def __init__(self, sLabel=None, loc=None, sExit="EXIT", sExitLabel=None,
                 nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sExit      = sExit
        self.sExitLabel = sExitLabel
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if self.sExitLabel:
            BasicStatement.ToList(self, stylesheet, l)
            l.append(stylesheet.sKeyword(self.sExit), nIndentNext=1)
            l.append(self.sExitLabel)
        else:
            BasicStatement.ToList(self, stylesheet, l)
            l.append(stylesheet.sKeyword(self.sExit))
               
# ==============================================================================
class Cycle(Exit):
    # Stores a cycle statement which can have a do-construct name
    # (which is basically the same as an exit statement)
    def __init__(self, sLabel=None, loc=None, sCycle='CYCLE',
                 sCycleLabel=None, nIndent=0):
        Exit.__init__(self, sLabel, loc, sCycle, sCycleLabel, nIndent)
# ==============================================================================
class DoWhile(BasicNamedStatement):
    # Stores a Do-While loop
    def __init__(self, sLabel=None, sName=None, loc=None,
                 sDo="DO", sDoLabel=None, sOptComma=None, sWhile="WHILE",
                 sParOpen='(', nIndent=0):
        self.sDo       = sDo
        self.sOptComma = sOptComma
        self.sDoLabel  = sDoLabel
        self.sWhile    = sWhile
        self.sParOpen  = sParOpen
        self.exp       = None
        self.sParClose = None
        BasicNamedStatement.__init__(self, sLabel, sName, loc, nIndent,
                                     isDeclaration=0)
    # --------------------------------------------------------------------------
    def SetExpression(self, exp, sParClose=')'):
        self.exp       = exp
        self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage):
        varUsage.AddVariable(self.exp, "read", self)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicNamedStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sDo))
        if self.sDoLabel:  l.append(self.sDoLabel, nIndent=1)
        if self.sOptComma: l.append(self.sOptComma)
        l.append(stylesheet.sKeyword(self.sWhile), nIndent=1)
        l.append(self.sParOpen)
        stylesheet.ToList(self.exp, l)
        l.append(self.sParClose)
        
# ==============================================================================

class Do(BasicNamedStatement):

    # Stores a Do-loop statement
    #
    # sLabel -- Label of the Do statement (this is NOT the label
    #           used in the DO loop, e.g.: 100 DO 200 i=1, 10
    #           This is the label 100, not the label 200
    #
    # sName -- Name of the do statement
    #
    def __init__(self, sLabel=None, sName=None, loc=None,
                 sDo="DO", sDoLabel=None, sOptComma=None, nIndent=0,
                 var=None, sFrom=None, sTo=None):
        self.sDo       = sDo
        self.sOptComma = sOptComma
        self.lLoopData = []
        self.sDoLabel  = sDoLabel
        BasicNamedStatement.__init__(self, sLabel, sName, loc, nIndent,
                                     isDeclaration=0)
        if var: self.SetVariable(var,"=")
        if sFrom: self.SetFrom(sFrom,",")
        if sTo: self.SetTo(sTo)
    # --------------------------------------------------------------------------
    def SetVariable(self, var, sEqual): self.lLoopData.extend([var, sEqual])
    # --------------------------------------------------------------------------
    def SetFrom(self, f, sComma): self.lLoopData.extend([f, sComma])
    # --------------------------------------------------------------------------
    def SetTo  (self, t): self.lLoopData.append(t)
    # --------------------------------------------------------------------------
    def SetStep(self, sComma, s): self.lLoopData.extend([sComma, s])
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage):
        varUsage.AddVariable(self.lLoopData[0], "write",self)   # the do variable is written
        varUsage.AddVariable(self.lLoopData[2], "read", self)
        varUsage.AddVariable(self.lLoopData[4], "read", self)
        if len(self.lLoopData)>5:
            varUsage.AddVariable (self.lLoopData[6], "read", self)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicNamedStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sDo), nIndentNext=1)
        if self.sDoLabel:
            l.append(self.sDoLabel, nIndentNext=1)
        if self.sOptComma: l.append(self.sOptComma)
        stylesheet.ToList(self.lLoopData[0], l)               # var
        l.indent(1)
        l.append(self.lLoopData[1], nIndentNext=1)            # =
        stylesheet.ToList(self.lLoopData[2], l)               # from
        l.append(self.lLoopData[3], nIndentNext=1)            # ,
        stylesheet.ToList(self.lLoopData[4], l)               # to
        if len(self.lLoopData)>5:
            l.append(self.lLoopData[5],nIndentNext=1)         # ,
            stylesheet.ToList(self.lLoopData[6], l)           # step
 
# ==============================================================================
class EndDo(BasicStatement):

    # Stores an EndDo statement which can have a do-construct name
    #
    # sLabel -- Label of the statement (5 digit number as a string)
    #
    def __init__(self, sLabel=None, loc=None, sEnd='END', sDo='DO',  nIndent=0):
        self.lEndDo  = [sEnd, sDo]
        self.sName = None
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
    # --------------------------------------------------------------------------
    def SetName(self, sName): self.sName = sName
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.lEndDo[0]), nIndentNext=1)
        l.append(stylesheet.sKeyword(self.lEndDo[1]))
        if self.sName:
            l.append(self.sName)
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.DoTest import RunTest
    RunTest()
