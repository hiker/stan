#!/usr/bin/env python

import string
from   Variable        import Variable, VariableData
from   AOR.Declaration import Type

class Variables:
    # Constructor for a set of variables
    def __init__(self):
        self.dVarsData = {}
        self.dImplicit = {}
    # --------------------------------------------------------------------------
    # Adds a variable. Paramater:
    #
    # sName -- Name of the Variable (a string or a AttributeString)
    #
    # dType -- A dictionary containing information about the type.
    def AddVariable(self, sName, dType):
        # If no type is defined, get the implicit default type
        # but set a flag that this variable was undefined
        if not dType.get('type',None):
            dType['type'     ] = self.GetImplicitType(sName)
        varData = VariableData(sName.lower(), dType)
        var     = Variable(sName, varData)
        self.dVarsData[sName.lower()] = varData
        return var
    # --------------------------------------------------------------------------
    # Get a pointer to the variable 'sName'. If the variable doesn't exist
    # the variable is added and the new pointer is returned. This is used
    # for undefined variables in a subroutine.
    def GetVariable(self, sName, d=None, bAutoAdd=1):
        if not d: d={}
        
        try:
            var=Variable(sName, self.dVarsData[sName.lower()])
            for k,v in d.items():
                var.SetAttribute(k,v)
                # If the variable was undefined up to now, remove the
                # undefined attribute. This happens e.g. for arguments,
                # which are added as undefined when parsing the subroutine
                # statement, and are declared later
                if k=="type":
                    if var['undefined']: del var['undefined']
            return var
        except KeyError:
            if bAutoAdd:
                if not d.get('type',None): d['undefined'] = 1
                return self.AddVariable(sName, d)
            else:
                return None
    # --------------------------------------------------------------------------
    def GetAttributes(self, sName):
        return self.dVarsData.get(string.lower(sName), {})
    # --------------------------------------------------------------------------
    def lGetAllVariables(self):
        return self.dVarsData.values()
    # --------------------------------------------------------------------------
    def SetImplicit(self, type, sFrom, sTo=None):
        if not sTo: sTo=sFrom
        # If this is the first implicit statement, a dictionary for the type
        # mapping is created:
        if not self.dImplicit:
            self.dImplit={}
            for i in 'ABCDEFGHOPQRSTUVWXYZ':
                self.dImplicit[i] = Type('REAL')
            for i in 'IJKLMN':
                self.dImplicit[i] = Type('INTEGER')
        # Now add the 
        sFrom = string.upper(sFrom[0])
        sTo   = string.upper(sTo[0]  )
        for i in range(ord(sFrom), ord(sTo)+1):
            self.dImplicit[chr(i)] = type
        # We now have to check if any variables have a wrong implicit
        # type set (e.g. arguments of a subroutine will have the default
        # implicit type set, since when the subroutine statement is parsed
        # no implicit statement is valid).
        for k,v in self.dVarsData.items():
            if v['undefined']:
                v['type']=self.GetImplicitType(`v`)
    # --------------------------------------------------------------------------
    def GetImplicitType(self, s):
        c = string.upper(s[0])
        if self.dImplicit:
            t = self.dImplicit.get(c, None)
            return t
        
        if c>="I" and c <="N":
            return Type('INTEGER')
        return Type('REAL')
    # --------------------------------------------------------------------------
    # Returns a unique symbol prefix, i.e. it is guaranteed that new symbols
    # created with this prefix plus some suffix will not be used anywhere.
    def sGetUniquePrefix(self):
        # First: try 'stan_' as prefix:
        # -----------------------------
        sVar="stan_"
        for j in self.lGetAllVariables():
            if `j`[0:len(sVar)]==sVar:
                break
        else:
            return sVar
        
        # Second: try all one letter prefixes:
        # ------------------------------------
        for i in string.ascii_lowercase:
            sVar="%s_"%i
            for j in self.lGetAllVariables():
                if `j`[0:2]==sVar:
                    break
            else:
                return sVar

        # Last: try all 2 letter prefixes, i.e. first letter
        # a charater, second 2 character or number. If this
        # still shouldn't help, add more 'a's to the beginning
        # till something is found
        s2nd="0123456789"+string.ascii_lowercase
        sBase=""
        while 1:
            for a in string.ascii_lowercase:
                for i in s2nd:
                    sVar = "%s%s%s_"%(sBase,a,i)
                    for j in self.lGetAllVariables():
                        if `j`[0:len(sVar)]==sVar:
                            break
                    else:
                        return sVar
            # Gee - all 26*36 characters are used - quite unlikely :)
            # Well, start adding 'a's to the beginning of the prefix.
            # Sooner or later there must be a unique prefix :)
            sBase="a"+sBase
                    
        
        
    # --------------------------------------------------------------------------
    def __repr__(self):
        s=""
        for i in self.dVarsData.keys():
            s="%s\n%s: %s %s"%(s, i, self.dVarsData[i],
                               self.dVarsData[i].GetAttributes())
        return s
    
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.VariablesTest import RunTest
    RunTest()
