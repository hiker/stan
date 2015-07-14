#!/usr/bin/env python

import string
from   types                import TupleType, StringType, ListType
from   AOR.BasicStatement   import BasicRepr
from   AOR.DoubleList       import DoubleList
from   AOR.AttributeString  import AttributeString
from   Stylesheets.Layout2d import Division2d, Layout2d
import Variable 

# ==============================================================================
# This class is the basic class for most of the expression classes.
# It stores a sequence like 'object operator object operator object ...'
# For example 'a + b + c' (where a, b, and c are variable objects)
#
class BasicExpression(BasicRepr):
    def __init__(self, o=None, operator=None, o2=None):
        self.l = DoubleList()
        if o:
            if operator:
                self.l.append(o, operator)
                if o2:
                    self.l.append(o2)
            else:
                self.l.append(o)

    # --------------------------------------------------------------------------
    def append(self, obj, sOperator=None):
        self.l.append(obj, sOperator)
    # --------------------------------------------------------------------------
    # Returns a list of all used variables in this expression
    def GetAllUsedVariables(self):
        l=[]
        for i in self.l.GetMainList():
            if isinstance(i,Variable.Variable):
                l.append(i)
            else:
                l.extend(i.GetAllUsedVariables())
        return l
    # --------------------------------------------------------------------------
    # In this case all variables MUST be read expression, since an expression
    # can't be written.
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.l.GetMainList():
            varUsage.AddVariable(i, "read", obj, loc)
    # --------------------------------------------------------------------------
    def lGetAsSimpleList(self):
        return self.l.lGetAsSimpleList()
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l2d):
        self.l.ToList(stylesheet, l2d)
# ==============================================================================
class Expression(BasicExpression):
    def __init__(self, o=None, operator=None, o2=None):
        BasicExpression.__init__(self, o=o, operator=operator, o2=o2)

# ==============================================================================
# A mult and division expression
class MultExpression(Expression):
    def __init__(self):
        Expression.__init__(self)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l2d):
        if not stylesheet["mathsmode"] or not stylesheet["dodiv"]:
            self.l.ToList(stylesheet, l2d)
            return
        
        # Now it is mathsmode
        # -------------------
        for i in self.l.lGetSecondaryList():
            if i=="/":
                # Division found, do special maths processing
                return stylesheet.HandleDivision(self, l2d)
        else:
            # No division in this expression, use normal processing
            self.l.ToList(stylesheet, l2d)

# ==============================================================================
# A power expression: a ** b
class PowerExpression(Expression):
    def __init__(self):
        Expression.__init__(self)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l2d):
        if stylesheet["mathsmode"] and stylesheet["dopower"]:
            stylesheet.HandlePower(self, l2d)
        else:
            self.l.ToList(stylesheet, l2d)
    
# ==============================================================================
# Stores a 'not' expression
class UnaryExpression(BasicRepr):
    def __init__(self, sOperator, obj):
        self.l = [sOperator, obj]
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        return self.l[1].GetAllUsedVariables()
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        varUsage.AddVariable(self.l[1], sType, obj, loc)
    # -------------------------------------------------------------------------- 
    def ToList(self, stylesheet, l):
        l.append(self.l[0])
        stylesheet.ToList(self.l[1], l)
# ==============================================================================
# Stores a (expression) expression
class ParenthesisExpression(BasicRepr):
    def __init__(self, sParOpen="(", obj=None, sParClose=")"):
        self.l = [sParOpen, obj, sParClose]
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        return self.l[1].GetAllUsedVariables()
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        varUsage.AddVariable(self.l[1], sType, obj, loc)
    # --------------------------------------------------------------------------
    def GetExprWithoutParenthesis(self): return self.l[1]
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        # Test for (a/b/c)  --> with mathmode and removeparenthesisdivision
        # the () can be removed.
        if stylesheet["mathsmode"] and \
               stylesheet["removeparenthesisdivision"] and \
               self.l[1].__class__==MultExpression:
            l2 = self.l[1].l.lGetSecondaryList()
            for i in l2:
                if i!="/":break
            else:
                # Only convert l[1], which is the expression without ()
                stylesheet.ToList(self.l[1], l)
                return

        l.append(self.l[0])
        stylesheet.ToList(self.l[1], l)
        l.append(self.l[2])
# ==============================================================================
# Stores a single section subscript
# with     section-subscript :: subscript or subscript-triplet or
#                               vector-subscript
# and      subscript-triplet :: [ subscript ] : [ subscript ] [ : stride ]
class SectionSubscript(BasicRepr):
    def __init__(self, lower, sColon1=None, upper=None,
                 sColon2=None, stride=None):
        if sColon1:
            if sColon2:
                self.t = (lower, sColon1, upper, sColon2, stride)
            else:
                self.t = (lower, sColon1, upper)
        else:
            self.t = (lower, )
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        l=[]
        for i in self.t:
            if i and not isinstance(i, str):
                l.extend(i.GetAllUsedVariables())
        return l
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        if self.t[0]: varUsage.AddVariable(self.t[0], sType, obj, loc)
        n = len(self.t)
        for i in range(1, n-1, 2):
            if self.t[i  ]: varUsage.AddVariable(self.t[i  ], sType, obj, loc)
            if self.t[i+1]: varUsage.AddVariable(self.t[i+1], sType, obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        n=len(self.t)
        if self.t[0]:
            stylesheet.ToList(self.t[0], l)
        for i in range(1,n-1,2):
            if self.t[i]:
                l.append(self.t[i])
            if self.t[i+1]:
                stylesheet.ToList(self.t[i+1], l)
# ==============================================================================
# Stores an arrays-spec, i.e.:
# [ scalar-int-expr : ] scalar-int-expr,... or
# [ scalar-int-expr ] :                ,... or
# :                                    ,... or
# [[ scalar-int-expr : ] scalar-int-expr,]..., [ scalar-int-expr : ] *
class ArraySpec(BasicRepr):
    def __init__(self):
        self.lExpr     = DoubleList()
        self.sParOpen  = "("
        self.sParClose = ")"
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen): self.sParOpen = sParOpen
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    # Adds an section subsripts: either a single expression, or
    # a subscript-triplet
    def AddSubscript(self, exp, sComma=None):
        if sComma==None and \
               len(self.lExpr.lGetSecondaryList())==len(self.lExpr)-1:
            self.lExpr.append(",", exp)
        else:
            self.lExpr.append(exp, sComma)
    # --------------------------------------------------------------------------
    def nGetNumberOfDimensions(self): return len(self.lExpr.GetMainList())
    # --------------------------------------------------------------------------
    def tGetDimension(self, n):
        o = self.lExpr[n]
        print "o=",o,o.__class__
    # --------------------------------------------------------------------------
    # Returns a list of all variables used in this array declaration
    def GetAllUsedVariables(self):
        lAll=[]
        for i in self.lExpr.GetMainList():
            lAll.extend(i.GetAllUsedVariables())
        return lAll
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.lExpr.GetMainList():
            varUsage.AddVariable(i, sType, obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(self.sParOpen)
        self.lExpr.ToList(stylesheet, l)
        l.append(self.sParClose)
# ==============================================================================
# Stores a data-ref is part-ref [ % part-ref ] ... expression
class DataRef(BasicRepr):
    def __init__(self, var, sPercent):
        self.l = DoubleList(var, sPercent)
    # --------------------------------------------------------------------------
    def append(self, pr, sPercent=None):
        self.l.append(pr, sPercent)
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        varUsage.AddVariable(self.l[0], sType, obj, loc)
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        return [self.l[0]]
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        self.l.ToList(stylesheet, l)
# ==============================================================================
# Stores a string, i.e. "abc" or 'abc'. This object can also handle a multi-
# line string, i.e. a string which doesn't end on the line it was started, e.g.:
#      s='test
#     &   rest of string'
class String(BasicRepr):
    # Constructor. Parameters:
    #
    # s -- String to store
    def __init__(self, s):
        self.l=[s]
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self): return []
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None): return
    # --------------------------------------------------------------------------
    # Add the next line of a multi-line string.
    def AddContString(self, s):
        self.l.append(s)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.extend(self.l[:])
# ==============================================================================
# Stores a complex constant,
class ComplexConst(BasicRepr):

    def __init__(self, sParOpen, oReal, sComma, oImag, sParClose):
        self.l = [sParOpen, oReal, sComma, oImag, sParClose]
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        l=self.l[1].GetAllUsedVariables()
        l.extend(self.l[3].GetAllUsedVariables())
        return l
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        varUsage.AddVariable(self.l[1], sType, obj, loc)
        varUsage.AddVariable(self.l[3], sType, obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(self.l[0])
        stylesheet.ToList(self.l[1], l)
        l.append(self.l[2])
        stylesheet.ToList(self.l[3], l)
        l.append(self.l[4])

# ==============================================================================
# Stores an array constructor:
# array-constructor     is (/ ac-spec /)
# ac-spec               is type-spec :: or [type-spec ::] ac-value-list
# ac-value              is expr or ac-implied-do
# ac-implied-do         is ( ac-value-list , ac-implied-do-control )
# ac-implied-do-control	is ac-do-variable = scalar-int-expr , scalar-int-expr
#                          [ , scalar-int-expr ]
class ArrayConstructor(BasicRepr):
    def __init__(self, sParOpen="(/"):
        self.sParOpen  = sParOpen
        self.sParClose = None
        self.l         = DoubleList()
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose="/)"): self.sParClose = sParClose
    # --------------------------------------------------------------------------
    def append(self, obj, sComma=None):self.l.append(obj, sComma)
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        for i in self.l.GetMainList():
            varUsage.AddVariable(i, sType, obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(self.sParOpen)
        stylesheet.ToList(self.l, l)
        l.append(self.sParClose)
# ==============================================================================
# Stores a single array dimension expression, i.e.:
# array-spec:   [ scalar-int-expr : ] scalar-int-expr,...   or
#               [ scalar-int-expr ] :                ,...   or
#               :                                    ,...   or
#               [[ scalar-int-expr : ] scalar-int-expr,]...,
#                                       [ scalar-int-expr : ] *
class OneArraySpec(BasicRepr):
    def __init__(self, lower=None, sColon=None, upper=None):
        self.l = [lower, sColon, upper]
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        l=[]
        if self.l[0]:
            l.extend(self.l[0].GetAllUsedVariables())
        if self.l[2]:
            l.extend(self.l[2].GetAllUsedVariables())
        return l
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        for i in self.l:
            if i: stylesheet.ToList(i, l)
# ==============================================================================
# Stores a name or a variable with an array expression, i.e.:
# DIMENSION(10:20,3,:)   or  a(10,20)
# or:
# Stores a part-ref ::  part-name [ ( section-subscript-list ) ]
# with     section-subscript :: subscript or subscript-triplet or
#                               vector-subscript
# and      subscript-triplet :: [ subscript ] : [ subscript ] [ : stride ]
# Part-name is a variable-object.
# ==============================================================================
class ArraySpecWithName(BasicRepr):
    def __init__(self, var=None, sName="", arrayspec=None, sParOpen=None):
        self.var           = var
        self.sName         = sName
        if not arrayspec:
            self.arrayspec = ArraySpec()
        else:
            self.arrayspec = arrayspec
        if sParOpen:
            self.arrayspec.SetParOpen(sParOpen)
        else:
            self.arrayspec.SetParOpen("(")
    # --------------------------------------------------------------------------
    def SetAttribute(self, att, value): self.var.SetAttribute(att, value)
    # --------------------------------------------------------------------------
    def SetParOpen(self, sParOpen):
        self.arrayspec.SetParOpen(sParOpen)
    # --------------------------------------------------------------------------
    def SetParClose(self, sParClose):
        self.arrayspec.SetParClose(sParClose)
    # --------------------------------------------------------------------------
    def AddSubscript(self, exp, sComma=None):
        self.arrayspec.AddSubscript(exp, sComma)
    # --------------------------------------------------------------------------
    def GetArraySpec(self): return self.arrayspec
    # --------------------------------------------------------------------------
    def oGetVariable(self): return self.var
    # --------------------------------------------------------------------------
    # Returns a list of all variables used in this array declaration
    def GetAllUsedVariables(self):
        return self.arrayspec.GetAllUsedVariables()
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None):
        # Add the main variable as whatever is appropriate (read or write).
        # e.g: a(i) = b(i) --> a will have sType='write', and b will have
        # sType="read"
        if self.var:
            varUsage.AddVariable(self.var,   sType,  obj, loc)
        varUsage.AddVariable(self.arrayspec, "read", obj, loc)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        if self.var:
            stylesheet.ToList(self.var, l)
        elif self.sName:
            l.append(stylesheet.sKeyword(self.sName))
        self.arrayspec.ToList(stylesheet, l)
    
# ==============================================================================
class Literal(BasicRepr):
    # Stores a literal, i.e. a number (which is stored as a string here so that
    # the number can be stored without rounding problems and in the way it was
    # specified by the user). This class is only necessary to avoid
    # distinguishing different cases in each __repr__ call, since a string like
    # "2.0" would be returned as '2.0' by ``, so "2.0*f" would be returned as
    # "'2.0'*f". (without these class we would have to test in many classes if
    # the object is a string, and if so not use `` but the plain string).
    # Parameters:
    #
    # sLiteral -- The Literal
    #
    def __init__(self, sLiteral):
        self.sLit = sLiteral
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        return []
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l): l.append(self.sLit)
    # --------------------------------------------------------------------------
    def __repr__(self):
        return self.sLit
# ==============================================================================
class LiteralKind(BasicRepr):
    # Stores a number with a kind expression, e.g. 1.0_ABC
    def __init__(self, sLiteral, sKind):
        self.l = [sLiteral, sKind]
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        return []
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="read", obj=None, loc=None): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.extend([self.l[0],'_',self.l[1]])
    # --------------------------------------------------------------------------
    def __repr__(self):
        return "%s_%s"%(self.l[0], self.l[1])
# ==============================================================================
class TrueFalse(Literal):
    # Stores a .true. or .false. statement. This is basically a Literal class,
    # except that this is a keyword (so must be handled differently when
    # using stylesheets). Parameters:
    #
    # sLiteral -- The Literal
    #
    def __init__(self, sLiteral):
        Literal.__init__(self, sLiteral)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        l.append(stylesheet.sKeyword('%s'%self))

# ==============================================================================

if __name__=="__main__":
    from AOR.Test.ExpressionTest import RunAllTests
    RunAllTests()
        
