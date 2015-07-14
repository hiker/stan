#!/usr/bin/env python

import string
from   types              import TupleType
from   AOR.DoubleList     import DoubleList
from   AOR.BasicStatement import BasicStatement, BasicRepr
from   AOR.Statements     import Assignment

# ==============================================================================
# Well, this doesn't really belong in here, but there isn't currently a better
# place - except a separate file. So for now it will remain here.
class Include(BasicStatement):
    def __init__(self, loc=None, sInclude="include", sFilename=None, nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sInclude  = sInclude
        self.sFilename = sFilename
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(self.sInclude)
        l.append(self.sFilename, nIndent=1)
# ==============================================================================
# Stores an intent(...) attribute
class Intent(BasicRepr):
    def __init__(self, sIntent, sParOpen, s, sParClose):
        self.l = [sIntent, sParOpen, s, sParClose]
    # --------------------------------------------------------------------------
    def GetIntent(self): return string.upper(self.l[2])
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.extend(self.l[:])
# ==============================================================================
# Stores a common block name, which can be '', '//', or '/name/'. It is most
# importantly used for the save statement.
class CommonBlockName(BasicRepr):
    def __init__(self, sSlash1=None, sName=None, sSlash2=None):
        self.l = (sSlash1, sName, sSlash2)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if self.l[1]:
            l.extend(list(self.l))
            return
        if self.l[0]:
            if self.l[1]:
                l.extend([self.l[0],self.l[1]])
                return
            l.append(self.l[0])
            return
        return []
# ==============================================================================
class Common(BasicStatement):
    def __init__(self, loc, sCommon="COMMON", nIndent=0, sGlobal=None):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sCommon = sCommon
        self.lName   = []               # List of the names of common blocks
        self.lObj    = []               # List of list of objects in c.b.
        self.sGlobal = sGlobal
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        l=[]
        for i in self.lObj:
            lObjects = i.GetMainList()
            l.extend( map(lambda x: x.oGetVariable(), lObjects) )
        return l
    # --------------------------------------------------------------------------
    # Adds a name of a common block, which is: [ / [ common-block-name ] / ].
    # If the nameless common block is used with //, just don't specify sName,
    # in case that the nameless common block is used without //, calls
    # this function with all parameters = None. Parameters:
    #
    # sComma -- An optional leading comma, e.g.: [[,]/[name]/object-list
    #
    # sSlash1 -- First slash
    #
    # sName -- Name of the common block (if applicable)
    #
    # sSlash2 -- Second ('closing') slash
    def AddCommonBlockName(self, sComma=None, sSlash1=None, sName=None,
                           sSlash2=None):
        self.lName.append( (sComma, CommonBlockName(sSlash1, sName, sSlash2)) )
        self.lObj.append(DoubleList())

    # --------------------------------------------------------------------------
    # Add an object to the last added common block name
    def AddCommonObject(self, obj, sComma=None):
        self.lObj[-1].append(obj, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if self.sGlobal:
            BasicStatement.ToList(self, stylesheet, l)
            l.append(stylesheet.sKeyword(self.sGlobal), nIndentNext=1)
            l.append(stylesheet.sKeyword(self.sCommon), nIndentNext=1)
        else:
            BasicStatement.ToList(self, stylesheet, l)
            l.append(stylesheet.sKeyword(self.sCommon), nIndentNext=1)
        n = 0
        for t in self.lName:
            if t[0]: l.append(t[0])
            stylesheet.ToList(t[1], l)
            self.lObj[n].ToList(stylesheet, l)
            n=n+1
    # --------------------------------------------------------------------------
       
# ==============================================================================
class Namelist(Common):
    def __init__(self, loc, sNamelist="namelist", nIndent=0, sGlobal=None):
        Common.__init__(self, loc=loc, sCommon=sNamelist, nIndent=nIndent,
                        sGlobal=sGlobal)
    # --------------------------------------------------------------------------
    def AddNamelistName(self, sComma=None, sSlash1=None, sName=None,
                        sSlash2=None):
        self.AddCommonBlockName(sComma, sSlash1, sName, sSlash2)
    # --------------------------------------------------------------------------
    # Add an object to the last added namelist
    def AddNamelistObject(self, obj, sComma=None):
        self.AddCommonObject(obj, sComma=None)

# ==============================================================================
# Stores a (pointer-variable, data-variable-declaration) object
class CrayPointerTuple:
    def __init__(self, sParOpen, pointer, sComma, data, sParClose):
        self.l=[sParOpen, pointer, sComma, data, sParClose]
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(self.l[0])
        stylesheet.ToList(self.l[1], l)
        l.append(self.l[2])
        stylesheet.ToList(self.l[3], l)
        l.append(self.l[4])
# ==============================================================================
# POINTER (pointer-variable, data-variable-declaration), ...
class CrayPointer(BasicStatement):
    def __init__(self, loc, sPointer='POINTER', nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sPointer = sPointer
        self.lPointer = DoubleList()
    # --------------------------------------------------------------------------
    def AddPointer(self, pointer, sComma=None):
        self.lPointer.append(pointer, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(self.sPointer, nIndentNext=1)
        self.lPointer.ToList(stylesheet, l)
        
# ==============================================================================
# Stores  / data-stmt-value-list /
class DataValueList(BasicRepr):
    def __init__(self, sSlash1='/'):
        self.sSlash1   = sSlash1
        self.sSlash2   = None
        self.ValueList = DoubleList()
    # --------------------------------------------------------------------------
    def AddValue(self, obj, sComma=None): self.ValueList.append(obj, sComma)
    # --------------------------------------------------------------------------
    def AddSlash(self, sSlash): self.sSlash2 = sSlash
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(self.sSlash1)
        self.ValueList.ToList(stylesheet, l)
        l.append(self.sSlash2)
# ==============================================================================
# Stores [,] data-stmt-object-list / data-stmt-value-list /
# This is part of a data statement (DATA data-stmt-set [ [ , ] data-stmt-set ] )
# Obviously, the first data-stmt-set can not have a ',', but nevertheless
# the same object is used.
class DataStatementSet(BasicRepr):
    def __init__(self, sComma=None):
        self.sComma     = sComma
        self.ObjectList = DoubleList()
        self.DataValue  = None
    # --------------------------------------------------------------------------
    def AddObject(self, obj, sComma=None): self.ObjectList.append(obj, sComma)
    # --------------------------------------------------------------------------
    def AddValueList(self, vl): self.DataValue = vl
    # --------------------------------------------------------------------------
    def AddSecondSlash(self, sSlash): self.sSlash2 = sSlash
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if self.sComma:
            l.append(self.sComma, nIndentNext=1)
        self.ObjectList.ToList(stylesheet, l)
        self.DataValue.ToList(stylesheet,  l)
    
# ==============================================================================
class Data(BasicStatement):
    def __init__(self, loc, sData, nIndent):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sData           = sData
        self.lDataStatements = []
    # --------------------------------------------------------------------------
    def AddDataStatement(self, ds):
        self.lDataStatements.append(ds)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sData), nIndentNext=1)
        for i in self.lDataStatements:
            i.ToList(stylesheet, l)
            l.indent(1)
        
# ==============================================================================
# A (character) variable with a length, e.g. 'character dummy*80' (dummy*80)
class VariableWithLen(BasicRepr):
    def __init__(self, var, sStar=None, len=None):
        self.var      = var
        self.sStar    = sStar
        self.len      = len
        self.lAddStar = None
    # --------------------------------------------------------------------------
    def SetParenthesisStar(self, sParOpen='(', sStar='*', sParClose=')'):
        self.lAddStar=[sParOpen, sStar, sParClose]
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        return self.var.GetAllUsedVariables()
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        
        self.var.ToList(stylesheet, l)
        l.append(self.sStar)
        if self.len:      self.len.ToList(stylesheet, l)
        if self.lAddStar: l.extend(self.lAddStar)

# ==============================================================================
# A variable with an initialisation statement, i.e. a=3 , a /4/, a(2,2)=(1,2,3,4)
class VariableWithInit(BasicRepr):
    def __init__(self, var, sEqual=None, value=None, dataobj=None):
        self.var = var
        if sEqual:
            self.value  = value
            self.sEqual = sEqual
        else:
            self.value  = dataobj
            self.sEqual = None
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        return self.var.GetAllUsedVariables()
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if self.sEqual:
            self.var.ToList(stylesheet, l)
            l.append(self.sEqual)
            self.value.ToList(stylesheet, l)
        else:
            self.var.ToList(stylesheet, l)
            l.indent(1)
            self.value.ToList(stylesheet, l)

# ==============================================================================
# A declaration like integer, allocatable :: a(:)
class Declaration(BasicStatement):
    def __init__(self, sType, sComma=None, loc=None, nIndent=0, var=None,
                 attribute=None):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sType        = sType
        self.sComma       = sComma
        self.lAttributes  = DoubleList()
        self.lColons      = []
        self.lVars        = DoubleList()
        if var:
            self.AppendVariable(var)
        if attribute:
            self.AddAttribute(attribute)
    # --------------------------------------------------------------------------
    # Add a variable or an array specification to the list of declaration
    def AddDeclaredVariable(self, var, sComma=None):
        self.lVars.append(var, sComma)
    # --------------------------------------------------------------------------
    # Add an attribute, like 'allocateable', ...
    def AddAttribute(self, sAtt, sComma=None):
        if len(self.lAttributes)==0 and not self.sComma:
            self.sComma=","
        self.lAttributes.append(sAtt, sComma)
    # --------------------------------------------------------------------------
    # Adds the optional double colon of a declaration. Parameters:
    # 
    # c1/c2 -- Each of the two colons (the scanner returns two colons for a ::)
    def AddDoubleColons(self, c1, c2): self.lColons=[c1,c2]
    # --------------------------------------------------------------------------
    # This function is used to construct new declaration statements:
    def AppendVariable(self, v):
        if len(self.lVars)==0:
            self.lColons=[":",":"]
            self.lVars.append(v)
        else:
            self.lVars.append(",", v)
    # --------------------------------------------------------------------------
    def GetAttributes(self):
        return self.lAttributes.GetMainList()
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        stylesheet.ToList(self.sType, l)
        if self.sComma:
            l.append(self.sComma)
        l.indent(1)
        # The if is not really necessary, but without it two spaces
        # would be added in case of an empy attribute list
        if len(self.lAttributes.GetMainList())>0:
            self.lAttributes.ToList(stylesheet, l, bAddSpace=1)
            l.indent(1)
        if self.lColons:
            l.extend(self.lColons)
            l.indent(1)
        self.lVars.ToList(stylesheet, l, bAddSpace=1)
# ==============================================================================
class Dimension(BasicStatement):
    def __init__(self, loc, sDim="DIMENSION", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.lVars   = DoubleList()
        self.sDim    = sDim
        self.lColons = []
    # --------------------------------------------------------------------------
    def AddDoubleColons(self, c1, c2):
        self.lColons=[c1,c2]
    # --------------------------------------------------------------------------
    def AddArraySpec(self, arrayspec, sComma=None):
        self.lVars.append(arrayspec, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sDim), nIndentNext=1)
        if self.lColons:
            l.extend(self.lColons)
            l.indent(1)
        self.lVars.ToList(stylesheet, l, bAddSpace=1)

# ==============================================================================
# Stores an '(a,b, c(3,4))' expression, which is part of an equivalence
# statement
class EquivalenceItem(BasicRepr):
    def __init__(self, sParOpen):
        self.sParOpen  = sParOpen
        self.l         = DoubleList()
        self.sParClose = ''
    # --------------------------------------------------------------------------
    def AddObject(self, obj, sComma=None): self.l.append(obj, sComma)
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def GetAllEquivalentVariables(self):
        return self.l.GetMainList()
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        l=[]
        for i in self.l.GetMainList():
            l.extend(i.GetAllUsedVariables())
        return l
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(self.sParOpen)
        self.l.ToList(stylesheet, l)
        l.append(self.sParClose)
# ==============================================================================
class Equivalence(BasicStatement):
    def __init__(self, loc, sEq="EQUIVALENCE", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sEq       = sEq
        self.lObjects  = DoubleList()
    # --------------------------------------------------------------------------
    def AddObject(self, obj, sComma=None):
        self.lObjects.append(obj, sComma)
    # --------------------------------------------------------------------------    
    def GetAllUsedVariables(self):
        l=[]
        for i in self.lObjects.GetMainList():
            l.extend(i.GetAllUsedVariables())
        return l
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sEq))
        self.lObjects.ToList(stylesheet, l)
# ==============================================================================
class External(BasicStatement):
   # Stores an external declaration
    def __init__(self, loc, sExternal="EXTERNAL", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sExternal = sExternal
        self.lColon    = []
        self.l         = DoubleList()
    # --------------------------------------------------------------------------
    def AddDoubleColon(self, sCol1, sCol2): self.lColon=[sCol1,sCol2]
    # --------------------------------------------------------------------------
    def AddExternal(self, ext, sComma=None):
        self.l.append(ext, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sExternal), nIndentNext=1)
        if self.lColon:
            l.extend(self.lColon)
        self.l.ToList(stylesheet, l)
# ==============================================================================
class FromTo(BasicRepr):
    def __init__(self, sFrom=None, sDash=None, sTo=None):
        if sDash:
            self.l=[sFrom, sDash, sTo]
        else:
            self.l=[sFrom]
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.extend(self.l[:])                # return a copy
# ==============================================================================
class Implicit(BasicStatement):

    # Stores a parameter declaration
    def __init__(self, sImplicit="IMPLICIT", loc=None, nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sImplicit = sImplicit
        self.sNone     = None
        self.type      = None
        self.l         = DoubleList()
        self.sParOpen  = None
        self.sParClose = None
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen): self.sParOpen = sParOpen
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def SetImplicitNone(self, sNone="NONE"): self.sNone=sNone
    # --------------------------------------------------------------------------
    def isNone(self): return self.sNone!=None
    # --------------------------------------------------------------------------
    def SetType(self, type): self.type=type
    # --------------------------------------------------------------------------
    def AddLetter(self, sFrom, sDash=None, sTo=None, sComma=None):
        self.l.append(FromTo(sFrom, sDash, sTo), sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sImplicit),nIndentNext=1)
        if self.sNone:
            l.append(stylesheet.sKeyword(self.sNone))
            return
        stylesheet.ToList(self.type, l)
        l.append(self.sParOpen)
        self.l.ToList(stylesheet, l)
        l.append(self.sParClose)
                    
# ==============================================================================
class Intrinsic(BasicStatement):
    # Stores an intrinsic declaration
    def __init__(self, loc, sIntri="INTRINSIC", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sIntri  = sIntri
        self.lColons = None
        self.l       = DoubleList()
    # --------------------------------------------------------------------------
    def AddDoubleColons(self, c1, c2): self.lColons=[c1,c2]
    # --------------------------------------------------------------------------
    def AddIntrinsic(self, obj, sComma=None): self.l.append(obj, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sIntri),nIndentNext=1)
        if self.lColons:
            l.extend(self.lColons)
        self.l.ToList(stylesheet, l)
# ==============================================================================
class Parameter(BasicStatement):

    # Stores a parameter declaration
    def __init__(self, loc, sParam="PARAMETER", nIndent=0, sParOpen="("):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sParam    = sParam
        self.l         = DoubleList()
        self.sParOpen  = sParOpen
        self.sParClose = None
    # --------------------------------------------------------------------------
    def AddVarValue(self, var, sEqual, obj, sComma=None):
        a=Assignment(sLabel=None, loc=None, nIndent=0, lhs=var,
                     sEqual=sEqual, rhs=obj, bNoIndent=1)
        self.l.append(a, sComma)
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose=sParClose
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sParam))
        l.append(self.sParOpen)
        self.l.ToList(stylesheet, l)
        l.append(self.sParClose)
                    
# ==============================================================================
# pointer-stmt is POINTER [ :: ] pointer-decl-list
class Pointer(BasicStatement):
    def __init__(self, loc, sPointer='POINTER', nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sPointer = sPointer
        self.lPointer = DoubleList()
        self.lColons  = None
    # --------------------------------------------------------------------------
    def AddDoubleColons(self, c1, c2): self.lColons=[c1,c2]
    # --------------------------------------------------------------------------
    def AddPointer(self, pointer, sComma=None):
        self.lPointer.append(pointer, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(self.sPointer)
        if self.lColons:
            l.indent(1)
            l.extend(self.lColons)
        l.indent(1)
        self.lPointer.ToList(stylesheet, l)
    
# ==============================================================================
class ModuleProcedure(BasicStatement):
    def __init__(self, loc, sModule=None, sProcedure="PROCEDURE", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sModule    = sModule
        self.sProcedure = sProcedure
        self.l          = DoubleList()
    # --------------------------------------------------------------------------
    def AddProcedure(self, obj, sComma=None): self.l.append(obj, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        if self.sModule:
            l.append(self.sModule,    nIndentNext=1)
            l.append(self.sProcedure, nIndentNext=1)
        else:
            l.append(self.sProcedure, nIndentNext=1)
        self.l.ToList(stylesheet, l)
        
# ==============================================================================
class Public(BasicStatement):
    # Stores a public statement declaration
    def __init__(self, loc, sPublic="PUBLIC", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sPublic = sPublic
        self.lColons = None
        self.l       = DoubleList()
    # --------------------------------------------------------------------------
    def AddDoubleColons(self, c1, c2): self.lColons=[c1,c2]
    # --------------------------------------------------------------------------
    def AddObject(self, obj, sComma=None): self.l.append(obj, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sPublic), nIndentNext=1)
        if self.lColons:
            l.extend(self.lColons)
        self.l.ToList(stylesheet, l)
# ==============================================================================
class Private(Public):
    def __init__(self,  loc, sPrivate="PRIVATE", nIndent=0):
        Public.__init__(self, loc, sPrivate, nIndent)
# ==============================================================================
class Save(BasicStatement):

    # Stores a parameter declaration
    def __init__(self, loc, sSave="SAVE", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sSave   = sSave
        self.lColons = None
        self.l       = DoubleList()
    # --------------------------------------------------------------------------
    def AddDoubleColons(self, c1, c2): self.lColons=[c1,c2]
    # --------------------------------------------------------------------------
    def AddCommonBlock(self, sSlash1, obj, sSlash2, sComma=None):
        self.l.append(CommonBlockName(sSlash1, obj, sSlash2), sComma)
    # --------------------------------------------------------------------------
    def AddObject(self, obj, sComma=None):
        self.l.append(obj, sComma)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sSave), nIndentNext=1)
        if self.lColons:
            l.extend(self.lColons)
        self.l.ToList(stylesheet, l)
# ==============================================================================
# Stores a type, i.e. either a basic type (and kind information)
# or a user-defined type. This can also be a type like 'character*8',
# 'integer*8', 'character*(*)', or character*(kind=3, len=*)
class Type(BasicRepr):

    # Constructor. Parameters:
    #
    # sType -- The basic type
    #
    # sType2 -- Used for double precision
    #
    def __init__(self, sType, sType2=None):
        self.sType  = sType
        self.sType2 = sType2
        self.sStar  = None
        self.len    = None
        self.lKind  = []
    # --------------------------------------------------------------------------
    def bIsType(self, sType):
        return string.upper(self.sType)==string.upper(sType)
    # --------------------------------------------------------------------------
    def SetStar(self, sStar): self.sStar = sStar
    # --------------------------------------------------------------------------
    def SetLen(self, l) : self.lKind = [l]
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen): self.lKind.append(sParOpen)
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.lKind.append(sParClose)
    # --------------------------------------------------------------------------
    # Adds the kind information: Either '(5)', or '(kind=5)'
    def AddKindOrLen(self, sKeyword=None, sEqual=None, obj=None, sComma=None):
        if sKeyword:
            self.lKind.append( (sKeyword, sEqual, obj) )
        else:
            self.lKind.append(obj)
        if sComma: self.lKind.append(sComma)
    # --------------------------------------------------------------------------
    # The tuple t is either (keyword,'=',exp) or a single exp obj. This will
    # return a tuple where the keyword is handled by the stylesheet
    def HandleKeywords(self, t, stylesheet, l):
        if type(t)==TupleType:
            l.append(stylesheet.sKeyword(t[0]))
            l.append(t[1])
            stylesheet.ToList(t[2], l)
        else:
            stylesheet.ToList(t, l)
    # --------------------------------------------------------------------------
    # Convert a basic type into a list.
    def ToList(self, stylesheet, l):
        l.append(stylesheet.sKeyword(self.sType))
        if self.sType2:
            l.append(stylesheet.sKeyword(self.sType2))
        if self.sStar:
            l.append(self.sStar)

        if not self.lKind:
            return
        # E.g. integer *8
        if len(self.lKind)==1:
            stylesheet.ToList(self.lKind[0], l)
        # E.g. (4)  or (KIND=4), since ('KIND','=',4) is a single tuple.
        elif len(self.lKind)==3:
            l.append(self.lKind[0])                             # (
            self.HandleKeywords(self.lKind[1], stylesheet, l)   # 3
            l.append(self.lKind[2])                             # )
        # E.g. (3, len=5)
        else:
            l.append(self.lKind[0])                             # (
            self.HandleKeywords(self.lKind[1],stylesheet, l)    # 4
            l.append(self.lKind[2])                             # ,
            self.HandleKeywords(self.lKind[3], stylesheet, l)   # 5 
            l.append(self.lKind[4], nIndentNext=1)              # )
    
# ==============================================================================
class UserType(BasicRepr):
    # Stores a user defined type
    def __init__(self, sType="TYPE", sParOpen='(', sSubType=None, sParClose=')'):
        self.sTypeString = sType
        self.sParOpen    = sParOpen
        self.type        = sSubType
        self.sParClose   = sParClose
    # --------------------------------------------------------------------------
    def bIsType(self, sType):
        return self.type.bIsType(sType)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(stylesheet.sKeyword(self.sTypeString))
        l.append(self.sParOpen)
        stylesheet.ToList(self.type, l)
        l.append(self.sParClose)
# ==============================================================================
# A simple rename within a use statement: 'a=>b'
class RenameVar(BasicRepr):
    def __init__(self, sFrom, sArrow, oTo):
        self.l=[sFrom, sArrow, oTo]
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.extend([self.l[0], self.l[1]])
        stylesheet.ToList(self.l[2], l)
# ==============================================================================
class StatementFunction(BasicStatement):

    def __init__(self, sLabel=None, loc=None, nIndent=0, lhs=None,
                 sEqual=None, rhs=None, bNoIndent=None):
        BasicStatement.__init__(self, sLabel, loc, nIndent)
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
    def ToList(self, stylesheet, l):
        if not self.bNoIndent:
            BasicStatement.ToList(self, stylesheet, l)
        stylesheet.ToList(self.lhs, l)
        l.indent(1)
        l.append(self.sEqual, nIndentNext=1)
        stylesheet.ToList(self.rhs, l)
# ==============================================================================
class Use(BasicStatement):
    # Constructor. Parameters:
    #
    # sub -- progunit Object, used to store variables in
    def __init__(self, loc, sUse="USE", nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.sUse        = sUse
        self.lNature     = []
        self.lColons     = []
        self.lOnly       = DoubleList()
        self.lOnlyString = ''
        self.lRename     = DoubleList()
        self.sComma      = None
        self.sName       = None
    # --------------------------------------------------------------------------
    # Returns the name of the module
    def GetName(self): return self.sName
    # --------------------------------------------------------------------------
    # Returns true if this is a 'use only' use statement
    def IsOnly(self): return len(self.lOnly)>0
    # --------------------------------------------------------------------------
    # Returns a list of all imported entries from a module
    def GetOnlyList(self):
        return self.lOnly
    # --------------------------------------------------------------------------
    # Returns true if this has a rename list
    def HasRename(self): return len(self.lRename)>0
    # --------------------------------------------------------------------------
    # Returns a list of tuples (from,to) for all renamed entries
    def GetRenameList(self):
        l=[]
        for i in self.lRename:
            l.append( (i[0], i[1]) )
        return l
    # --------------------------------------------------------------------------
    def SetNature(self, sComma, sNature): self.lNature=[sComma, sNature]
    # --------------------------------------------------------------------------
    # Adds the optional double colon of an use statement. Parameters:
    # 
    # c1/c2 -- Each of the two colons (the scanner returns two colons for a ::)
    def AddDoubleColon(self, c1, c2): self.lColons=(c1,c2)
    # --------------------------------------------------------------------------
    # Sets the module name to import from. Parameter:
    #
    # sName -- Name
    def SetName(self, sName):
        self.sName=sName
    # --------------------------------------------------------------------------
    # Adds the comma which comes before a "ONLY" or a rename list
    def AddComma(self, sComma): self.sComma=sComma
    # --------------------------------------------------------------------------
    # Adds the comma, the 'only' string, and the colon. If this function was
    # called, no rename function  (AddRenameComma/AddRename) should be called.
    def AddOnlyString(self, sOnly="ONLY", sColon=":"):
        self.lOnlyString=[sOnly, sColon]
    # --------------------------------------------------------------------------
    # Adds a 'only' import plus (optionally) a comma
    def AddOnly(self, var, sComma=None): self.lOnly.append(var, sComma)
    # --------------------------------------------------------------------------
    # Adds a rename statement, i.e. the ", from => to" part - including the
    # comma!
    def AddRename(self, sFrom, sArrow, varTo, sComma=None):
        self.lRename.append( RenameVar(sFrom, sArrow, varTo), sComma )
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.sUse), nIndentNext=1)
        if self.lNature: l.extend(self.lNature)
        if self.lColons:
            l.extend(self.lColons)
            l.indent(1)
        l.append(self.sName)
        # If it's an 'only' use statement
        if self.sComma: l.append(self.sComma)
        if self.lOnly:
            l.extend(self.lOnlyString)
            self.lOnly.ToList(stylesheet, l)
        else:
            self.lRename.ToList(stylesheet, l)
                        
                           
# ==============================================================================
# ==============================================================================
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.UseTest import RunTest
    RunTest()
