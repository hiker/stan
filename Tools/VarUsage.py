#!/usr/bin/env python

from AOR.Variable   import Variable
from AOR.Expression import Literal, ArraySpecWithName

class VarUsage:
    # If bUseUnknown is set to 0, all 'unknown' variables will be appended
    # to read and write instead of to 'unknown'. Depending on the application
    # that is more useful (e.g. call sub(a) --> a will be read/write instead
    # of unknown).
    def __init__(self, bUseUnknown=1):
        self.dRead       = {}
        self.dWrite      = {}
        self.dUnknown    = {}
        self.bUseUnknown = bUseUnknown;
        self.dType2Dict  = {"read"      : self.dRead,
                            "write"     : self.dWrite,
                            "unknown"   : self.dUnknown  }
        # Variables can be set to be ignored, for example:
        # loop variables might be ignored, so that they are
        # not reported as being read/written
        self.dIgnore     = {}
    # --------------------------------------------------------------------------
    def __str__(self): return self.__repr__()
    # --------------------------------------------------------------------------
    def __repr__(self):
        s=""
        for i in ("read", "write","unknown"):
            d = self.dType2Dict[i]
            if d:
                s="%s%s: %s\n"%(s, i, `d`)
        return s
    # --------------------------------------------------------------------------
    def addVariableToIgnore(self, s):
        if s.__class__ == Variable:
            self.dIgnore[`s`.lower()]=1
        else:  # assume string:
            self.dIgnore[s.lower()]=1
    # --------------------------------------------------------------------------
    def stopIgnoringVariable(self,s):
        if s.__class__ == Variable:
            del self.dIgnore[`s`.lower()]
        else:
            del self.dIgnore[s.lower()]
            
    # --------------------------------------------------------------------------
    # Create a one line output for unit tests
    def GetTestOutput(self):
        s=""
        for i in ("read", "write", "unknown"):
            l = self.dType2Dict[i].keys()
            l.sort()
            if l:
                s1 = reduce(lambda s,x: s+","+`x`[1:-1], l)
                s="%s%s: %s; "%(s, i, s1)
        return s[:-2]

    # --------------------------------------------------------------------------
    def __getitem__(self, sType): return self.GetVarUsage(sType)
    # --------------------------------------------------------------------------
    def GetVarUsage(self, sType, sVar=None):
        s = sType.lower()
        if sVar==None:
            return self.dType2Dict[s]
        return self.dType2Dict[s][sVar]
    # --------------------------------------------------------------------------
    def AddVariable(self, v, sType="read", obj=None, loc=None):
        # If no unknown state is to be saved, save all 'unknown' as read and as
        # write.
        if sType=="unknown" and not self.bUseUnknown:
            self.AddVariable(v, "read",  obj=obj, loc=loc)
            self.AddVariable(v, "write", obj=obj, loc=loc)
            return

        if v.__class__ == str: return  # e.g. a(:) --> the ":" appears as string
        if v.__class__ != Variable:
            v.GetVarUsage(self, sType, obj, loc)
            return

        # We have to use the name of the variable, since the same variable
        # (name) might have different variable objects representing it
        sVar=`v`.lower()
        
        # Check if the variable should be ignored
        if self.dIgnore.get(sVar,None): return
        
        if obj: loc = obj.GetLocation()
        l = self.dType2Dict[sType].get(sVar)
        if l:
            l.append(loc)
        else:
            self.dType2Dict[sType][sVar]=[loc]
        return

    # --------------------------------------------------------------------------

