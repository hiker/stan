#!/usr/bin/env python
import string
from AOR.Statements import Call
from AOR.BasicStatement import BasicStatement
from AOR.Do import Do,EndDo
from AOR.If import If,ElseIf,Else,EndIf,IfOnly


def GenerateFileCallTree(objFile,sFilename):
    bDoLoops = 1
    bIf = 1
    nLevel = 3
    lIgnore = ['']
   
    mystring  = "File:" + sFilename + "\n"
    for sub in objFile.GetAllSubroutines():
	sRoutineName =  sub.GetName()
	mystring = mystring + "Call tree for subroutine:" + sRoutineName + "\n"
	mycalltree = CallTree(sub,nLevel,lIgnore, bDoLoops,bIf)
	mystring = mystring + CallTree.__repr__(mycalltree) + "\n"
    return mystring
        
class CallTree:
    def __init__(self, oSubroutine, nLevel=11, lIgnore=[], bDo=None,bIf=None):
	self.oSubroutine  = oSubroutine
        self.nLevel = nLevel
        self.lIgnore = lIgnore
        self.bDo = bDo
        self.bIf = bIf
        self.lstatements = []
        self.lAllBlocks = []
        self.lfind = [Call]
	self.nCallnest = 0

	# store routines to ignore in a dict.
        self.dIgnore = {}
        for i in self.lIgnore:
	    self.dIgnore[i]=1

	# Are we interested in Do Loops surrounding calls
        if self.bDo:
	    self.lfind.append(Do)
	    self.lfind.append(EndDo)

	# Are we interested in If/Else/Endif surrounding calls
        if self.bIf:
          self.lfind.append(If)
          self.lfind.append(Else)
          self.lfind.append(ElseIf)
          self.lfind.append(EndIf)
          self.lfind.append(IfOnly)
        lAll = self.oSubroutine.lGetStatements(self.lfind)

	# Check for Routines to Ignore
        for statement in lAll:
	    if isinstance(statement,Call):
		if not self.dIgnore.has_key(statement.GetName()):
		    self.lstatements.append(statement)
            # IfOnly statements may have calls, check those too
            elif isinstance(statement,IfOnly):
		checkIf = statement.GetStatement()
		if isinstance(checkIf,Call):
		    if not self.dIgnore.has_key(checkIf.GetName()):
			self.lstatements.append(statement)
	    else:
		self.lstatements.append(statement)

	# Get All Blocks at the outer most level for a subroutine
        self.lAllBlocks = self.lGetAllBlocks()
        return

    def __repr__(self):
	mystring = ""
	for l in self.lAllBlocks:
	    if self.bHasCall(l):
		for i in l:
		    mystring = mystring + BasicStatement.__repr__(i) + "\n"
        return mystring

    def bHasCall(self,lBlock):
	bCall = 0
	for i in lBlock:
	    if isinstance(i,Call):
		bCall = 1
        return bCall

    def lGetAllBlocks(self):
	lBlocks = []
	lnextBlock = []
	nest = 0
	for i in self.lstatements:
	    if isinstance(i,IfOnly):
		if isinstance(i.GetStatement(),Call):
		    lnextBlock.append(i)
	    elif isinstance(i,If):
		nest = nest + 1
		lnextBlock.append(i)
	    elif isinstance(i,EndIf):
		lnextBlock.append(i)
		if nest==1:
		    lBlocks.append(lnextBlock)
		    lnextBlock = []
		    nest = 0
		else:
		    nest = nest - 1
	    elif isinstance(i,Call):
		lnextBlock.append(i)
		if nest==0:
		    lBlocks.append(lnextBlock)
		    lnextBlock = []
	    elif isinstance(i,Do):
		lnextBlock.append(i)
		nest = nest + 1
            elif isinstance(i,EndDo):
		lnextBlock.append(i)
		if nest==1:
		    lBlocks.append(lnextBlock)
		    lnextBlock = []
		    nest = 0
		else:
		    nest = nest - 1
        return lBlocks
