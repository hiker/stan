#!/usr/bin/env python

# Different error classes

class Error:
    def __init__(self, sErrorMessage):
        self.sErrorMessage = sErrorMessage
    # ----------------------------------------------------
    def sGetError(self):
        return self.__str__()
    # ----------------------------------------------------
    def __str__(self):
        return self.sErrorMessage

# ========================================================
class FatalError(Error):
    pass
# ========================================================
class Warning:
    def __init__(self, sWarningMessage):
        self.sWarningMessage = sWarningMessage
    # ----------------------------------------------------
    def sGetError(self):
        return `self`
    # ----------------------------------------------------
    def __repr__(self): return self.sWarningMessage
    # ----------------------------------------------------
    def __str__(self):
        return `self`
# ========================================================

class NotYetImplemented(Warning):
    def __init__(self, sWarningMessage, scanner):
        Warning.__init__(self, sWarningMessage)
        self.nLinenumber   = scanner.GetLinenumber()
        self.nColumnnumber = scanner.GetColumnnumber()
    # ----------------------------------------------------
    def __repr__(self):
        return "Line %d, column %d: %s not yet implemented."%\
               (self.nLinenumber, self.nColumnnumber,
                Warning.__repr__(self) )

# ========================================================
