#!/usr/bin/env python

import string
from   AOR.Variables        import Variables
from   AOR.BasicStatement   import BasicStatement, BasicRepr
from   AOR.If               import IfOnly
from   Stylesheets.Default  import DefaultStylesheet
from   Stylesheets.Layout2d import Layout2d

class ProgUnit(Variables, list, BasicRepr):
    # Constructor for a program unit object. Parameter:
    #
    # sType -- Type of the program unit (subroutine, function, program)
    #
    # sName -- Name of unit
    #
    # nLine -- Line number
    #
    # nColumn -- Column number
    #
    def __init__(self, obj=None):
        self._bIsExec         = 0
        Variables.__init__(self)
        if obj:
            self.nLastDeclaration = 1
            list.__init__(self, [obj])
        else:
            self.nLastDeclaration = 0
            list.__init__(self)
        self.contains         = None
        self.oContainedIn     = None
        self.lContains        = []
        self.lCalls           = []
        self.lFuncCalls       = []
        # The StatementIndex contains the index position of all real Fortran
        # statements. Most function will only access these statements (and not
        # comment lines, directive lines, ...), so the default is to return
        # only statements. Separate functions (oGetLine(), lGetLines()) must be
        # used if all statements are needed.
        self.lAllStatements  = []
    # --------------------------------------------------------------------------
    def delete(self, i):
        return self.remove(i)
    # --------------------------------------------------------------------------
    def __getitem__(self, n):
        return self.lAllStatements[n]
    # --------------------------------------------------------------------------
    def oGetLine(self,n):
        return list.__getitem__(self, n)
    # --------------------------------------------------------------------------
    def lGetLines(self,n):
        return self[:]
    # --------------------------------------------------------------------------
    # Renamed from 'append'. If append is overwritten here, this object (for
    # whatever reasons) can't be deepcopied anymore (apparently deepcopy calls
    # append, before setting _bIsExec, so that append fails).
    def AppendStatement(self, d):
        if self._bIsExec:
            list.append(self,d)
        else:
            self.AddDeclaration(d)
        # If its a real statement, add the index to the statement index list
        if d.isStatement():
            self.lAllStatements.append(d)
    # --------------------------------------------------------------------------
    # Adds a declaration (or a list of declarations) at the right place of the
    # program unit.
    def AddDeclaration(self, d):
        # Support for adding a list of declarations
        if type(d)==type([]):
            for i in d:
                self.AddDeclaration(i)
            return
        if len(self)==self.nLastDeclaration:
            list.append(self, d)
            self.nLastDeclaration = len(self)
        else:
            self.insert(self.nLastDeclaration,d)
            self.nLastDeclaration = self.nLastDeclaration+1
    # --------------------------------------------------------------------------
    def SetIsExec(self, b): self._bIsExec = b
    # --------------------------------------------------------------------------
    def bIsExec(self): return self._bIsExec
    # --------------------------------------------------------------------------
    # The name is stored in the first statement, which is the subroutine-,
    # function-, ... -statement
    def sGetName(self): return self[0].GetName()
    # --------------------------------------------------------------------------
    # Return the type of a program unit, i.e.:  'module', 'subroutine',
    # 'program', 'function', 'blockdata'
    def sGetType(self): return self.__class__.__name__.lower()
    # --------------------------------------------------------------------------
    # Inserts a statement before (or after) another statement. This must be a
    # pointer to a statement, not a line number!
    def Insert(self, statement, before=None, after=None):
        # Support lists of statements, so simple statements are treated
        # as 1-element lists.
        if type(statement) != type([]):
            statement = [statement]
            
        if not before:
            if not after:
                self.extend(statement)
                return
            sToFind = after
            nDelta  = 1
        else:
            sToFind = before
            nDelta  = 0

        # First insert in list of all lines
        # ---------------------------------
        nCount = 0
        for i in self:
            if i == sToFind:
                for j in range(len(statement)-1, -1, -1):
                    self.insert(nCount+nDelta, statement[j])
                break
            nCount = nCount + 1
        nCount = 0

        # Then insert in lists of all statements (i.e. without comments etc)
        # ------------------------------------------------------------------
        for i in self.lAllStatements:
            if i == sToFind:
                for j in range(len(statement)-1, -1, -1):
                    if(statement[j].isStatement()):
                        self.lAllStatements.insert(nCount+nDelta, statement[j])
                return
            nCount = nCount + 1
                
        # No insertion point found
        # ------------------------
        self.extend(statement)
        return -nCount
        
    # --------------------------------------------------------------------------
    def AddExecution  (self, e): self.append(e)
    # --------------------------------------------------------------------------
    def AddEnd        (self, e): self.append(e)
    # --------------------------------------------------------------------------
    # Adds an argument of a program unit. Each argument is stored as an id
    # only (pointer to variable object), so that variables can easily be renamed
    def AddArgument(self, sName, d=None, sComma=None):
        if d==None: d={}
        d["argument"]=1
        var=Variables.GetVariable(self, sName, d, bAutoAdd=1)
    # --------------------------------------------------------------------------
    # Adds the actual 'contain' statements
    def SetContainStatement(self, contains):
        self.contains = contains
    # --------------------------------------------------------------------------
    # Appends a contained subroutine/function
    def AddContained(self, obj):
        self.lContains.append(obj)
        obj.SetContainedIn(self)
    # --------------------------------------------------------------------------
    # If this subroutine is contained in another subroutine, a pointer
    # to this other subroutine is stored.
    def SetContainedIn(self, obj): self.oContainedIn = obj
    # --------------------------------------------------------------------------
    def bContains(self): return self.olContains
    # --------------------------------------------------------------------------
    def GetArguments(self): return self[0].GetArguments()
    # --------------------------------------------------------------------------
    def GetPrefix(self): return self[0].GetPrefix()
    # --------------------------------------------------------------------------
    def GetVariable(self, sName, d={}, bAutoAdd=1):
        var =  Variables.GetVariable(self, sName, d=d, bAutoAdd=0)
        if var: return var

        if self.oContainedIn:
            var=self.oContainedIn.GetVariable(sName, bAutoAdd=0)
            
        if not var:
            if bAutoAdd:
                return Variables.GetVariable(self, sName, d=d, bAutoAdd=1)
        return var

    # --------------------------------------------------------------------------
    def GetAttributes(self, sName):
        var=self.GetVariable(sName, bAutoAdd=0)
        if not var: return {}
        return var.GetAttributes()    
    # --------------------------------------------------------------------------
    # lCalls contains a list of all subroutine/function calls, the locations it
    # occurs, and the type ('subroutine'/'function').
    def AddFunctionCall(self, sName, loc):
        self.lFuncCalls.append( (sName, loc) )
    # --------------------------------------------------------------------------
    # lCalls contains a list of all subroutine/function calls, the locations it
    # occurs, and the type ('subroutine'/'function').
    def AddCall(self, sName, loc, type):
        self.lCalls.append( (sName, loc) )
    # --------------------------------------------------------------------------
    def lContainedProgUnits(self): return self.lContains
    # --------------------------------------------------------------------------
    def lGetFunctionCalls(self):   return self.lFuncCalls
    # --------------------------------------------------------------------------
    def lGetCalls(self):           return self.lCalls
    # --------------------------------------------------------------------------
    def lGetAllCalls(self):        return self.lCalls + self.lFuncCalls
    # --------------------------------------------------------------------------
    # Copies the declaration from this program unit to the program unit
    # 'progunit'. If var is specified, only the variable 'var' will be
    # copied, if in addition renamedTo is specified, the variable will be
    # named 'renamedTo' in 'progunit'
    def CopyDeclarationTo(self, progunit, sVar=None, sRenamedTo=None):
        if not sVar:
            for var in self.lGetAllVariables():
                dAttr = var.GetAttributes()
                progunit.AddVariable(var.sGetName(), dAttr)
            return
        if sRenamedTo:
            dAttr=self.GetAttributes(sVar)
            v=progunit.AddVariable(sRenamedTo, dAttr)
            return
        dAttr=self.GetAttributes(sVar)
        progunit.AddVariable(sVar, dAttr)
        
    # --------------------------------------------------------------------------
    # Returns a list of all statements of the program unit (this is basically
    # a copy of the program unit object). If lClasses is specified, only
    # statements which are of a class specified in that list will be returned.
    # Example:
    # from AOR.Statements import Call
    # from AOR.Do import Do, EndDo
    #     for i in objFile:
    #         for j in i.lGetStatements([Call, Do, EndDo]):
    #             print j
    # Parameter:
    #
    # lClasses -- List of statement classes. If this is specified, only
    #             statements belonging to one of the classes of this list
    #             are returned. If this parameter is not specified (or None),
    #             a list of all statements is returned.
    #
    # bExtractIfOnly -- If statements without a then (called ifonly here) have
    #             a statement attached to them. With this flag it can be chosen
    #             whether these statements in ifonly statements are to be
    #             returned or not. The function is probably faster if they are
    #             not to be returned. Example (consider that IfOnly is NOT an
    #             If object!!):
    #             ProgUnit is [if (a.eq.1) call sub(a)]
    #             lGetStatements(...,lClasses=[If, Call])
    #                    -> [call sub(a)]
    #             lGetStatements(...,lClasses=[IfOnly, Call])
    #                    -> [if (a.eq.1) call sub(a)]
    #                       the Call is not returned twice in the list!
    #             lGetStatements(...,lClasses=[If, Call], bExtractIfOnly=0)
    #                    -> []
    #                       because the call statement in the IfOnly statement
    #                       is not returned
    #             lGetStatements(...,lClasses=[IfOnly], bExtractIfOnly=0)
    #                    -> [if (a.eq.1) call sub(a)]
    def lGetStatements(self, lClasses = None, bExtractIfOnly=1):
        if lClasses==None:
            return self[:]
        # Convert to a dictionary for faster access
        d = {}
        for i in lClasses:
            d[i]=1
        # We can use the faster filter function here
        if not bExtractIfOnly:
            return filter(lambda x, d=d: d.get(x.__class__,None), self)
        # Now we have to loop over all statements and check for IfOnly
        l = []
        for i in self:
            if d.get(i.__class__, None):
                l.append(i)
            else:
                if i.__class__==IfOnly:
                    s = i.GetStatement()
                    if d.get(s.__class__, None): l.append(s)
        return l
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if not self.lContains:
            for i in self:
                l2dDummy = Layout2d()
                stylesheet.ToList(i, l2dDummy)
                l.append(l2dDummy)
            return
        for i in self[:-1]:
            l2dDummy = Layout2d()
            stylesheet.ToList(i, l2dDummy)
            l.append(l2dDummy)
        l2dDummy = Layout2d()
        stylesheet.ToList(self.contains, l2dDummy)
        l.append(l2dDummy)
        for sub in self.lContains:
            stylesheet.ToList(sub, l)
        l2dDummy = Layout2d()
        stylesheet.ToList(self[-1], l2dDummy)
        l.append(l2dDummy)
    # --------------------------------------------------------------------------
    def __repr__(self):
        return self.ToString(DefaultStylesheet())
    
# ==============================================================================
# For storing incomplete files, e.g. include files which only store information
# about a common block. They don't have a name, prefix, ...
class IncompleteProgUnit(ProgUnit):
    def __init__(self):
        ProgUnit.__init__(self)
    # --------------------------------------------------------------------------
    def sGetName(self): return ""
    # --------------------------------------------------------------------------
    def GetArguments(self): return []
    # --------------------------------------------------------------------------
    def sGetPrefix(self): return []
# ==============================================================================
class EndProgUnit(BasicStatement):

    # Stores an end-{program, subroutine, function} statement:
    # end-program-stmt	is END [ PROGRAM [ program-name ] ]
    # end-subroutine-stmt is END [ SUBROUTINE [ subroutine-name ] ]
    # end-function-stmt	is END [ FUNCTION [ function-name ] ]
    def __init__(self, sLabel=None, loc=None, sEnd="END", nIndent=0, sName=None):
        self.sEnd  = sEnd
        self.sType = None
        self.sName = sName
        BasicStatement.__init__(self, sLabel, loc, nIndent)
    # --------------------------------------------------------------------------
    # Is sName is none, only 'subroutine' will be appended
    def SetName(self, sType, sName=None):
        self.sType = sType
        self.sName = sName
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sEnd))
        if self.sType: l.append(stylesheet.sKeyword(self.sType), nIndent=1)
        if self.sName: l.append(self.sName,                      nIndent=1)
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.ProgUnitTest import RunTest
    RunTest()
