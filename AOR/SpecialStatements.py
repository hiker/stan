#!/usr/bin/env python

from UserString         import UserString

from AOR.Location       import Location
from AOR.BasicStatement import BasicStatement

# A selection of special 'statements', mostly lines that are not part
# of the actual grammar, but still stored as ojects in the program unit,
# e.g.: comment lines, compiler directives, preprocessor directives, ...

# A strange python problem(?): if any of the following classes is based upon
# str, the constructor will not work, instead an error message (str() expects
# 1 parameter, got 3) is given and the program aborts :((( So I had to base
# everything here on UserString :(((

# A simple base class for all non-statement lines like Comment, Directives, ...
class BasicNonStatement(BasicStatement, UserString):
    def __init__(self, sComment, loc):
        BasicStatement.__init__(self, None, loc)
        UserString.__init__(self, sComment)
    # --------------------------------------------------------------------------
    def isStatement(self): return 0
    # --------------------------------------------------------------------------
    def GetVarUsage(self, v): return
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        # Do not use BasicStatement.ToList, since it will indent lines to the
        # start column specified in the stylesheet.
        # First "" is for label, second for correct indentation
        l.extend(["","",self.__repr__()])
    # --------------------------------------------------------------------------
    def __repr__(self): return UserString.__str__(self)
# ==============================================================================
# Stores a comment at the end of a line
class Comment(BasicNonStatement):
    def __init__(self, sComment, loc):
        BasicNonStatement.__init__(self, sComment, loc)

# ==============================================================================
class CommentLine(BasicNonStatement):
    def __init__(self, sComment, loc=None):
        BasicNonStatement.__init__(self, sComment, loc)
       
# ==============================================================================
class PreDirective(BasicNonStatement):
    def __init__(self, sPreDirective, loc):
        BasicNonStatement.__init__(self, sPreDirective, loc)
    
# ==============================================================================
class CompilerDirective(BasicNonStatement):
    def __init__(self, sCompilerDirective, loc):
        BasicNonStatement.__init__(self, sCompilerDirective, loc)
    
# ==============================================================================
class ContMarker(BasicNonStatement):
    def __init__(self, sContMarker, loc):
        BasicNonStatement.__init__(self, sContMarker, loc)
