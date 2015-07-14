#!/usr/bin/env python

from AOR.BasicStatement import BasicStatement
from AOR.ProgUnit       import ProgUnit

# ==============================================================================
class InterfaceStatement(BasicStatement):
    def __init__(self, loc=None, sInterface='INTERFACE', sAbstract=None,
                 nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.l = [sAbstract, sInterface]
    # --------------------------------------------------------------------------
    # A GenericSpec can be simply the name, or OPERATOR(operator);
    # READ(FORMATTED), ...
    def AddGenericSpec(self, *s):
        for i in s:
            self.l.append(i)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        if self.l[0]: l.append(stylesheet.sKeyword(self.l[0]), nIndentNext=1)
        l.append(stylesheet.sKeyword(self.l[1]))
        for i in self.l[2:]:
            l.append(i, nIndent=1)

# ==============================================================================
class EndInterfaceStatement(BasicStatement):
    def __init__(self, loc=None, sEnd='END', sInterface='INTERFACE', nIndent=0):
        BasicStatement.__init__(self, None, loc, nIndent)
        self.l     = [sEnd, sInterface]
        self.sName = None
    # --------------------------------------------------------------------------
    def SetName(self, sName): self.sName = sName
    # --------------------------------------------------------------------------
    # A GenericSpec can be simply the name, or OPERATOR(operator);
    # READ(FORMATTED), ...
    def AddGenericSpec(self, *s):
        for i in s:
            self.l.append(i)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        BasicStatement.ToList(self, stylesheet, l)
        l.append(stylesheet.sKeyword(self.l[0]))                 # End
        if len(self.l)>1:
            l.append(stylesheet.sKeyword(self.l[1]), nIndent=1)  # Interface
        if len(self.l)>2:
            l.appen(self.l[1], nIndent=1)                        # name
