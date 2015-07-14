#!/usr/bin/env python

import string
from   Stylesheets.Default          import DefaultStylesheet
from   AOR.Declaration              import Common, Implicit
from   Analyser.interface.Interface import Interface
from   AOR.Interface                import InterfaceStatement, \
                                           EndInterfaceStatement

def GetAllVariables(lVars, dDone={}):
    #print "gav",lVars, dDone
    lAll=[]
    for i in lVars:
        print "i=",i,`i`,i.__class__
        if not dDone.get(string.lower(`i`), None):
            lNew = i.GetAllUsedVariables()
            #print "lNew for",i,i.__class__,"is",lNew
            dDone[string.lower(`i`)]=1
            if lNew:
                l=GetAllVariables(lNew, dDone)
                lAll.extend(l)
            lAll.append(i)
    return lAll

def GenerateInterface(sub, stylesheet=None):
    if not stylesheet:
        from Stylesheets.Default import DefaultStylesheet
        stylesheet=DefaultStylesheet

    # First create the interface objects, which stores all
    # declaration statements
    iface          = Interface()

    # Create the actual begin interface statement
    ifacestatement = InterfaceStatement('INTERFACE')
    ifacestatement.AddGenericSpec(sub.sGetName())
    iface.append(ifacestatement)
    iface.append(sub[0])
    l = []
    for i in sub.GetArguments():
        x=sub.GetVariable(i)
        print "x=",x, x.__class__
        l.append(x)

    #lDepend    = GetAllVariables(sub.GetArguments())
    lDepend    = GetAllVariables(l)
    # Now distribute the variables regarding their types:
    # a variable might be declared via an include statement,
    # as a part of a module, as a common block - or just
    # itself.
    lInclude   = []
    lModule    = []
    lCommon    = []
    lVars      = []
    for i in lDepend:
        # The order is rather important: testing for includes
        # first ensures that an include statement is used for
        # declaring this variable.
        if i['include']:
            lInclude.append(i)
        elif i['use']:
            lModule.append(i)
        elif i['common']:
            lCommon.append(i)
        else:
            lVars.append(i)
    # The correct order of declaration is:
    # use, implicit, then everything else.
    dDone = {}
    for i in lModule:
        if not dDone.get(i['module']):
            iface.append(i)
            dDone[i]=1
            
    # Now add any implicit statement found in the program unit
    for impl in sub.lGetStatements([Implicit]):
        iface.append(impl)

    # Then the include files
    dDone = {}
    for i in lInclude:
        if not dDone.get(i['include']):
            iface.append(i.oCreateDeclarationStatement(0))
            dDone[i['include']] = 1

    # Now all remaining variables
    dVarsDone = {}
    for i in lVars:
        iface.append(i.oCreateDeclarationStatement(0))
        dVarsDone[i]=1
    
    iface.append(EndInterfaceStatement(sEnd='END',sInterface='INTERFACE'))
    return iface

