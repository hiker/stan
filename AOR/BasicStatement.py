#!/usr/bin/env python

# Stores a label, i.e. a 1-5 digit number.

from Stylesheets.Default import DefaultStylesheet
from AOR.Location        import Location

class Label:
    # Constructor for Label. Parameter:
    # sLabel -- The label
    #
    def __init__(self, sLabel): Label.SetLabel(self, sLabel)
    # --------------------------------------------------------------------------
    def SetLabel(self, sLabel):
        self.sLabel = sLabel
    # --------------------------------------------------------------------------
    def LabelIs(self, iLabel):
        if self.sLabel:
            return int(self.sLabel)==iLabel
        return None
    # --------------------------------------------------------------------------
    # See stylesheet f77: If there is a label, there can't be a continuation
    # marker in the same line. In this case, the label must occupy the first
    # (usually) 5 columns, plus one space for a (non existant) cont marker.
    def ToList(self, stylesheet, l):
        if self.sLabel:
            if stylesheet['labelalignright']:
                sFormat = "%%%ds "%(stylesheet['startcolumn']-2)
            else:
                sFormat = "%%-%ds "%(stylesheet['startcolumn']-2)
            if self.sLabel.__class__==str:
                l.append(sFormat%self.sLabel)
            else:
                l.append(self.sLabel.sCreateCopy(sFormat%self.sLabel))
        else:
            # We have to add a ' ' here, since the f77 split lines function
            # depends on having the spaces at the beginning.
            # nIndent specifies additional spaces to indent, so the actual
            # indentation is startcolumn-2 + 1 (for the space), so the next
            # character starts at column startcolumn.
            l.append(" ", nIndent=stylesheet['startcolumn']-2)
    # --------------------------------------------------------------------------
    def __repr__(self):
        if self.sLabel:
            return "%s"%self.sLabel
        else:
            return ""
    
    
# ==============================================================================
# This class basically wraps the interface for __repr__ to ToList
class BasicRepr:
    def __repr__(self):
        ssheet = DefaultStylesheet()
        return self.ToString(ssheet)
    # --------------------------------------------------------------------------
    def ToString(self, stylesheet): return stylesheet.ToString(self)
    # --------------------------------------------------------------------------
    def __str__(self): return self.__repr__()
# ==============================================================================
# Base class for all (declaration and executable) statements. One important
# resitrction: the first element of the list returned by ToList must be
# a label (if it exists) plus the correct number of spaces to assure that the
# program starts at the correct column. The second element must be the
# (potentially empty) string of spaces for the indentation.
class BasicStatement(Label, Location):

    def __init__(self, sLabel=None, loc=None, nIndent=0, isDeclaration=1):
        Label.__init__(self, sLabel)
        Location.__init__(self, loc)
        self._isDeclaration=isDeclaration
        self.nIndent=nIndent
    # --------------------------------------------------------------------------
    def isA(self, c):
        return self.__class__ == c
    # --------------------------------------------------------------------------
    # Returns true if the statement is a 'real' fortran statement (as opposed to
    # a compiler directive, comment line, preprocessor directive). This method
    # is overwritten in those classes.
    def isStatement(self): return 1
    # --------------------------------------------------------------------------
    # Returns if this statement is a declaration statement or not
    def isDeclaration(self): return self._isDeclaration
    # --------------------------------------------------------------------------
    def ToString(self, stylesheet): return stylesheet.ToString(self)
    # --------------------------------------------------------------------------
    def GetIndentation(self): return self.nIndent
    # --------------------------------------------------------------------------
    def GetVarUsage(self, varUsage, sType="", obj=None, loc=None): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        Label.ToList(self, stylesheet, l)
        l.append(stylesheet.GetIndentation(self))
    # --------------------------------------------------------------------------
    def __str__(self): return self.__repr__()
    # --------------------------------------------------------------------------
    def __repr__(self):
        stylesheet = DefaultStylesheet()
        return "%s%s"%(Label.__repr__(self),
                       "".join(stylesheet.ToString(self)))
# ==============================================================================
# Base class for all named executable statements (if, do, ...)
class BasicNamedStatement(BasicStatement):

    def __init__(self, sLabel=None, sName=None, loc=None, nIndent=0,
                 isDeclaration=1):
        self.sName=sName
        BasicStatement.__init__(self, sLabel, loc, nIndent,
                                isDeclaration=isDeclaration)
    # --------------------------------------------------------------------------
    def SetName(self, s): self.sName=s
    # --------------------------------------------------------------------------
    def NameIs(self, s):
        return self.sName and string.upper(self.sName) == string.upper(s)
    # --------------------------------------------------------------------------
    def GetName(self): return self.sName
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l, bAddSpace=0):
        BasicStatement.ToList(self, stylesheet, l)
        if self.sName:
            if bAddSpace:
                l.append(self.sName,nIndentNext=1)
            else:
                l.append(self.sName)

# ==============================================================================

if __name__=="__main__":
    from AOR.Test.BasicStatementTest import RunTest
    RunTest()
