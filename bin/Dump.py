#!/usr/bin/env python

#./Dump.py -l 149-172 sound.F >xx

import sys
import getopt
import string
import copy
from   os.path         import basename, splitext
from   Tools.Project   import Project
from   Tools.VarUsage  import VarUsage
from   Grammar.Parser  import Parser
from   Stylesheets.f77 import f77
from   Stylesheets.Default import DefaultStylesheet
from   AOR.Declaration import Declaration, VariableWithInit, Include
from   AOR.Expression  import Expression, Literal, ArraySpecWithName, TrueFalse
from   AOR.Variable    import VariableData, Variable
from   AOR.Statements  import Allocate, Call, Assignment, Stop, FunctionCall, \
                              Return
from   AOR.Do          import ControlLessDo, Exit, EndDo,Do
from   AOR.If          import IfOnly, If, EndIf
from   AOR.IO          import Write, Read, Open, Print, Close
from   AOR.Subroutine  import SubroutineStatement, Subroutine
from   AOR.Program     import ProgramStatement, Program
from   AOR.ProgUnit    import EndProgUnit

# ==============================================================================
class Dump:
    # The object representing the file, where to start dumping, line number
    # where dumping should start and end, and then either a sorted list of
    # numbers representing when to dump, or a Fortran expression returning
    # 0, 1, or 2: 0 represents: do not dump, 1: dump, 2: dump and stop dumping
    def __init__(self, objFile, lLineFrom, lLineTo, lWhenDump=[],
                 sCond="", bDoMPI = 0):
        if not sCond and not lWhenDump:
            print "Error: one condition must be specified"
            return
        if sCond and lWhenDump:
            print "Error: don't specify both conditions"
            return
        self.objFile     = objFile
        self.nLineFrom   = nLineFrom
        self.nLineTo     = nLineTo
        self.lWhenDump   = lWhenDump
        self.bDoMPI      = bDoMPI
        self.nUnit       = 1234
        try:
            filename,ext = splitext(basename(objFile.sGetFilename()))
        except:
            # in case that something went wrong
            filename = objFile.sGetFilename()
            ext      = ""
        self.sDumpFile   = "%s.dump"%filename
        self.sDumpWriteName = "%s.write%s"%(filename, ext)
        self.sDumpReadName  = "%s.driver%s" %(filename, ext)
        self.sDumpPrefix = "DUMP"
        if objFile.sGetFormat()=="fixed":
            self.stylesheet  = f77()
        else:
            self.stylesheet  = DefaultStylesheet()
            self.stylesheet  = f77()
        self.GenerateWriter()
        self.GenerateDriver()
    # --------------------------------------------------------------------------
    # Creates a variables with a prefix so that it is guaranteed that the
    # variable does not exist
    def sVar(self, var):
        if type(var)==type(""):
            s = self.sPre+var
        else:
            s = self.sPre+var.sGetName()
        return s[:31]
    # --------------------------------------------------------------------------
    # Returns a modified version of the variable, to which "correct_" is
    # prepended, and which is unique as well
    def sCorrectVar(self, var):
        if type(var)==type(""):
            s = "%scorrect_%s"%(self.sPre, var)
        else:
            s = "%scorrect_%s"%(self.sPre,var.sGetName())
        # Maximum length of fortran variables is 31, so restrict new variables
        # to this length. This is obviously a work around, since the shortened
        # variable name might clash :((
        return s[:31]
    
    # --------------------------------------------------------------------------
    def GetScalarAndArrayVariables(self, unit, lVars):
        dDone   = {}
        lScalar = []
        lArray  = []
        for i in lVars:
            var = unit.GetVariable(i)
            s   = `var`.lower()
            if dDone.get(s): continue
            dDone[s]=1
            
            if var['dimension']:
                lArray.append( (s, var) )
            else:
                lScalar.append(var)
        return (lScalar, lArray)
    # --------------------------------------------------------------------------
    # This subroutine adds all variables that are used in declarations of arrays
    #  to the list of scalars, e.g. real,dimension(m,n) :: a --> add m and n
    def AddVariablesForDeclarations(self, lScalars, lArrays):

        dDone = {}
        # First add all scalars used in array declarations
        for i, var in lArrays:
            l = var.GetAllUsedVariables()
            for j in l:
                if `j`==`var`: continue
                if dDone.get(`j`.lower()): continue
                dDone[`j`.lower()]=1
                print "appending array",j
                lScalars.append(j)


        # We have to add the variables in the right order, so that variables
        # which are used in the init part of another variable are declared
        # in the right order, e.g.:
        # integer, parameter :: n=10
        # integer, parameter :: n12 = n*11
        lNewScalars = []
        dDone = {}
        for i in lScalars:
            if dDone.get(`i`.lower()): continue

            lNewScalars.append(i)
            print "Appending",i,i.DisplayAll()
            dDone[`i`.lower()]=1
            l=i.GetAllUsedVariables()
            for j in l:
                if `j`==`i`: continue
                if dDone.get(`j`.lower()): continue
                # The variable which is used in the declaration must
                # be checked for other dependencies, too
                lScalars.append(j) 
                lNewScalars.insert(0,j)
                dDone[`j`.lower()]=1
                
                print "prepending",j

        # lScalars=lNewScalars would not change the original list
        lScalars[:] = lNewScalars[:]
    # --------------------------------------------------------------------------
    def CreateWriteStatements(self, lScalars, lArrays):
        write   = Write(nUnit=self.nUnit)
        write.AddIOExpression(1)
        l       = [write]
        write   = Write(nUnit=self.nUnit)
        
        #lScalars.sort(lambda x,y:cmp(`x`.lower(), `y`.lower()) )
        for i in lScalars:
            if i["parameter"]: continue
            write.AddIOExpression(i)
        l.append(write)

        lArrays.sort()
        for s, var in lArrays:
            n = var["dimension"].nGetNumberOfDimensions()
            if var["parameter"]: continue
            write   = Write(nUnit=self.nUnit)
            for i in range(n):
                write.AddIOExpression("lbound(%s,%d)" % (s,i+1))
                write.AddIOExpression("ubound(%s,%d)" % (s,i+1))
            l.append(write)
            write   = Write(nUnit=self.nUnit)
            write.AddIOExpression(s)
            l.append(write)
        return l

    # --------------------------------------------------------------------------
    def GenerateWriter(self):

        # Create a deep copy in order to avoid modifying the original file.
        oFile          = copy.deepcopy(self.objFile)

        self.firstStatement = None
        self.lastStatement  = None
        self.lVarUsage=[]
        for unit in oFile:
            # Unknown variables (i.e. parameter to calls) will be considered
            # to be read and written.
            varUsage=VarUsage(bUseUnknown=0)
            bIsCorrectProgUnit=0
            for statement in unit:
                # Ignore comment lines etc.
                if not statement.isStatement(): continue

                # Ignore declaration statements
                if statement.isDeclaration(): continue
                
                loc=statement.GetLocation()
                nLine = loc[0]   # returns (line, column)
                
                # Ignore if line numbers are specified and the statment
                # is outside the specified range
                if self.nLineFrom and nLine<self.nLineFrom: continue
                if self.nLineTo and  nLine>self.nLineTo:    continue
                bIsCorrectProgUnit=1
                # Save pointers to first/last executable statement to
                # know where to insert the newly generated code (this is
                # better than using an index, since inserting will modify
                # the later indices.
                if not statement.isDeclaration():
                    if not self.firstStatement:
                        self.firstStatement = statement
                    self.lastStatement = statement

                statement.GetVarUsage(varUsage)
            if not bIsCorrectProgUnit: continue
            
            self.sPre = unit.sGetUniquePrefix()
            self.lVarUsage.append(varUsage)
            
            # Add declaration for variables            
            # ----------------------------
            vInit = Variable(self.sVar("needinit"))

            d=Declaration("LOGICAL")
            d.AddAttribute("SAVE")
            vInitWithValue = VariableWithInit(vInit,"=",
                                              TrueFalse(".true."))
            d.AppendVariable(vInitWithValue)
            
            lDeclaration = [d]
            lPreRegion   = [ If(oIfCond="%s"%vInit) ]
            # Create the Open statement. If MPI is used, append the rank
            # to the filename so that each process has its own dump file
            oOpen = Open(nUnit=self.nUnit)
            if self.bDoMPI:
                lDeclaration.append(Declaration("CHARACTER(256)",
                                                var=self.sVar("fname")))
                # Saving myrank can be useful if additional conditions
                # on when writing the results are added manually
                lDeclaration.append(Declaration("integer",
                                                var=self.sVar("myrank"),
                                                attribute="save"))
                lDeclaration.append(Declaration("integer",
                                                var=self.sVar("ierr")))
                lDeclaration.append(Include(sFilename="\"mpif.h\""))
                call = Call(sName="MPI_Comm_rank")
                call.AddArgument("MPI_COMM_WORLD")
                call.AddArgument(self.sVar("myrank"))
                call.AddArgument(self.sVar("ierr"))
                write=Write(nUnit=self.sVar("fname"))
                write.AddIOOpt("\"(a,i2.2)\"")
                write.AddIOExpression("\"%s.\""%self.sDumpFile)
                write.AddIOExpression(self.sVar("myrank"))
                
                oOpen.AddIOOpt("file=%s"%self.sVar("fname"))
                lPreRegion.extend([call, write, oOpen])
            else:
                oOpen.AddIOOpt("file='%s'"%self.sDumpFile)
                lPreRegion.append(oOpen)
                
            lPreRegion.extend([Assignment(lhs=vInit, rhs=".FALSE."),
                               EndIf(),
                               If(oIfCond="1.eq.1")
                               ])

            # Create the statements to write all variables to the unit
            # --------------------------------------------------------
            self.lReadScalars, self.lReadArrays  = \
                               self.GetScalarAndArrayVariables(unit,
                                                               varUsage["read" ])
            self.lWriteScalars, self.lWriteArrays = self.GetScalarAndArrayVariables(unit,
                                                                        varUsage["write"])

            # We need all
            self.AddVariablesForDeclarations(self.lReadScalars, self.lReadArrays+self.lWriteArrays)

            lPreRegion.extend(self.CreateWriteStatements(self.lReadScalars, self.lReadArrays))
            lPreRegion.append(EndIf())
            
            lPostRegion = [If(oIfCond="1.eq.1")]
            lPostRegion.extend(self.CreateWriteStatements(self.lWriteScalars,
                                                          self.lWriteArrays))
            lPostRegion.append(EndIf())

            write = Write(nUnit=self.nUnit)
            write.AddIOExpression(-1)
            lPostRegion.extend([If(oIfCond="2.eq.2"),
                                write,
                                Close(nUnit=self.nUnit)])
            if self.bDoMPI:
                call = Call(sName="MPI_Barrier")
                call.AddArgument("MPI_COMM_WORLD")
                call.AddArgument(self.sVar("ierr"))
                lPostRegion.append(call)
            lPostRegion.extend([Stop(),
                                EndIf()])

            unit.AddDeclaration(lDeclaration)
            unit.Insert(lPreRegion, before = self.firstStatement)

            # If there is a return statement as last statement, make sure
            # to add the writing code before the return!
            if(self.lastStatement.isA(Return)):
                unit.Insert(lPostRegion, before  = self.lastStatement )
            else:
                unit.Insert(lPostRegion, after  = self.lastStatement )

        f = open(self.sDumpWriteName,"w")
        f.write(self.stylesheet.ToString(oFile))
        f.write("\n")    # necessary, otherwise the compiler complains
        f.close()
    # --------------------------------------------------------------------------
    def AppendDeclarations(self, lDecl, lScalars, lArrays, bCorrect=0):
        s       = ""
        nCount  = 0
        dDone   = {}

        # First add all declaration - unless the variable is already declared
        # -------------------------------------------------------------------
        for oVar in lScalars:
            # Get the declaration statement, but do not use include or module
            # declaration if the original variable was declared via an include
            # or in a module - this program will be standalone compileable.
            if bCorrect:
                # We have to create a new variable to rename it properly
                oVar = copy.deepcopy(oVar)
                sVarName = self.sCorrectVar(oVar)  # convert to string
                oVar.SetName(sVarName)
            else:
                sVarName = oVar.sGetName()  # convert to string
            if dDone.get(sVarName.lower()): continue
            dDone[sVarName.lower()]=1
            # We have to add constants here, too, since they might be used
            # in the declaration of arrays.
            o = oVar.oCreateDeclarationStatement(bUseInclude=0, bUseModule=0,
                                                 bAddInit=1)
            lDecl.append(o)
            
        for sName, oVar in lArrays:
            if bCorrect:
                oVar = copy.deepcopy(oVar)
                sVarName = self.sCorrectVar(oVar).lower()  # convert to string
                oVar.SetName(sVarName)
            else:
                sVarName = oVar.sGetName().lower()  # convert to string
            if dDone.get(sVarName): continue
            dDone[sVarName]=1
            nDim  = oVar["dimension"].nGetNumberOfDimensions()
            sShape = string.join(":"*nDim,",") # create :,:,:
            decl = Declaration(oVar["type"])
            decl.AddAttribute("dimension(%s)"%sShape)
            decl.AddAttribute("allocatable")
            decl.AppendVariable(oVar)
            lDecl.append(decl)

    # --------------------------------------------------------------------------
    # This subroutine first reads the scalar data from the dump file, then
    # allocates the arrays (depending on the size specified in the dump file),
    # and then reads the values into the allocated variables.
    # If bCorrect is specified, all variables in the two lists will get
    # be created using the prefix in self.sCorrectVar (this is used to declare
    # the 'correct' arrays).
    # If bCorrect is specified, this subroutine will additionally allcoate (but
    # not read) the original arrays, unless they are specified in
    # lAlreadyDeclared. This is necessary to allocate the memory for output
    # only variables (they are declared in the first AppendDeclaration call)
    # lAlreadyDeclared is an array of tuples (string var name, var object).
    def AppendReadInputData(self, lDecl, lMain, lScalars, lArrays,
                            bCorrect=0, lAlreadyDeclared=[]):

        # Convert lAlreadyDeclared into a dictionary for quicker lookup
        dDone = {}
        for i,sVar in lAlreadyDeclared:
            dDone[i.lower()]=1

        s       = ""
        read    = Read(nUnit=self.nUnit)
        for i in lScalars:
            if i["parameter"]: continue
            if bCorrect:
                var = copy.deepcopy(i)
                sVarName = self.sCorrectVar(var)
                var.SetName(sVarName)
            else:
                var=i
            read.AddIOExpression(var)
        lMain.append(read)

        for s, var in lArrays:
            n = var["dimension"].nGetNumberOfDimensions()
            if n>self.nDimMax: self.nDimMax=n
            read     = Read(nUnit=self.nUnit)
            allocate = Allocate()
            if bCorrect:
                var = copy.deepcopy(var)
                sVarName = self.sCorrectVar(var)
                var.SetName(sVarName)
            else:
                sVarName = `var`
            v        = ArraySpecWithName(var=var)
            for i in range(n):
                read.AddIOExpression("%s%d" % (self.sLow,  i) )
                read.AddIOExpression("%s%d" % (self.sHigh, i) )
                v.AddSubscript("%s%d:%s%d"%(self.sLow,  i, self.sHigh, i))

            lMain.append(read)
            allocate.AddVariable(v)
            lMain.append(allocate)
            read   = Read(nUnit=self.nUnit)
            read.AddIOExpression(v)
            lMain.append(read)
            if bCorrect:
                if not(dDone.get(s.lower())):
                    allocate = Allocate()
                    v = ArraySpecWithName(var=s)
                    for i in range(n):
                        v.AddSubscript("%s%d:%s%d"%(self.sLow,  i, self.sHigh, i))
                    allocate.AddVariable(v)
                    lMain.append(allocate)

    # --------------------------------------------------------------------------
    # Add the test etc. for a numerical variable:
    # if( abs(  a(i)-b(i) ) > 0) then
    #    errcount=errcount+1
    #    if( abs( a(i)-b(i)) > fmax) then
    #      fmax = abs( a(i)-b(i) )
    #      ubound0=i
    #    endif
    # endif
    def AppendCheckNumerical(self, lMain, oNew, oCorrect, nDim, sLoopVar):
        oSubtract   = Expression(oNew,"-",oCorrect)
        oAbs        = FunctionCall("abs",oSubtract)
        oCompare    = Expression(oAbs,">","0")
        lMain.append(If(oIfCond=oCompare))                         # if(abs(a-b)>0) then
        
        exp = Expression(Variable(self.sVar("errcount")), "+","1") 
        lMain.append(Assignment(lhs=self.sVar("errcount"),rhs=exp))#  errcount=errcount+1
        
        oCompare    = Expression(oAbs,">",self.sVar("fmax"))
        lMain.append(If(oIfCond=oCompare))                         #  if(abs(a(i)-b(i))>fmax)
        
        lMain.append(Assignment(lhs=self.sVar("fmax"), rhs=oAbs))  #   fmax=abs(a(i)-b(i))
        
        for i in range(nDim):                                   
            lMain.append(Assignment(lhs=self.sVar("ubound%d"%i),   #   ubound0 = i
                                    rhs="%s%d"%(sLoopVar,i)))
        lMain.append(EndIf())                                      #  endif
        lMain.append(EndIf())                                      # endif
       
    # --------------------------------------------------------------------------
    def AppendCheckLogical(self, lMain, oNew, oCorrect, nDim, sLoopVar):
        oCompare    = Expression(oNew,".neqv.",oCorrect)
        lMain.append(If(oIfCond=oCompare))                         # if(a .ne. b) then
        
        exp = Expression(Variable(self.sVar("errcount")), "+","1") 
        lMain.append(Assignment(lhs=self.sVar("errcount"),rhs=exp))#  errcount=errcount+1
        
        for i in range(nDim):                                   
            lMain.append(Assignment(lhs=self.sVar("ubound%d"%i),   #   ubound0 = i
                                    rhs="%s%d"%(sLoopVar,i)))
        lMain.append(EndIf())                                      # endif
    # --------------------------------------------------------------------------
    def AppendCheckOther(self, lMain, oNew, oCorrect, nDim, sLoopVar):
        oCompare    = Expression(oNew,".ne.",oCorrect)
        lMain.append(If(oIfCond=oCompare))                         # if(a .ne. b) then
        
        exp = Expression(Variable(self.sVar("errcount")), "+","1") 
        lMain.append(Assignment(lhs=self.sVar("errcount"),rhs=exp))#  errcount=errcount+1
        
        for i in range(nDim):                                   
            lMain.append(Assignment(lhs=self.sVar("ubound%d"%i),   #   ubound0 = i
                                    rhs="%s%d"%(sLoopVar,i)))
        lMain.append(EndIf())                                      # endif

    # --------------------------------------------------------------------------
    # Appends code to check all elements of one array, and print out the
    # maximum error (if any), and number of errors
    def AppendCheckOneArray(self, lMain, oVar, sLoopVar):
        nDim = oVar["dimension"].nGetNumberOfDimensions()
        lMain.append(Assignment(lhs=self.sVar("fmax"),rhs="0.0"))
        lMain.append(Assignment(lhs=self.sVar("errcount"),rhs="0"))

        # Add all outer loops
        # -------------------
        for i in range(nDim):
            do = Do(var="%s%d"%(sLoopVar, nDim-i-1),
                    sFrom="lbound(%s,%d)"%(oVar, nDim-i),
                    sTo="ubound(%s,%d)"%(oVar, nDim-i)   )
            lMain.append(do)
            
        oNew     = ArraySpecWithName(var=oVar)
        oCorrect = ArraySpecWithName(self.sCorrectVar(oVar))
        for i in range(nDim):
            oNew.AddSubscript("%s%d"%(sLoopVar,i))
            oCorrect.AddSubscript("%s%d"%(sLoopVar,i))
        
        # Check for maximum error
        # -----------------------
        
        # We have to create real objects here (instead of making one string
        # which contains the comparison), since otherwise the expression is
        # too long and the stylesheet can't split the line
        sType = `oVar["type"]`.lower()
        if sType=="real" or sType=="integer" or sType=="complex" or \
           sType=="doubleprecision":
            self.AppendCheckNumerical(lMain, oNew, oCorrect, nDim, sLoopVar)
        elif (sType=="logical"):
            self.AppendCheckLogical(lMain, oNew, oCorrect, nDim, sLoopVar)
        else:
            self.AppendCheckOther(lMain, oNew, oCorrect, nDim, sLoopVar)

        # Add all EndDos for loops
        # ------------------------
        for i in range(nDim):
            lMain.append(EndDo())

        oIf = If(oIfCond="%s>0"%(self.sVar("errcount")))
        lMain.append(oIf)
        pr= Print(format="*")
        pr.AddIOExpression("\"%s: error: %s, number of errors:\""%(self.sDumpPrefix, `oVar`))
        pr.AddIOExpression(self.sVar("errcount"))
        lMain.append(pr)

        oNew     = ArraySpecWithName(var=oVar)
        oCorrect = ArraySpecWithName(self.sCorrectVar(oVar))
        lIndices = []
        for i in range(nDim):
            s = self.sVar("ubound%d"%i)
            oNew.AddSubscript(s)
            oCorrect.AddSubscript(s)
            lIndices.append(s)
            
        pr= Print(format="*")
        pr.AddIOExpression("\"%s: correct\""%self.sDumpPrefix)
        pr.AddIOExpression(oCorrect)
        lMain.append(pr)
        
        pr= Print(format="*")
        pr.AddIOExpression("\"%s: is     \""%self.sDumpPrefix)
        pr.AddIOExpression(oNew)
        lMain.append(pr)

        pr= Print(format="*")
        pr.AddIOExpression("\"%s: at     \""%self.sDumpPrefix)
        for i in lIndices:
            pr.AddIOExpression(i)
        lMain.append(pr)

        lMain.append(EndIf())

    # --------------------------------------------------------------------------
    def AppendResultCheck(self, lDecl, lMain):

        # Check all scalar variables
        # --------------------------
        for i in self.lWriteScalars:
            sCorrect=self.sCorrectVar(i)
            pr = Print(format="*")
            pr.AddIOExpression("\"%s: error scalar variable: %s\""%(self.sDumpPrefix, `i`))
            pr.AddIOExpression(i)
            pr.AddIOExpression(sCorrect)
            if `i["type"]`.lower()=="logical":
                lMain.extend([If(oIfCond="%s.neqv.%s"%(i, sCorrect)),
                              pr,
                              EndIf()
                              ])
            else:
                lMain.extend([If(oIfCond="%s/=%s"%(i, sCorrect)),
                              pr,
                              EndIf()
                              ])

        # Check all arrays
        # ----------------
        sLoopVar=self.sVar("i")
        for i in range(self.nDimMax):
            decl = Declaration("INTEGER", var="%s%d"%(sLoopVar, i))
            lDecl.append(decl)
        lDecl.append(Declaration("real"  ,var=self.sVar("fmax")))
        lDecl.append(Declaration("integer" ,var=self.sVar("errcount")))
        
        for i, oVar in self.lWriteArrays:
            self.AppendCheckOneArray(lMain, oVar, sLoopVar)
            
    # --------------------------------------------------------------------------
    def GenerateDriver(self):

        # Create a deep copy in order to avoid modifying the original file.
        oFile          = copy.deepcopy(self.objFile)

        # Find the right program unit
        n=0
        lAllStatements = []
        for oUnit in oFile:
            varUsage = self.lVarUsage[n]
            for statement in oUnit:
                if not statement.isStatement(): continue
                if statement.isDeclaration(): continue
                loc=statement.GetLocation()
                nLine = loc[0]   # returns (line, column)
                if self.nLineFrom and nLine<self.nLineFrom: continue
                if self.nLineTo and  nLine>self.nLineTo:    continue
                lAllStatements.append(statement)
                unit=oUnit

        # First create main, which reads all variables
        # ( and allocates memory for arrays)
        # --------------------------------------------
        sName = unit.sGetName()
        lDecl = [ProgramStatement(sName="%sDUMP"%sName)]

        # First declare the input variables for the subroutine. ALL variables
        # need to be declared, even the once that are written only (i.e.
        # that are not included in the data file read)
        self.AppendDeclarations(lDecl, self.lReadScalars+self.lWriteScalars,
                                       self.lReadArrays +self.lWriteArrays)
        self.AppendDeclarations(lDecl, self.lWriteScalars, self.lWriteArrays,
                                bCorrect=1)

        sMarkerVar = self.sVar("Marker")
        lDecl.append(Declaration("integer",var=sMarkerVar))
        oOpen = Open(nUnit=self.nUnit)
        oOpen.AddIOOpt("file='%s'"%self.sDumpFile)
        lMain  = [oOpen,
                  ControlLessDo(),                          # DO
                  Read(nUnit=self.nUnit, var=sMarkerVar),   #  read marker
                  IfOnly(oIfCond="%s==-1"%sMarkerVar,       #   if(marker==-1) exit
                         oStatement=Exit())
                 ]
        # Append code to declare and read the
        # variables, and to allocate the arrays
        # -------------------------------------
        self.nDimMax       = -1
        self.sLow          = self.sVar("lbound")
        self.sHigh         = self.sVar("ubound")
        self.dVarAllocated = {}
        self.AppendReadInputData(lDecl, lMain, self.lReadScalars, self.lReadArrays)

        # Declare and allocate the variables with the correct result values
        # -----------------------------------------------------------------
        lMain.extend([Read(nUnit=self.nUnit, var=sMarkerVar),
                      IfOnly(oIfCond="%s==-1"%sMarkerVar,
                             oStatement=Exit())])

        self.AppendReadInputData(lDecl, lMain, self.lWriteScalars,
                                 self.lWriteArrays, bCorrect=1, 
                                 lAlreadyDeclared=self.lReadArrays)


        # Add the call, and create declaration of the subroutine
        # ------------------------------------------------------
        subroutine = SubroutineStatement(sName=sName)
        lSubDecl = [subroutine]
        lSubExec = []
        call = Call(sName=sName)

        dDone = {}
        for i in self.lReadScalars+self.lWriteScalars:
            # Don't pass parameters as argument, since they will be declared as
            # parameter in the subroutine anyway
            if not dDone.get(`i`):
                if not i["parameter"]:
                    call.AddArgument(i)
                    subroutine.AddArgument(i)
                dDone[`i`]=1
                lSubDecl.append(i.oCreateDeclarationStatement(bUseInclude=0,
                                                              bUseModule=0,
                                                              bAddInit=1))
        for i, var in self.lReadArrays+self.lWriteArrays:
            if not dDone.get(i):
                call.AddArgument(var)
                subroutine.AddArgument(i)
                lSubDecl.append(var.oCreateDeclarationStatement())
                dDone[i]=1
            
        lMain.append(call)

        # Now add the code for checking the results
        # -----------------------------------------
                  
        self.AppendResultCheck(lDecl, lMain)

        # Declare the temporary integers used in reading the dimensions
        # -------------------------------------------------------------
        for i in range(self.nDimMax):
            decl = Declaration("INTEGER")
            decl.AppendVariable("%s%d"%(self.sLow, i))
            decl.AppendVariable("%s%d"%(self.sHigh, i))
            lDecl.append(decl)

        lMain.append(EndDo())
        lMain.append(EndProgUnit(sName="PROGRAM %sDUMP"%sName))

        # Create the subroutine to call
        # -----------------------------
        lSubDecl.extend(lAllStatements)
        lSubDecl.append(EndProgUnit(sName="SUBROUTINE %s"%sName))

        # Done
        # ----
        
        main = Program()
        for i in lDecl:
            main.AppendStatement(i)
        for i in lMain:
            main.AppendStatement(i)
        sub = Subroutine()
        for i in lSubDecl:
            sub.AppendStatement(i)
        # We have to suppress attributes, since they can cause chaos with
        # newly created statements. e.g consider:
        # real a(20) ! 20 elements
        # If this is used, the code created might be:
        # real, dimension(20) :: a
        # BUT since the "!" is attached to the ")", it will actually be:
        # real, dimension(20) ! 20 elements :: a
        f = open(self.sDumpReadName,"w")
        f.write(self.stylesheet.ToString(main, bIgnoreAttributes=1))
        f.write("\n") 
        f.write("! ====================================================\n")
        f.write("\n") 
        f.write(self.stylesheet.ToString(sub, bIgnoreAttributes=1))
        f.write("\n")    # necessary, otherwise the compiler complains
        f.close()

    # --------------------------------------------------------------------------
    
# ==============================================================================
def Usage():
    print """Dump [-m] [-l l1-l2] [-n N1,N2,...] file.[f|F|f90|F90]
Creates two version of the Fortran file FILE:
file.write.f90:  A replacement file, which will write all input
                 output variables used in between the lines l1 and
                 l2 (defaults to first and last line of the
                 subroutine) into a file called file.dump. This
                 dump is created on the N1st, N2nd, ... call, and
                 will be closed and the application ended after
                 the last call (default: -n 1)
This data dump can then be used with the second created program:
file.driver.f90: This driver reads the data from a dump file, and calls
                 a subroutine which consists of the line l1-l2. On return,
                 the results from this subroutine are compared with the
                 correct results.
"""
    sys.exit(-1)
# ==============================================================================

if __name__=="__main__":
    try:
        lOpt, lArgs = getopt.getopt(sys.argv[1:],"ml:n:]")
    except getopt.GetoptError:
        Usage()
    # Default parameter: whole file, and write one data set and then exit
    nLineFrom = None
    nLineTo   = None
    bDoMPI    = 0
    lWhenDump = [1]
    for (sKey, sVal) in lOpt:
        if sKey=="-n":
            l = string.split(sVal,",")
            try:
                lWhenDump = map(int,l)
            except ValueError:
                Usage()
        elif sKey=="-m":
            bDoMPI=1
        elif sKey=="-l":
            l = string.split(sVal,"-",1)
            if len(l)==1:
                try:
                    nLineFrom=nLineTo=int(l[0])
                except ValueError:
                    Usage()
            else:
                try:
                    nLineFrom=int(l[0])
                    nLineTo=int(l[1])
                except ValueError:
                    Usage()

    # There must be exactly one filename
    if len(lArgs)!=1:
        Usage()
    sFilename = lArgs[0]
    project = Project()
    #    try:
    objFile = project.oGetObjectForIdentifier(sFilename, "file")
    #except:
    #print "Errors parsing file '%s'."%sFilename
        
    Dump(objFile, nLineFrom, nLineTo, lWhenDump, bDoMPI=bDoMPI)
