#!/usr/bin/env python

import sys
import string
import re
import os
import getopt
from   traceback                  import print_exception
from   Scanner.Token              import Token
from   Scanner.Scanner            import ScannerFactory
from   Grammar.ParseSpecification import ParseSpecification
from   Grammar.ParseExp           import ParseExp
from   Grammar.ParseExecution     import ParseExecution
from   AOR.AttributeString        import AttributeString
from   AOR.File                   import File
from   AOR.ProgUnit               import IncompleteProgUnit
from   AOR.Subroutine             import Subroutine, SubroutineStatement
from   AOR.Function               import Function, FunctionStatement
from   AOR.Blockdata              import Blockdata,  BlockdataStatement, \
                                         EndBlockdata
from   AOR.Module                 import Module, ModuleStatement
from   AOR.Statements             import Contains
from   AOR.SpecialStatements      import CommentLine, CompilerDirective, \
                                         PreDirective
from   Tools.Error                import NotYetImplemented, Error

# ==============================================================================
class DummyProject:
    def __init__(self, sProjectName="test"):
        self.sProjectName=sProjectName
    # --------------------------------------------------------------------------
    # A very simple implementation, not using sType at all, just good
    # enough to find include files in the current directory.
    def oGetObjectForIdentifier(self, sIdentifier, sType):
        sFullName = "./%s"%sIdentifier
        if os.access(sFullName, os.R_OK):
            return sFullName
        return None
# ==============================================================================
class ParserClass(ParseSpecification, ParseExp, ParseExecution):
    # Constructor for File object. The data to parse can be specified
    # as either a filename, a string (\n separated lines), or a list of
    # strings. Only one should be specified.
    #
    # sFilename -- Filename, including path
    #
    # sInput -- Input as a string (lines separated by \n)
    #
    # lInputLines -- List of input lines to parse
    #
    # sFormat   -- Format of the file: 'fix' or 'free' (default is the
    #              default  of the scanner, which is fixed
    #
    def __init__(self, sFilename=None, sInput="", lInputLines=[], 
                 scanner=None, sFormat=None, bTestOnly=None,
                 project=None):
        if project:
            self.project=project
        else:
            self.project=DummyProject("test")
        self.bErrorDuringParsing = 0    # 1 if an error occurred
        ParseSpecification.__init__(self)
        ParseExecution.__init__(self)
        self.dKeyword2Func = {"SUBROUTINE" : self.ParseSubroutine,
                              "FUNCTION"   : self.ParseFunction,
                              "PROGRAM"    : self.ParseProgram,
                              "MODULE"     : self.ParseModule,
                              "BLOCK"      : self.ParseBlockData,
                              "BLOCKDATA"  : self.ParseBlockData }
        # Create the correct scanner
        if sFilename:
            self.scanner = ScannerFactory(name=sFilename, format=sFormat,
                                          project=project)
        else:
            if sInput: lInputLines = string.split(sInput,"\n")
            if lInputLines:
                self.scanner = ScannerFactory(lines=lInputLines,
                                              format=sFormat)
            else:
                if not scanner:
                    raise Error("No input or scanner given")
                self.scanner = scanner

        self.sFormat   = self.scanner.GetFormat()
        assert self.sFormat  in ["fixed","free"]

        # This attributes is the current indentation level. This is the logical
        # indentation level, not the physical. Program units statements are
        # on level 0, declaration and all 'top level' executable statements are
        # on level 1. Statements within blocks (if, do, ...) have the next higher
        # level. It is the task of the output formatter to match the logical
        # level to physical levels: e.g. a user might want to have program unig
        # statements, specifiation, and 'top level' executable statements with
        # the same indentation:
        # subroutine test()        or  subroutine test()
        # integer i                      integer i
        # print *,i                      print *,i
        # end subroutine test          end subroutine test
        self.nIndent=0
        
        # Hook for unit tests: do nothing if this is a test run
        # The test unit will then call the scanner functions to test.
        if bTestOnly:
            self.sub   = Subroutine(None)
            self.oFile = []
            return
        
        self.oFile   = File(sFilename=self.scanner.GetFilename(),
                            sFormat=self.scanner.GetFormat()     )
        try:
            self.ParseFile(self.GetNextToken())
        except NotYetImplemented, w:
            print `w`

        if self.bErrorDuringParsing:
            self.oFile=None
    # --------------------------------------------------------------------------
    # Returns the create file object
    def GetFileObject(self):
        return self.oFile
    # --------------------------------------------------------------------------
    def GetNextToken(self):
        if self.scanner.eof(): return None
        return self.scanner.GetNextToken()
    # --------------------------------------------------------------------------
    def ParseFile(self, tok, bIsTest=0):
        # A stack is needed to store tokens before the keyword determining
        # the correct rule is found (e.g. consider 'recursive function').
        # In addition, we need the location for the first keyword, so the
        # location is stored in this stack as well:
        # stack = [ ( token, location), (token, location), ...]
        stack=[]
        
        while tok:
            if tok[0]==Token.tok_COMMENTLINE or \
               tok[0]==Token.tok_DIRECTIVE   or \
               tok[0]==Token.tok_PREDIRECTIVE:
                stack.append( (tok, self.scanner.GetLocation()) )
                tok=self.GetNextToken()
                assert tok[0]==Token.tok_SEPARATOR
                tok=self.GetNextToken()
                continue
            s = string.upper(tok[1])
            f = self.dKeyword2Func.get(s,None)
            if f:
                tok, obj = f(stack, tok, bIsTest=bIsTest )
                stack = []
            else:
                # Test if we are parsing an 'incomplete' file, e.g.
                # a include file containing only common block information
                if tok[0]==Token.tok_SEPARATOR:
                    tok, obj = self.ParseIncompleteFile(stack, tok, bIsTest=bIsTest)
                    return
                stack.append( (tok, self.scanner.GetLocation()) )
                tok = self.GetNextToken()
        #print "Parsing finished"
        #print "=="*80
        #print `self.oFile`
    # --------------------------------------------------------------------------
    # contains-stmt is CONTAINS
    def ParseContained(self, tok, loc=None, sLabel=None, sName=None):
        contains = Contains(sLabel, loc, tok[1], self.nIndent)
        self.sub.SetContainStatement(contains)
        tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        
        # Very similar to ParseFile above
        stack    = []
        tok      = self.GetNextToken()
        sKeyword = string.upper(tok[1])
        while sKeyword!="END":
            f = self.dKeyword2Func.get(sKeyword,None)
            if f:
                # We can use an attribute self.oldsub, since contained
                # statements are not allowed to be nested! Otherwise
                # we would have to either use a list, or pass oldsub
                # to all Parse{Function,Statements,...} functions
                self.oldsub   = self.sub
                tok, obj = f(stack, tok, bIsContained=1)
                stack = []
                self.sub = self.oldsub
            else:
                stack.append( (tok, self.scanner.GetLocation()) )
                tok = self.GetNextToken()
            sKeyword = string.upper(tok[1])
        return tok, None
    # --------------------------------------------------------------------------
    # Parses the arguments of a subroutine or function. Parameters:
    #
    # tok - The next token - If this is not '(', no arguments are present
    #
    # statement - The statement object to store the arguments (function or
    #             subroutine)
    def ParseArguments(self, tok, statement):
        if tok[1]!='(':
            return tok                  # no arguments present
        statement.SetParOpen(tok[1])
        tok = self.GetNextToken()
        # Parameter list found, parse all parameters
        while tok[1]!=")":
            assert tok[0]==Token.tok_IDENTIFIER
            tokComma = self.GetNextToken()
            # Add the argument to the subroutine - this will automatically
            # add the argument to the subroutine-statement
            if tokComma[1]==",":
                statement.AddArgument(tok[1], sComma=tokComma[1])
                tok = self.GetNextToken()
            else:
                statement.AddArgument(tok[1])
                tok = tokComma
        statement.SetParClose(tok[1])
        return self.GetNextToken()
        
    # --------------------------------------------------------------------------
    def ParseDeclarationAndExecutionPart(self, tok):
        self.sub.SetIsExec(0)
        # Now we are reading the specification part
        # -----------------------------------------
        try:
            tok = self.ParseStatements(tok,
                                       dEnd={"END":self.ParseEndProgUnit,
                                             "ENDSUBROUTINE":self.ParseEndProgUnit},
                                       nIndentModifier=1)
        except:
            self.bErrorDuringParsing = 1
            print "Error while parsing '%s'"%\
                  self.sub.sGetName()
            print "file:",self.scanner.GetFileLocation()
            print self.scanner.GetCurrentLine()
            excp, value, tb = sys.exc_info()
            print_exception(excp, value, tb)
            return None
        return tok
    # --------------------------------------------------------------------------
    def ParseSubroutine(self, stack, tok, bIsTest=0, bIsContained=0):
        self.sub = Subroutine()
        # First append each non-real statements to the subroutine:
        if stack:
            flag = 1
            while flag and stack:
                if stack[0][0][0]==Token.tok_COMMENTLINE:
                    self.sub.AppendStatement( CommentLine(stack[0][0][1]) )
                elif stack[0][0][0]==Token.tok_DIRECTIVE:
                    self.sub.AppendStatement( CompilerDirective(stack[0][0][1]) )
                elif stack[0][0][0]==Token.tok_PREDIRECTIVE:
                    self.sub.AppendStatement( PreDirective(stack[0][0][1], self.scanner.GetLocation()) )
                else:
                    flag=0
                if flag:
                    del stack[0]
            # To get the right position for the 'subroutine', we use the
            # column (and line) of the first prefix (if there is a prefix)
            if stack:
                loc = stack[0][1]
            else:
                loc = self.scanner.GetLocation()
        else:
            loc = self.scanner.GetLocation()
            
        tokName = self.GetNextToken()
        
        # Create the subroutine object
        # Stack is [ ( token, location), (token, location), ...]!
        subStatement = SubroutineStatement(loc=loc,
                                           lPrefix=map(lambda x:x[0][1],
                                                       stack),
                                           sSub=tok[1],
                                           sName=tokName[1],
                                           nIndent=0,
                                           oSub = self.sub)
        self.sub.AppendStatement(subStatement)
        # Only append the subroutine to the file object, if we are not parsing
        # a contained statement (in the latter case the subroutine is appended
        # to the 'outer' subroutine in ParseContained).
        if not bIsContained:
            self.oFile.append(self.sub)
        else:
            self.oldsub.AddContained(self.sub)

        # Look for arguments
        tok = self.ParseArguments(self.GetNextToken(), subStatement)
        if tok[1]==",":
            # Following now: BIND ( C [ , NAME = scalar-char-initialization-expr ] )
            print "language-binding-spec currently not supported"
            return
        assert tok[0]==Token.tok_SEPARATOR
        if bIsTest:
            return self.GetNextToken(), subStatement
        
        tok = self.ParseDeclarationAndExecutionPart(self.GetNextToken())
        #tok = self.ParseInternal(tok)
        return tok, self.sub
        
    # --------------------------------------------------------------------------
    def ParseFunction(self, stack, tok, bIsTest=0, bIsContained=0):
        # For functions we might have to parse more complex types, so we
        # put everything we have read up to now back to the scanner, and start
        # all over again.
        # stack = [ ( token, location), (token, location), ...]
        self.scanner.UnGet(tok)
        for i in  stack:
            self.scanner.UnGet(i[0])
        tok   = self.GetNextToken()
        loc = self.scanner.GetLocation()
        stack = []
        sType = None
        while string.upper(tok[1])!="FUNCTION":
            sKeyword = string.upper(tok[1])
            if sKeyword=="RECURSIVE" or sKeyword=="ELEMENTAL" or \
               sKeyword=="PURE":
                stack.append(tok[1])
                tok = self.GetNextToken()
            else:
                # Now we have a declaration type spec
                tok, exp = self.ParseTypeSpec(tok)
                stack.append(exp)
                sType = exp
        
        tokName = self.GetNextToken()
        # Stack is [ ( token, location), (token, location), ...]!
        funcStatement = FunctionStatement(loc=loc, nIndent=0, lType = stack,
                                          sFunc=tok[1], sName=tokName[1])

        # Create the subroutine object
        self.sub = Subroutine(funcStatement)

        if sType:
            self.sub.GetVariable(tokName[1], {'type':sType}, bAutoAdd=1)
        else:
            self.sub.GetVariable(tokName[1], bAutoAdd=1)
            
        # Only append the subroutine to the file object, if we are not parsing
        # a contained statement (in the latter case the subroutine is appended
        # to the 'outer' subroutine in ParseContained).
        if not bIsContained:
            self.oFile.append(self.sub)
        else:
            self.oldsub.AddContained(self.sub)

        # Look for arguments
        tok = self.ParseArguments(self.GetNextToken(), funcStatement)
        if tok[1]==",":
            # Following now: BIND ( C [ , NAME = scalar-char-initialization-expr ] )
            print "language-binding-spec currently not supported"
            return
        if string.upper(tok[1])=="RESULT":
            funcStatement.SetResult(tok[1], self.GetNextToken()[1],
                                    self.GetNextToken()[1],
                                    self.GetNextToken()[1])
            tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        if bIsTest:
            return self.GetNextToken(), funcStatement
        
        tok = self.ParseDeclarationAndExecutionPart(self.GetNextToken())
        #tok = self.ParseInternal(tok)
        return tok, self.sub
        
    # --------------------------------------------------------------------------
    def ParseProgram(self, stack, tok, bIsTest=0, bIsContained=0):
        raise NotYetImplemented("Program", self.scanner)
    # --------------------------------------------------------------------------
    def ParseModule(self, stack, tok, bIsTest=0, bIsContained=0):
        loc = self.scanner.GetLocation()
        tokName = self.GetNextToken()
        # Create the subroutine object
        self.sub = Module()
        # Stack is [ ( token, location), (token, location), ...]!
        modStatement = ModuleStatement(loc=loc,
                                       sModule=tok[1],
                                       sName=tokName[1],
                                       nIndent=0,
                                       oModule = self.sub)
        self.sub.AppendStatement(modStatement)
        if not bIsContained:
            self.oFile.append(self.sub)
        else:
            self.oldsub.AddContained(self.sub)
        assert self.GetNextToken()[0]==Token.tok_SEPARATOR
        if bIsTest:
            return self.GetNextToken(), modStatement
        
        tok = self.ParseDeclarationAndExecutionPart(self.GetNextToken())
        return tok, self.sub
        
    # --------------------------------------------------------------------------
    def ParseBlockData(self, stack, tok, bIsTest=0, bIsContained=0):
        if stack:
            loc = stack[0][1]
        else:
            loc = self.scanner.GetLocation()
        if string.upper(tok[1])=='BLOCK':
            sBlock = tok[1]
            sData = self.GetNextToken()[1]
        else:
            if isinstance(tok[1], AttributeString):
                sBlock, sData = tok[1].tSplitString(5)
            else:
                sBlock = tok[1][0:5]
                sData  = tok[1][5: ]
        tokName = self.GetNextToken()
        if tokName[0]!=Token.tok_SEPARATOR:
            blockdataStatement = BlockdataStatement(loc=loc, sBlock=sBlock,
                                                    sData=sData,
                                                    sName=tokName[1],
                                                    nIndent=0)
            tok = self.GetNextToken()
        else:
            blockdataStatement = BlockdataStatement(loc=loc, sBlock=sBlock,
                                                    sData=sData,
                                                    nIndent=0)
        assert tok[0]==Token.tok_SEPARATOR
        self.sub = Blockdata(blockdataStatement)
        
        # Only append the subroutine to the file object, if we are not parsing
        # a contained statement (in the latter case the subroutine is appended
        # to the 'outer' subroutine in ParseContained).
        if not bIsContained:
            self.oFile.append(self.sub)
        else:
            self.oldsub.AddContained(self.sub)
        self.ParseDeclarationAndExecutionPart(self.GetNextToken())
#         try:
#             #print "declaration parsing",tok
#             #tokEnd       = self.ParseSpecification(self.GetNextToken() )
#             tokEnd       = self.ParseStatements(self.GetNextToken(),
#                                                 dEnd={"END":self.ParseEndProgUnit},\
#                                                 nIndentModifier=1)
#             print tokEnd
#             assert string.upper(tokEnd[1])=='END'
#             print "Declaration stopping at",tokEnd
#         except :
#             print "Error while parsing declaration part of %s"%\
#                   self.sub.GetName()
#             print "file:",self.scanner.GetFileLocation()
#             print self.scanner.GetCurrentLine()
#             excp, value, tb = sys.exc_info()
#             print_exception(excp, value, tb)
#             return None                 # this aborts the outer loop

#        tok = self.GetNextToken()
        return self.GetNextToken(), self.sub
        if tok[0]!=Token.tok_SEPARATOR:
            if string.upper(tok[1])=='BLOCK':
                sBlock = tok[1]
                sData = self.GetNextToken()[1]
            else:
                if isinstance(tok[1], AttributeString):
                    sBlock, sData = tok[1].tSplitString(5)
                else:
                    sBlock = tok[1][0:5]
                    sData  = tok[1][5: ]
            tok = self.GetNextToken()
            if tok and tok[0]!=Token.tok_SEPARATOR:
                sName = tok[1]
                tok[0] = self.GetNextToken()
            else:
                sName = None
        else:
            sName  = None
            sBlock = None
            sData  = None
        ebd = EndBlockdata(sEnd=tokEnd[1], sBlock=sBlock,  sData=sData,
                           sName=sName, nIndent=self.nIndent-1)
        self.sub.AppendStatement(ebd)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), self.sub
    # --------------------------------------------------------------------------
    def ParseIncompleteFile(self, stack, tok, bIsTest=0, bIsContained=0):
        # Push back all read tokens to get a clear start for parsing.
        # The stack is [ (token,location), (token, location), ...]
        self.scanner.UnGet(tok)
        for i in range(len(stack)-1, 0, -1):
            self.scanner.UnGet(stack[i][0])
        # The first token is still on the stack
        
        self.sub = IncompleteProgUnit()
        self.oFile.append(self.sub)
        tok = self.ParseDeclarationAndExecutionPart(stack[0][0])
        return tok, self.sub
        
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
            
# ==============================================================================
def Parser(sFilename=None, sInput=None, lInputLines=None,
           sFormat=None, project=None):
    p = ParserClass(sFilename=sFilename, sInput=sInput, sFormat=sFormat,
                    lInputLines=lInputLines, project=project)
    return p.GetFileObject()
# ==============================================================================
def usage():
    print "Usage: Parser.py [-P] [-i] <list of files>"
    print
    print "-P: Profile"
    print "-i: Generate interface"
# ------------------------------------    
if __name__=="__main__":

    bDoProfile = 0
    bDoPrint   = 0
    bDoTest    = 0
    bInterface = 0
    # P : Profile
    # O : Output tokens
    lOpt, lArgs = getopt.getopt(sys.argv[1:],"PoTi")
    for i in lOpt:
        if i[0]=="-P":
            bDoProfile=1
        elif i[0]=="-o":
            bDoPrint=1
        elif i[0]=="-T":
            bDoTest=1
        elif i[0]=="-i":
            bInterface=1
            
    if len(lArgs)<1:
        usage()

    project = DummyProject()
    if not bDoProfile:
        for i in lArgs:
            objFile = Parser(i)
            if bDoPrint:
                from Stylesheets.f77 import f77
                s = f77()
                print s.ToString(objFile)

            if bInterface:
                from Analyser.Interface import GenerateInterface
                from Stylesheets.f77    import f77
                ssheet = f77()
                ssheet['keywordcase']='upper'
                for i in objFile.GetAllProgUnits(Subroutine):
                    print ssheet.ToString(GenerateInterface(i, ssheet),
                                          bIgnoreAttributes=1)
    else:
        import profile
        profile.run(
"""for i in lArgs:
       objFile = Parser(sFilename=i)
""")
