#!/usr/bin/env python

import string
from   AOR.DoubleList     import DoubleList
from   AOR.BasicStatement import BasicStatement, BasicNamedStatement

# ==============================================================================
# Stores an if statement without a then, e.g: if (a.eq.b) call sub
class IfOnly(BasicStatement):
    def __init__(self, sLabel=None, loc=None, sIf="IF", sParOpen='(',
                 oIfCond=None, sParClose=')', oStatement=None, nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sIf        = sIf
        self.l          = [sIf, sParOpen, oIfCond, sParClose, oStatement]
    # --------------------------------------------------------------------------
    # Returns the object representing the condition of an if-then statement
    def GetCondition(self): return self.l[2]
    # --------------------------------------------------------------------------
    # Returns the statement which is part of the if (without then) statement
    def GetStatement(self): return self.l[4]
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage):
        varUsage.AddVariable(self.l[2], "read", self)
        self.l[4].GetVarUsage(varUsage)
        
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.l[0]),nIndentNext=1)
        l.append(self.l[1])
        stylesheet.ToList(self.l[2], l)
        l.append(self.l[3],nIndentNext=1)
        stylesheet.ToList(self.l[4], l)
# ==============================================================================
# Stores an if-then or if statement
class If(BasicNamedStatement):
    def __init__(self, sLabel=None, sName=None, loc=None, sIf="IF", nIndent=0,
                 sParOpen='(', oIfCond=None, sParClose=')', sThen='THEN'):
        BasicNamedStatement.__init__(self, sLabel, sName, loc, nIndent,
                                     isDeclaration=0)
        self.l = [sIf, sParOpen,  oIfCond, sParClose, sThen]
    # --------------------------------------------------------------------------
    # Returns the object representing the condition of an if-then statement
    def GetCondition(self): return self.l[2]
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage):
        varUsage.AddVariable(self.l[2], "read", self)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicNamedStatement.ToList(self, stylesheet, l, bAddSpace=1)
        l.append(stylesheet.sKeyword(self.l[0]), nIndentNext=1)
        l.append(self.l[1])
        stylesheet.ToList(self.l[2], l)
        l.append(self.l[3], nIndentNext=1)
        l.append(stylesheet.sKeyword(self.l[4]))
    
# ==============================================================================
class ElseIf(BasicStatement):
    def __init__(self, sLabel=None, loc=None, sElse=None, sIf=None, nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.lElseIf = [sElse, sIf]
        self.lExpr   = []
        self.sThen   = None
        self.sName   = None
    # --------------------------------------------------------------------------
    def AddExpr(self, sParOpen, expr, sParClose):
        self.lExpr = [sParOpen, expr, sParClose]
    # --------------------------------------------------------------------------
    def SetThen(self, sThen): self.sThen = sThen
    # --------------------------------------------------------------------------
    def SetName(self, sName): self.sName = sName
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage):
        varUsage.AddVariable(self.lExpr[1], "read", self)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.lElseIf[0]), nIndentNext=1)
        l.append(stylesheet.sKeyword(self.lElseIf[1]), nIndentNext=1)
        l.append(self.lExpr[0])
        stylesheet.ToList(self.lExpr[1], l)
        l.append(self.lExpr[2], nIndentNext=1)
        if self.sThen:
            l.append(stylesheet.sKeyword(self.sThen))
        if self.sName:
            l.append(self.sName, nIndent=1)
# ==============================================================================
class Else(BasicStatement):
    def __init__(self, sLabel=None, loc=None, sElse="ELSE", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sElse = sElse
        self.sName = None
    # --------------------------------------------------------------------------
    def SetName(self, sName): self.sName = sName
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sElse))
        if self.sName: l.append(self.sName, nIndent=1)
# ==============================================================================
class EndIf(BasicStatement):
    def __init__(self, sLabel=None, loc=None, sEnd="END", sIf="IF", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc,nIndent, isDeclaration=0)
        self.lEndIf = [sEnd, sIf]
        self.sName  = None
    # --------------------------------------------------------------------------
    def SetName(self, sName): self.sName = sName
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(self.lEndIf[0]           )
        l.append(self.lEndIf[1], nIndent=1)
        if self.sName: l.append(self.sName, nIndent=1)
# ==============================================================================
class ArithmeticIf(BasicStatement):
    # Stores an arithmetic if statement
    def __init__(self, sLabel=None, loc=None, sIf="IF", sParOpen='(',
                 ifCond=None, sParClose=')', nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sIf       = sIf
        self.sParOpen  = sParOpen
        self.ifCond    = ifCond
        self.sParClose = sParClose
        self.lLabels   = DoubleList()
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage):
        varUsage.AddVariable(self.ifCond, "read", self)
    # --------------------------------------------------------------------------
    def AppendLabel(self, sLabel, sComma=None):
        self.lLabels.append(sLabel, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sIf), nIndentNext=1)
        l.append(self.sParOpen)
        stylesheet.ToList(self.ifCond, l)
        l.append(self.sParClose, nIndentNext=1)
        self.lLabels.ToList(stylesheet, l)
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.IfTest import RunTest
    RunTest()
