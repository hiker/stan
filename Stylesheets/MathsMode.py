#!/usr/bin/env python

import string
from Tools.functions       import flatten
from Stylesheets.Default   import DefaultStylesheet
from AOR.BasicStatement    import BasicStatement
from AOR.ProgUnit          import ProgUnit
from AOR.Expression        import BasicExpression, ParenthesisExpression
from AOR.AttributeString   import AttributeString
from AOR.SpecialStatements import Comment, CommentLine, CompilerDirective,  \
                                  PreDirective, ContMarker
from Stylesheets.Layout2d  import Division2d, Layout2d, Sqrt2d, Exp2d, Abs2d

class MathsMode(DefaultStylesheet):
    
    def __init__(self):
        DefaultStylesheet.__init__(self, 'fixed')
        self['keywordcase']               = 'identical'
        self['contlinemarker']            = '>'
        self['mathsmode']                 = 1
        self['dodiv']                     = 1  # math-layout for divisions
        self['dosqrt']                    = 1  # math-layout for sqrt
        self['doexp']                     = 1  # math-layout for exp()
        self['doabs']                     = 1  # math-layout for abs()
        self['dopower']                   = 1  # math-layout for a ** b
        self['removeparenthesisdivision'] = 1
        self["maxcols"] = 72
     
    # --------------------------------------------------------------------------
    # Handles exp() calls
    def HandleExp(self, obj, l):
        lexp = Exp2d()
        self.ToList(obj.lGetArgs(), lexp)
        lexp.exp()
        l.append(lexp)
    # --------------------------------------------------------------------------
    # Handles exp() calls
    def HandlePower(self, obj, l2d):
        lSimple = obj.lGetAsSimpleList()
        lexp    = Exp2d()
        self.ToList(lSimple[0], lexp )
        n = len(lSimple)
        for i in range(1, n, 2):
            l = Layout2d()
            if lSimple[i+1].__class__==ParenthesisExpression and \
                   self['removeparenthesisdivision']:
                self.ToList(lSimple[i+1].GetExprWithoutParenthesis(), l)
            else:
                self.ToList(lSimple[i+1], l)
            lexp.power(l)

        l2d.append(lexp)
        l2d.append(" ")
        
    # --------------------------------------------------------------------------
    # Handles sqrt() calls
    def HandleSqrt(self, obj, l2d):
        lsqrt = Sqrt2d()
        l = obj.lGetArgs()
        if len(l)==1 and l[0].__class__==ParenthesisExpression and \
               self["removeparenthesisdivision"]:
            self.ToList(l[0].GetExprWithoutParenthesis(), lsqrt)
            lsqrt.sqrt()
        else:
            self.ToList(l, lsqrt)
            lsqrt.sqrt()
            
        l2d.append(lsqrt)
    # --------------------------------------------------------------------------
    # Handles abs() calls
    def HandleAbs(self, obj, l):
        labs = Abs2d()
        self.ToList(obj.lGetArgs(), labs)
        labs.abs()
        l.append(labs)
    # --------------------------------------------------------------------------
    # Handle a division - this code is currently NOT used, instead a similar
    # function is implemented in MultExpression. Reason is that some knowledge
    # about the implementation of MultExpression/ParenthesisExpression is
    # necessary here
    def HandleDivision(self, obj, l2d):
        lSimple = obj.lGetAsSimpleList()
        l2dDiv = Division2d()
        # Handle the 0-th 
        # Test for:  (a+b)/c  --> parenthesis around a+b can be removed
        if len(lSimple)>1:
            if lSimple[1]=="/" and lSimple[0].__class__==ParenthesisExpression and \
                   self["removeparenthesisdivision"]:
                self.ToList(lSimple[0].GetExprWithoutParenthesis(), l2dDiv)
            else:
                self.ToList(lSimple[0], l2dDiv )
        else:
            stylesheet.ToList(self.l[0], l2dDiv )
        n = len(lSimple)
        for i in range(1, n, 2):
            l = Layout2d()
            if lSimple[i]=="/":
                if lSimple[i+1].__class__==ParenthesisExpression and \
                       self['removeparenthesisdivision']:
                    self.ToList(lSimple[i+1].GetExprWithoutParenthesis(), l)
                else:
                    self.ToList(lSimple[i+1], l)
                l2dDiv.over(l)
            else:
                l.append(" ")
                self.ToList(lSimple[i  ], l)
                l.append(" ")
                self.ToList(lSimple[i+1], l)
                l2dDiv.append(l)
        l2d.append(l2dDiv, nIndent=1)
        l2d.append(" ")
    # --------------------------------------------------------------------------
    def SplitIntoLines(self, l2d, bIgnoreAttributes=None):
        #print "Splitting",l2d,len(l2d),self["maxcols"]
        if isinstance(l2d, Layout2d) and len(l2d)>=self["maxcols"]:
            l2d.sSplitIntoLines(self["maxcols"])
        else:
            DefaultStylesheet.SplitIntoLines(self, l2d, bIgnoreAttributes)
        
    # --------------------------------------------------------------------------
    def ToList(self, obj, l, bIgnoreAttributes=None):
        DefaultStylesheet.ToList(self, obj, l,
                                 bIgnoreAttributes=bIgnoreAttributes)
        #if isinstance(obj, BasicStatement):
        #    self.SplitIntoLines(l)
        return
# ==============================================================================

if __name__=="__main__":
    import sys
    from Tools.Project import Project

    project = Project()
    ssheet  = MathsMode()
    for i in sys.argv[1:]:
        o = project.oGetObjectForIdentifier(i, "file")
        print ssheet.ToString(o)
    
