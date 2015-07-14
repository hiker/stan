#!/usr/bin/env python

import string
from   types              import StringType, IntType
from   AOR.DoubleList     import DoubleList
from   AOR.BasicStatement import BasicStatement, BasicRepr

# ==============================================================================
# Stores an io-implied do list
class IODoList(BasicRepr):
    # Stores '(obj1, obj2, ..., objn, i=1, n)
    def __init__(self,sParOpen, obj1, sComma1):
        self.sParOpen    = sParOpen
        self.sParClose   = None
        self.lObj        = DoubleList(l1=[obj1], l2=[sComma1])
        self.lLoopData =  []             # stores: [var,'=',from',',to]
                                          # and maybe [',',stride]
    # --------------------------------------------------------------------------
    # Sets the implied do variable and the equal sign
    def SetVar(self, v, sEqual): self.lLoopData.extend([v, sEqual])
    # --------------------------------------------------------------------------
    def SetFrom(self,f,sComma): self.lLoopData.extend([f,sComma])
    # --------------------------------------------------------------------------
    def SetTo(self,t): self.lLoopData.append(t)
    # --------------------------------------------------------------------------
    def SetStep(self,sComma, s): self.lLoopData.extend([sComma,s])
    # --------------------------------------------------------------------------
    def AddExpr(self, e, sComma): self.lObj.append(e, sComma)
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.lObj.GetMainList():
            varUsage.AddVariable(i, sType, obj, loc)
        varUsage.AddVariable(self.lLoopData[0], "write", obj, loc)
        varUsage.AddVariable(self.lLoopData[2], "read",  obj, loc)
        varUsage.AddVariable(self.lLoopData[4], "read",  obj, loc)
        if len(self.lLoopData)>5:
            varUsage.AddVariable(self.lLoopData[6], "read", obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(self.sParOpen)
        self.lObj.ToList(stylesheet, l)
        stylesheet.ToList(self.lLoopData[0], l)      # var
        l.append(self.lLoopData[1])                  # =
        stylesheet.ToList(self.lLoopData[2], l)      # from
        l.append(self.lLoopData[3])                  # ,
        stylesheet.ToList(self.lLoopData[4], l)      # to
        if len(self.lLoopData)>5:
            l.append(self.lLoopData[5])              # ,
            stylesheet.ToList(self.lLoopData[6], l)  # step
        l.append(self.sParClose)

# ==============================================================================
# Basic class for  each statement of the form KEYWORD ([a=]b, [c=]d)
# (or without () ).
class BasicIOList(BasicStatement):
    def __init__(self, sLabel=None, loc=None, nIndent=0, sKeyword="",
                 sParOpen=None, opt=None):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sKeyword  = sKeyword
        self.sParOpen  = sParOpen
        self.sParClose = ')'
        self.lParams   = DoubleList()
        if opt: self.AddIOOpt(opt)
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen='('): self.sParOpen = sParOpen
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose=')'): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def AddIOOpt(self, exp, sComma=None):
        if type(exp)==type(1): exp=`exp`
        self.lParams.append(exp, sComma)
    # --------------------------------------------------------------------------
    def sGetParClose(self): return self.sParClose
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.lParams.GetMainList():
            varUsage.AddVariable(i, "unknown", obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sKeyword))
        if self.sParOpen:
            l.append(self.sParOpen)
            self.lParams.ToList(stylesheet, l),
            l.append(self.sParClose)
# ==============================================================================
class Close(BasicIOList):
    # Stores a close statement
    def __init__(self, sLabel=None, loc=None, nIndent=0,
                 sClose="CLOSE", sParOpen='(', nUnit=None):
        BasicIOList.__init__(self, sLabel, loc, nIndent, sClose, sParOpen)
        if nUnit:
            self.AddIOOpt(nUnit)
 
# ==============================================================================
class Format(BasicStatement):

    # Stores a format statement.
    def __init__(self, sLabel=None, loc=None, sFormat="FORMAT", nIndent=0):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sFormat = sFormat
        self.l       = []
    # --------------------------------------------------------------------------
    def append(self, e): self.l.append(e)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.extend([stylesheet.sKeyword(self.sFormat)]+self.l[:])
# ==============================================================================
class Print(BasicStatement):

    # Stores a return statement.
    def __init__(self, sLabel=None, loc=None, sPrint="PRINT", nIndent=0,
                 format=None):
        BasicStatement.__init__(self, sLabel, loc, nIndent, isDeclaration=0)
        self.sPrint  = sPrint
        self.format  = format
        if format:
            self.sComma  = ","              # First comma after format
        else:
            self.sComma  = None             # First comma after format
        self.lIO     = DoubleList()
    # --------------------------------------------------------------------------
    def AddIOExpression(self, e, sComma=None): self.lIO.append(e, sComma)
    # --------------------------------------------------------------------------
    def SetComma(self, sComma): self.sComma=sComma
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.lIO.GetMainList():
            varUsage.AddVariable(i, sType, obj, loc)
    # --------------------------------------------------------------------------
    def SetFormat(self, format):
        self.format = format
        self.sComma = ","
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sPrint),nIndentNext=1)
        if type(self.format)==StringType:
            l.append(self.format)
        elif type(self.format)==IntType:
            l.append(`self.format`)
        else:
            stylesheet.ToList(self.format, l)
        if not self.sComma: return 
        l.append(self.sComma)
        self.lIO.ToList(stylesheet, l)
        
# ==============================================================================
class Rewind(BasicIOList):
    # Stores a rewind statement
    def __init__(self,  sLabel=None, loc=None, nIndent=0, sRewind="REWIND"):
        BasicIOList.__init__(self, sLabel, loc, nIndent, sRewind,sParOpen=None)
        self.sUnitNumber = None
    # --------------------------------------------------------------------------
    def AddUnitNumber(self, sUnitNumber): self.sUnitNumber = sUnitNumber
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicIOList.ToList(self, stylesheet, l)
        if self.sUnitNumber:
            l.append(self.sUnitNumber, nIndent=1)
# ==============================================================================
class Backspace(Rewind):
    # Stores a backspace statement - which is basically identical to a rewind
    def __init__(self,  sLabel=None, loc=None, nIndent=0,
                 sBackspace="BACKSPACE"):
        Rewind.__init__(self, sLabel ,loc, nIndent, sRewind=sBackspace)
# ==============================================================================
class Endfile(Rewind):
    # Stores a endfile statement - which is basically identical to a rewind
    def __init__(self,  sLabel=None, loc=None, nIndent=0,
                 sEndfile="ENDFILKE"):
        Rewind.__init__(self, sLabel ,loc, nIndent, sRewind=sEndfile)
# ==============================================================================
class Open(BasicIOList):
    # Stores an open statement
    def __init__(self, sLabel=None, loc=None, nIndent=0, sOpen="OPEN",
                 sParOpen='(', nUnit=None):
        BasicIOList.__init__(self, sLabel, loc, nIndent, sOpen, sParOpen,
                             opt=nUnit)
# ==============================================================================
class Read(BasicIOList):
    # Stores a read statement
    def __init__(self, sLabel=None, loc=None, nIndent=0,
                 sRead="READ", sParOpen=None,
                 nUnit=None, var=None):
        BasicIOList.__init__(self, sLabel, loc, nIndent, sRead, sParOpen)
        self.lIOExp    = DoubleList()
        self.sFormat   = None
        self.sComma    = None
        if nUnit:
            if not sParOpen: self.SetParOpen()
            self.AddIOOpt("%s"%nUnit)
            self.SetParClose()
        if var:
            self.AddIOExpression(var)
    # --------------------------------------------------------------------------
    def SetFormat(self, sFormat, sComma=None):
        self.sFormat = sFormat
        self.sComma  = sComma
    # --------------------------------------------------------------------------
    def AddIOExpression(self, exp, sComma=None):
        # To simplify manually creating statements, a comma is automatically
        # added, if only expressions are specified here (except for the first
        # call).
        if type(exp)==type(1): exp=`exp`
        if sComma==None and \
               len(self.lIOExp.lGetSecondaryList())==len(self.lIOExp)-1:
            self.lIOExp.append(",", exp)
        else:
            self.lIOExp.append(exp, sComma)
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.lIOExp.GetMainList():
            varUsage.AddVariable(i, "write", obj, loc)
        BasicIOList.GetVarUsage(self, varUsage, sType, obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicIOList.ToList(self, stylesheet, l)
        l.append(' ')
        if self.sFormat:
            l.append(self.sFormat, nIndent=1)
            if self.sComma:
                l.append(self.sComma)
        self.lIOExp.ToList(stylesheet, l)
# ==============================================================================
class Write(Read):
    # Stores a write statement. Read and writes are basically identical,
    # except that read can have a format instead of a () expression
    def __init__(self, sLabel=None, loc=None, nIndent=0,
                 sWrite="WRITE", sParOpen=None, nUnit=None):
        Read.__init__(self, sLabel, loc, nIndent,
                      sRead=sWrite, sParOpen=sParOpen, nUnit=nUnit)
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.lIOExp.GetMainList():
            varUsage.AddVariable(i, "read", obj, loc)
        BasicIOList.GetVarUsage(self, varUsage, sType, obj, loc)
# ==============================================================================
class Inquire(Read):
    # Stores an inquire statement. Inquire, read and writes are basically
    # identical.
    def __init__(self, sLabel=None, loc=None, nIndent=0,
                 sInquire="INQUIRE", sParOpen=None):
        Read.__init__(self, sLabel, loc, nIndent, sInquire, sParOpen)
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.AllocateTest import RunTest
    RunTest()
