#!/usr/bin/env python

import string
from   UserDict              import UserDict
from   types                 import TupleType, StringType, ListType
from   AOR.Expression        import ArraySpec, ArraySpecWithName
from   AOR.Declaration       import Intent, Use, Declaration, VariableWithInit
from   AOR.SpecialStatements import PreDirective

# Handling of variables: the basic idea is to have only one instance of each
# variable, and instead store only pointers to this instance whenever the
# variable is used. This allows a very easy rename of a variable in a
# subroutine by just changing the data in this one instance.
# But since it is necessary to store each string (because the string might
# have attributes like comments, ..., attached to it), this approach doesn't
# work as described anymore. The following design is used instead:
#
# Whenever a variable is used and stored in an object, a call to the
# containing ProgUnit is made requesting the variable (which will be added
# to the list of variables used in the ProgUnit, see ProgUnit and the base
# class Variables). ProgUnit in turn will create an instance of Variable.
# This instance stores the original string (with attibutes), and a pointer
# to a VariableData instance (of which only one exists for each variable,
# while an arbitrary number of Variable instances can exist). VariableData
# stores the 'current' (i.e. potentially renamed) name of a variable.
# Whenever a Variable instance is 'printed', it has to check whether the
# VariableData instance has a changed name, and if so, the string representing
# the original variable has to be replaced with an up-to-date version. It
# seems to be easier doing it this way than keeping track of all instances
# of Variable which uses a certain instance of VariableData (and then changing
# all those Variable instances when a variable is changed). If this should
# become a performance bottleneck, it can be changed.

# Todo: Using UserDict seems to be a problem with python 2.2, since '
#       __getitem__ uses get, which in turn uses self[], which is
#       __getitem__ --> loop :((( As a workaround, I am using the
#       data attribute of UserDict directly. The implementation of
#       UserDict was changed with 2.2 :(((
#       I tried using dict instead of UserDict, but then python's
#       pickle module had a problem and couldn't properly unpickle
#       classe with a dict as a baseclass.

# ==============================================================================
class VariableData(UserDict):

    # Stores information about a variable. This object is a dictionary itself,
    # so the attributes of a variable can be accessed via [] etc. Only one
    # instance of this object is created, each Variable instance contains a
    # pointer to this object which is used to store and retrieve information/
    # Parameter:
    #
    # sName -- Name of the variable
    #
    # dType -- Type information of the variable
    #          'argument'   : 1 if the variable is an argument
    #          'dimension'  : for arrays only: contains ArraySpec
    #          'type'       : type of the variable (class Type)
    #          'undefined'  : 1 if not defined (type will then be implicit)
    #          'allocatable': 1 if allocatable
    #          'pointer'    : 1 if pointer
    #          'target'     : 1 if target
    #          'parameter'  : 1 if parameter
    #          'optional'   : 1 if optional
    #          'save'       : 1 if save
    #          'intent'     : a Intent instance
    #          'kind'       : kind information
    #          'module'     : module-name: for variables from a module
    #          'renamedfrom': orig name. Variable renamed from a module
    #          'common'     : variable belongs to a common block, value is
    #                         the common block statement
    #          'include'    : true if this variable was declared in an
    #                         included file, object is the include file name
    #          'equivalence': variable is used in an equivalence statement
    #                         value is a list of equivalence items in which
    #                         the variable is used.
    #          'init'       : An initial value, e.g. integer, parameter:n=3
    
    def __init__(self, sName, dType=None):
        if not dType: dType={}
        UserDict.__init__(self, dType)
        self.sName = sName
    # --------------------------------------------------------------------------
    # Overwrite the default, so that no excpetion is raised for
    # non existing attributes
    def __getitem__(self, key):
        return self.data.get(key, None)
    # --------------------------------------------------------------------------
    # Returns the current name of the variable (the current name is either the
    # original one or a renamed one.
    def sGetName(self): return self.sName
    # --------------------------------------------------------------------------
    def SetName(self, s) : self.sName=s
    # --------------------------------------------------------------------------
    def bIsArray(self):
        return self['dimension'] or self['type'].bIsType("CHARACTER")
    # --------------------------------------------------------------------------
    # This creates a declaration statment which declares the current variable.
    # The result is a real AOR object, not just a list
    def oCreateDeclarationStatement(self, nIndent, bUseInclude=1, bUseModule=1,
                                    sNewName="", bAddInit=0):
        if self['include'] and bUseInclude:
            return PreDirective('#include "%s"'%self['include'],(0,0))
        if self['module'] and bUseModule:
            use = Use('USE', nIndent=nIndent)
            use.SetName(self['module'])
            use.AddComma(',')
            if self['renamedfrom']:
                if sNewName:
                    use.AddRename(self['renamedfrom'],'=>', sNewName)
                else:
                    use.AddRename(self['renamedfrom'],'=>', self.sName)
            else:
                use.AddOnlyString('ONLY',':')
                use.AddOnly(self)
            return use
        l=[]
        # First handle all attributes which are basically strings:
        for i in ['allocatable','pointer','target','parameter','optional',
                  'save','kind']:
            if self[i]:
                l.extend([i,','])
        # Now handle dimension statements (the value of the dimension
        # attribute is actually an ArraySpec, so we have to create a
        # new ArraySpecWithName object here).
        if self['dimension']:
            l.extend([ArraySpecWithName(sName='dimension',
                                        arrayspec=self['dimension']), ','])
        # The value of 'intent' is actually an object, which can be used
        # directly here.
        if self['intent']:
            l.extend([self['intent'], ', '])
        # Remove the last comma and create the Declaration object:
        if l and l[-1]==',':
            del l[-1]
            decl = Declaration(self['type'], sComma=',', nIndent=nIndent)
        else:
            decl = Declaration(self['type'], nIndent=nIndent)

        # Now add all attributes and the commas
        for i in range(0, len(l)-1, 2):
            decl.AddAttribute(l[i],l[i+1])
        if l: decl.AddAttribute(l[-1])
        decl.AddDoubleColons(':',':')
        if bAddInit and self["init"]:
            decl.AppendVariable(VariableWithInit(self,"=",self["init"]))
        else:
            if sNewName:
                decl.AppendVariable(Variable(sNewName, self))
            else:
                decl.AppendVariable(Variable(self.sName, self))

        return decl
        
    # --------------------------------------------------------------------------
    # This is basically a ToList method for creating proper declaration of a
    # variable, e.g. for interfaces, .... The returned list will have the usual
    # 'special' first two elements: the first one a label plus potential
    # indentation (to start the correct start column), the second one
    # correct indentation for the logical nesting (which is in this case a '').
    def lGetDeclaration(self, stylesheet):
        # First, test if the variable was declared in a module. If so,
        # create the proper use statement:
        if self['module']:
            if self['renamedfrom']:
                return [stylesheet.sGetStartColumnSpaces(), '',
                        stylesheet.sKeyword('USE'),' ',
                        self['module'],', ',self['renamedfrom'],'=>',
                        self.sName]
            else:
                return [stylesheet.sGetStartColumnSpaces(),'',
                        stylesheet.sKeyword('USE'),' ',self['module'],
                        ', ',stylesheet.sKeyword('ONLY'),':', self.sName]
        # Each variable has a type, since the default type will be set!
        l=[stylesheet.sGetStartColumnSpaces(),'',"%s"%self['type'], ', ' ]
        for i in ['allocatable','pointer','target','parameter','optional',
                  'save']:
            if self[i]: l.extend([i, ', '])
        if self['kind']: l.extend([self['kind'], ', '])
        if self['dimension']:
            l.extend(["DIMENSION%s"%self.GetDimensionAsString(), ', '])
        if self['intent']: l.extend(["INTENT(%s)"%self['intent'], ', '])
        # The last element of the list is a ', ', so this must be removed!
        l[-1]=' :: '
        l.append(self.sName)
        return l
    # --------------------------------------------------------------------------
    def GetDeclarationAsString(self, stylesheet):
        return "".join(self.lGetDeclaration(stylesheet))
    # --------------------------------------------------------------------------
    # Returns a list of all variables used when declaring this variable.
    # The variable itself is added to the list of variables in the Variable
    # objects. This is necessary::
    # consider the example expressions 'a' and 'a+b'. GetAllUsedVaraibles for
    # the latter one has to return 'a' and 'b' as part of the sum expression,
    # so the first expression has to return 'a'. But since this expression is
    # only a variable, each variable has to return itself as a used variable.
    def GetAllUsedVariables(self):
        l = []
        if self['include'  ]:
            return l
        if self['dimension']: l.extend(self['dimension'].GetAllUsedVariables())
        if self['common'   ]: l.append(self['common'   ])
        if self['init'     ]: l.extend(self['init'].GetAllUsedVariables())
        return l
    # --------------------------------------------------------------------------
    # Sets an attributes for the variable. The attribute can be either
    # a string (in which case the value is set to 1), or an object
    # (e.g. dimension, type).
    def SetAttribute(self, att, value=1):
        if att=='equivalence':
            if self[att]:
                self[att].append(value)
            else:
                self[att]=[value]
        else:
            self[att]=value
    # --------------------------------------------------------------------------
    # Returns a dictionary with all attributes of a variable.
    def GetAttributes(self): return self
    # --------------------------------------------------------------------------
    # Returns a string with the correct declaration of the variable, e.g.
    # '(1:2, 3:, nlat_dyn+3, nlon_dyn,*)'
    def GetDimensionAsString(self):
        dim=self.get('dimension',None)
        if not dim: return ""
        return `dim`
        
    # --------------------------------------------------------------------------
    # Displays the variable name and all attributes
    def DisplayAll(self):
        return '%s[%s]'%(self.sName, UserDict.__repr__(self))
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l): l.append(stylesheet.sVariable(self.sName))
    # --------------------------------------------------------------------------
    # Returns just the variable name.
    def __repr__(self):
        return self.sName.__str__()
# ==============================================================================
# This stores the actual string of a variable as it is used in a program. This
# is necessary since the string might be an AttributeString containing
# directives, .... All actual information about a variable (like type,
# dimension, intend...) is stored in an instance of VariableData (to which this
# object stores a pointer), of which only one instance per variable exists.
class Variable:
    def __init__(self, sName, oVariableData=None):
        self.sName    = sName                     # Potential an AttributeString
        if oVariableData:
            self.oVarData = oVariableData
        else:
            self.oVarData = VariableData(self.sName,{})
    # --------------------------------------------------------------------------
    # Forward this to the actual VariableData instance
    def __getitem__(self, key): return self.oVarData[key]
    # --------------------------------------------------------------------------
    # Forward this to the actual VariableData instance
    def __setitem__(self, key, value):
        return self.oVarData.__setitem__(key, value)
    # --------------------------------------------------------------------------
    # Forward this to the actual VariableData instance
    def __delitem__(self, key):
        return self.oVarData.__delitem__(key)
    # --------------------------------------------------------------------------
    # This is necessary, since for example in a common block an expression
    # like common /xx/ a, b(10) can be used. Now, to store the information
    # that a common block is used, we need acces to the variable b (which is
    # an ArrayRef). To avoid further tests, the same method is implemented
    # for variables as well.
    def oGetVariable(self): return self
    # --------------------------------------------------------------------------
    # Forward this to the actual VariableData instance
    def GetDeclarationAsString(self, stylesheet):
        return self.oVarData.GetDeclarationAsString(stylesheet)
    # --------------------------------------------------------------------------
    def GetAllUsedVariables(self):
        l = self.oVarData.GetAllUsedVariables()
        l.append(self)
        return l
    # --------------------------------------------------------------------------
    # Sets an attributes for the variable. The attribute can be either
    # a string (in which case the value is set to 1), or an object
    # (e.g. dimension, type). This is forwarded to the respective VariableData
    # instance.
    def SetAttribute(self, att, value=1):
        return self.oVarData.SetAttribute(att, value)
    # --------------------------------------------------------------------------
    # Returns a dictionary with all attributes of a variable.
    def GetAttributes(self): return self.oVarData.GetAttributes()
    # --------------------------------------------------------------------------
    def sGetName(self): return self.oVarData.sGetName()
    # --------------------------------------------------------------------------
    def SetName(self, s) : self.oVarData.SetName(s)
    # --------------------------------------------------------------------------
    # Returns a string with the correct declaration of the variable, e.g.
    # '(1:2, 3:, nlat_dyn+3, nlon_dyn,*)'. This is forwarded to the respective
    # VariableData instance.
    def GetDimensionAsString(self): return self.oVarData.GetDimensionAsString()
    # --------------------------------------------------------------------------
    def oCreateDeclarationStatement(self, nIndent=0, bUseInclude=1, bUseModule=1,
                                    sNewName="", bAddInit=0):
        return self.oVarData.oCreateDeclarationStatement(nIndent,
                                                         bUseInclude=bUseInclude,
                                                         bUseModule=bUseModule,
                                                         sNewName=sNewName,
                                                         bAddInit=bAddInit)
    # --------------------------------------------------------------------------
    def bTypeIs(self, sType):
        return self["type"].bIsType(sType)
    # --------------------------------------------------------------------------
    def bIsArray(self): return self.oVarData.bIsArray()
    # --------------------------------------------------------------------------
    # Displays the variable name and all attributes. This is forwarded to the
    # respective VariableData instance.
    def DisplayAll(self): return self.oVarData.DisplayAll()
    # --------------------------------------------------------------------------
    # Needed for layout2d
    def __len__(self): return len(self.sName)
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l):
        sCurrentName = self.oVarData.sGetName()
        if string.lower(sCurrentName)==string.lower(self.sName):
            l.append(stylesheet.sVariable(self.sName))
            return
        # The variable has been renamed. If the current name is a normal string,
        # simply replace it with the new name:
        if type(self.sName)==type(''):
            self.sName=sCurrentName
            l.append(sCurrentName)
            return
        # Otherwise sName is an AttributeString. Create a new instance of
        # AttributeString
        self.sName = self.sName.sCreateCopy(sCurrentName)
        l.append(stylesheet.sVariable(self.sName))
    # --------------------------------------------------------------------------
    def __repr__(self): return self.sName
    # --------------------------------------------------------------------------


# ==============================================================================

if __name__=="__main__":
    from AOR.Test.VariableTest import RunTest
    RunTest()
