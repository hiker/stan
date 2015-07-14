#!/usr/bin/env python

# This class is used to output warning and error messages
class Output:
    def __init__(self):
        pass
    # ----------------------------------------------------------
    def Warning(self, s):
        print "Warning:",s
    # ----------------------------------------------------------
    def Error(self, s):
        print "Error:  ",s
    # ----------------------------------------------------------
    def ImplementationError(self, s):
        print "Implementation Error:  ",s
