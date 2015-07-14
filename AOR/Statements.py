#!/usr/bin/env python

import string
from   UserList           import UserList
from   AOR.DoubleList     import DoubleList
from   AOR.BasicStatement import BasicStatement, BasicRepr
from   AOR.Expression     import ArraySpecWithName

# ==============================================================================
# Stores an option string like 'a=b'
class OptionString(BasicRepr):
    def __init__(self, lhs, sEqual, rhs):
        self.l=[lhs, sEqual, rhs]
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        varUsage.AddVariable(self.l[2], sType, obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        stylesheet.ToList(self.l[0], l)
        l.append(self.l[1])
        stylesheet.ToList(self.l[2], l)
# ==============================================================================
class Allocate(BasicStatement):

    # Stores a return statement.
    def __init__(self, sLabel=None, loc=None, sOp='ALLOCATE',sParOpen='(',
                 nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sOp             = sOp
        self.sParOpen        = sParOpen
        self.lVars           = DoubleList()
        self.lOptions        = DoubleList()
        self.sParClose       = ")"
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    # Adds a variable to allocate to the allocate statement. Parameters:
    #
    # var -- Variable to add
    #
    # sSeparator -- String which separates a variable from the next. Usual a
    #               comma, but the ')' is stored here as well.
    def AddVariable(self, var, sSeparator=None):
        self.lVars.append(var, sSeparator)
    # --------------------------------------------------------------------------
    # Appends an option (stat, errmsg, or source) to the statement. Parameters:
    #
    # sName -- Name of the option
    #
    # sEqual -- The '=' character
    #
    # obj -- A scalar int variable
    #
    # sSeparator -- String which separates an option from the next. Usual a
    #               comma, but the ')' can be stored here as well.
    def AddOption(self, sName, sEqual, obj, sSeparator=None):
        self.lOptions.append( OptionString(sName, sEqual, obj), sSeparator )
    # --------------------------------------------------------------------------
    # Creates a list of strings which represents this statement. Parameters:
    #
    # stylesheet -- The stylesheet to use during layout
    def ToList(self, stylesheet=None,l=[]):
        BasicStatement.ToList(self, stylesheet, l)
        l.extend([stylesheet.sKeyword(self.sOp), self.sParOpen]) # 'allocate', '('
        self.lVars.ToList(stylesheet, l)
        self.lOptions.ToList(stylesheet, l)
        l.append(self.sParClose)

# ==============================================================================
class Assignment(BasicStatement):

    # Stores an assignment or pointer assignment statement:
    # assignment-stmt is variable = expr   or
    # pointer-assignment-stmt is
    #     data-pointer-object [ (bounds-spec-list) ] => data-target or
    #     data-pointer-object (bounds-remapping-list ) => data-target or
    #     proc-pointer-object => proc-target
    # This object is not only used as a real statement e.g. it is used
    # in the Parameter object as well). If the flag bNoIndent is set
    # the object will not add indentation in ToList!!
    def __init__(self, sLabel=None, loc=None, nIndent=0, lhs=None,
                 sEqual='=', rhs=None, bNoIndent=None):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.lhs       = lhs
        self.sEqual    = sEqual
        self.rhs       = rhs
        self.bNoIndent = bNoIndent
    # --------------------------------------------------------------------------
    # Define the left hand side of an assignment
    def SetLeftHandSide (self, ls): self.lhs=ls
    # --------------------------------------------------------------------------
    def SetRightHandSide(self, rs): self.rhs=rs
    # --------------------------------------------------------------------------
    def SetEqualSign(self, eq): self.eq = eq
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        varUsage.AddVariable(self.rhs, "read",  obj=self)
        varUsage.AddVariable(self.lhs, "write", obj=self)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet,l):
        if not self.bNoIndent:
            BasicStatement.ToList(self, stylesheet, l)
        stylesheet.ToList(self.lhs, l)
        # one space before and after the =
        l.append(self.sEqual, nIndent=1, nIndentNext=1)
        stylesheet.ToList(self.rhs, l)
# ==============================================================================
# Stores a '*123' like expression
class StarLabel(BasicRepr):
    def __init__(self, sStar, sLabel):
        self.l=[sStar, sLabel]
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.extend([self.l[0], self.l[1]])
# ==============================================================================
class FunctionCall(BasicRepr):

    # Stores a function call.
    def __init__(self, sName=None, sArg=None):
        self.sName     = sName
        self.lArgs     = DoubleList()
        self.sParOpen  = None
        self.sParClose = None
        if sArg:
            self.sParOpen="("
            self.AddArgument(sArg)
            self.sParClose=")"
    # --------------------------------------------------------------------------
    # Returns the name of the called subroutine
    def sGetName(self): return self.sName
    # --------------------------------------------------------------------------
    def lGetArgs(self): return self.lArgs
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen): self.sParOpen = sParOpen
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    # Adds an actual argument.
    def AddArgument(self, arg, sComma=None):
        if self.sParOpen==None: self.sParOpen="("
        self.sParClose = ")"
        if sComma==None and \
               len(self.lArgs.lGetSecondaryList())==len(self.lArgs)-1:
            self.lArgs.append(",", arg)
        else:
            self.lArgs.append(arg, sComma)
    # --------------------------------------------------------------------------
    # Adds a keyword argument: keyword=val
    def AddKeywordArgument(self, sKeyword, sEqual, obj, sComma=None):
        self.lArgs.append(OptionString(sKeyword, sEqual, obj), sComma)
    # --------------------------------------------------------------------------
    # Adds an alternate return specification: *123
    def AddAltReturn(self, sStar, sLabel, sComma=None):
        self.lArgs.append(StarLabel(sStar, sLabel), sComma)
    # --------------------------------------------------------------------------
    # Adds an alternate return specification with keyword: keyw=*123
    def AddKeywordAltReturn(self, sKeyword, sEqual, sStar, sLabel, sComma=None):
        self.lArgs.append(OptionString(sKeyword, sEqual,
                                       StarLabel(sStar, sLabel)), sComma)
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.lArgs.GetMainList():
            varUsage.AddVariable(i, "unknown", obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if stylesheet["mathsmode"]:
            s = string.lower(self.sName)
            if s=="sqrt" and stylesheet["dosqrt"]:
                return stylesheet.HandleSqrt(self, l)
            if s=="exp" and stylesheet["doexp"]:
                return stylesheet.HandleExp(self, l)
            if s=="abs" and stylesheet["doabs"]:
                return stylesheet.HandleAbs(self, l)
        l.append(self.sName)
        if not self.sParOpen: return
        l.append(self.sParOpen)
        self.lArgs.ToList(stylesheet, l, bAddSpace=1)
        l.append(self.sParClose)
# ==============================================================================
class Call(FunctionCall, BasicStatement):
    def __init__(self, sLabel=None, loc=None, sCall="CALL", sName=None,
                 nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        FunctionCall.__init__(self, sName)
        self.sCall = sCall
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sCall), nIndentNext=1)
        FunctionCall.ToList(self, stylesheet, l)

# ==============================================================================
class Contains(BasicStatement):

    # Stores a contains statement
    #
    def __init__(self, sLabel=None, loc=None, sContains="CONTAINS", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent)
        self.sContains = sContains
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(self.sContains)
# ==============================================================================
class Continue(BasicStatement):

    # Stores a continue statement (with a label)
    #
    # sLabel -- Label of the statement (5 digit number as a string)
    #
    def __init__(self, sLabel=None, loc=None, sCont="CONTINUE", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sCont = sCont
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sCont))
    
# ==============================================================================
# Deallocate is basically like an allocate - so we can use the same object here.
class Deallocate(Allocate):

    # Stores a deallocate statement.
    def __init__(self, sLabel=None, loc=None, sOp='DEALLOCATE',sParOpen='(',
                 nIndent=0):
        Allocate.__init__(self, sLabel=None, loc=loc, sOp=sOp,
                          sParOpen='(', nIndent=0)
    
# ==============================================================================
class Goto(BasicStatement):

    # Stores a goto statement (with a label)
    #
    # sLabel -- Label of the statement (5 digit number as a string)
    #
    # sGotoLabel -- The label to go to
    def __init__(self, sLabel=None, loc=None, sGo="GO", sTo="TO",
                 sGotoLabel=None, nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sGo        = sGo
        self.sTo        = sTo
        self.sGotoLabel = sGotoLabel
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.extend([stylesheet.sKeyword(self.sGo), stylesheet.sKeyword(self.sTo)])
        l.append(self.sGotoLabel, nIndent=1)
# ==============================================================================
class ComputedGoto(BasicStatement):

    # Stores a goto statement (with a label)
    #
    # sLabel -- Label of the statement (5 digit number as a string)
    #
    # sGotoLabel -- The label to go to
    def __init__(self, sLabel=None, loc=None, sGo="GO", sTo="TO",
                 sParOpen="(", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sGo        = sGo
        self.sTo        = sTo
        self.sParOpen   = sParOpen
        self.sParClose  = ""
        self.sComma     = ""
        self.lLabels    = DoubleList()
        self.oExp       = None
    # --------------------------------------------------------------------------
    def AddLabel(self, sLabel, sComma=None):
        self.lLabels.append(sLabel, sComma)
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose =sParClose
    # --------------------------------------------------------------------------
    def AddComma(self, sComma): self.sComma = sComma
    # --------------------------------------------------------------------------
    def SetExp(self, oExp): self.oExp = oExp
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.extend([stylesheet.sKeyword(self.sGo), stylesheet.sKeyword(self.sTo)])
        l.append(self.sParOpen, nIndent=1)
        self.lLabels.ToList(stylesheet, l)
        l.append(self.sParClose)
        if self.sComma:
            l.append(self.sComma)
        self.oExp.ToList(stylesheet, l)

# ==============================================================================
class Nullify(BasicStatement):
    def __init__(self, sLabel=None, loc=None, sNullify="NULLIFY",
                 sParOpen='(', nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sNullify  = sNullify
        self.sParOpen  = sParOpen
        self.sParClose = None
        self.lPointers = DoubleList()
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose=')'): self.sParClose=')'
    # --------------------------------------------------------------------------
    def AddExpression(self, exp, sComma=None):
        self.lPointers.append(exp, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.extend([stylesheet.sKeyword(self.sNullify), self.sParOpen])
        self.lPointers.ToList(stylesheet, l)
        l.append(self.sParClose)
# ==============================================================================
class Return(BasicStatement):

    # Stores a return statement.
    def __init__(self, sLabel=None, loc=None, sReturn="RETURN", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sReturn  = sReturn
        self.retvalue = None
    # --------------------------------------------------------------------------
    def SetReturnValue(self, obj):
        self.retvalue = obj
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage):
        if self.retvalue:
            selt.retvalue.GetVarUsage(varUsage)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        if self.retvalue:
            l.append(stylesheet.sKeyword(self.sReturn), nIndentNext=1)
            stylesheet.ToList(self.retvalue, l)
        else:
            l.append(stylesheet.sKeyword(self.sReturn))
# ==============================================================================
class Stop(BasicStatement):
      # Stores a stop statement.
    def __init__(self, sLabel=None, loc=None, sStop="STOP", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sStop    = sStop
        self.stopcode = None
    # --------------------------------------------------------------------------
    def SetStopCode(self, obj):
        self.stopcode = obj
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        if self.stopcode:
            l.append(stylesheet.sKeyword(self.sStop), nIndentNext=1)
            stylesheet.ToList(self.stopcode, l)
        else:
            l.append(stylesheet.sKeyword(self.sStop))
# ==============================================================================
class Pause(Stop):
    # Stores a pause statement - which is similar to a stop statement
    def __init__(self, sLabel=None, loc=None, sPause="PAUSE", nIndent=0):
        Stop.__init__(self, sLabel, loc, sPause, nIndent)
# ==============================================================================
# ==============================================================================
# ==============================================================================
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.StatementsTest import RunTest
    RunTest()
