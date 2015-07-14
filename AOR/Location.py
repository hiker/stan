#!/usr/bin/env python

# ==============================================================================
# Stores a locations (i.e. line number and column number).
# This base object is only used for certain statements, not for all tokens!
# Separate file to avoid recursive dependencies.

class Location:
    def __init__(self, loc): self.loc=loc
    # --------------------------------------------------------------------------
    def SetEndLocation(self, loc): self.endloc = loc
    # --------------------------------------------------------------------------
    def GetLocation(self):    return self.loc
    # --------------------------------------------------------------------------
    def GetEndLocation(self): return self.endloc
    
