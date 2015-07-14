#! /usr/bin/env python

# This is used by Parser

import string
import sys
from   traceback             import print_exception
from   Scanner.Token         import Token
from   Tools.Error           import NotYetImplemented, Error
from   AOR.AttributeString   import AttributeString
from   AOR.SpecialStatements import CompilerDirective, PreDirective,           \
                                    CommentLine
from   AOR.If                import IfOnly, If, ElseIf, Else, EndIf,           \
                                    ArithmeticIf
from   AOR.Do                import ControlLessDo, Cycle, Do, DoWhile, EndDo,  \
                                    Exit
from   AOR.Select            import Select, Case, EndSelect
from   AOR.ProgUnit          import EndProgUnit
from   AOR.Statements        import Allocate, Assignment, Call, Continue,      \
                                    Deallocate, Goto, ComputedGoto, Nullify,   \
                                    OptionString, Pause, Return, Stop
from   AOR.Declaration       import Include, StatementFunction
from   AOR.IO                import Backspace, Close, Endfile, Format, Inquire,\
                                    Open, Print, Read, Rewind, Write

#  RR216    action-stmt
#          or      forall-stmt
#          or      wait-stmt
#          or      where-stmt

class ParseExecution:
    
    def __init__(self):
        # Mapping of keywords to parser functions to call
        self.dDecl2Function = {
                               # Declaration statements
                               "CHARACTER" : self.ParseTypeDeclaration,
                               "COMPLEX"   : self.ParseTypeDeclaration,
                               "INTEGER"   : self.ParseTypeDeclaration,
                               "DOUBLE"    : self.ParseTypeDeclaration,
                               "DOUBLEPRECISION": self.ParseTypeDeclaration,
                               "LOGICAL"   : self.ParseTypeDeclaration,
                               "REAL"      : self.ParseTypeDeclaration,
                               "TYPE"      : self.ParseTypeDeclaration,
                               "COMMON"    : self.ParseCommon,
                               "NAMELIST"  : self.ParseNamelist,
                               "GLOBAL"    : self.ParseCommon,
                               "DIMENSION" : self.ParseDimension,
                               "IMPLICIT"  : self.ParseImplicit,
                               "INTRINSIC" : self.ParseIntrinsic,
                               "PARAMETER" : self.ParseParameter,
                               "SAVE"      : self.ParseSave,
                               "PUBLIC"    : self.ParsePublicPrivate,
                               "PRIVATE"   : self.ParsePublicPrivate,
                               "USE"       : self.ParseUse,
                               "POINTER"   : self.ParsePointer,
                               "EQUIVALENCE":self.ParseEquivalence,
                               "DATA"      : self.ParseData,
                               "INCLUDE"   : self.ParseInclude,
                               "EXTERNAL"  : self.ParseExternal,
                               "INTERFACE" : self.ParseInterface,
                               "MODULE"    : self.ParseModuleProcedure,
                               "PROCEDURE" : self.ParseModuleProcedure,
                               "SUBROUTINE": self.ParseSubroutineStatement,
                               }
        self.dExec2Function = {
                               # Executable statements
                               "IF"        : self.ParseIf,
                               "DO"        : self.ParseDo,
                               "CONTINUE"  : self.ParseContinue,
                               "RETURN"    : self.ParseReturn,
                               "ALLOCATE"  : self.ParseAllocate,
                               "DEALLOCATE": self.ParseDeallocate,
                               "NULLIFY"   : self.ParseNullify,
                               "CALL"      : self.ParseCall,
                               "PRINT"     : self.ParsePrint,
                               "READ"      : self.ParseRead,
                               "WRITE"     : self.ParseWrite,
                               "CLOSE"     : self.ParseClose,
                               "OPEN"      : self.ParseOpen,
                               "REWIND"    : self.ParseRewind,
                               "BACKSPACE" : self.ParseBackspace,
                               "ENDFILE"   : self.ParseEndfile,
                               "INQUIRE"   : self.ParseInquire,
                               "CYCLE"     : self.ParseCycle,
                               "EXIT"      : self.ParseExit,
                               "GOTO"      : self.ParseGoto,
                               "STOP"      : self.ParseStop,
                               "PAUSE"     : self.ParsePause,
                               "GO"        : self.ParseGoto,
                               "FORMAT"    : self.ParseFormat,
                               "INCLUDE"   : self.ParseInclude,
                               "SELECT"    : self.ParseSelect,
                               "SELECTCASE": self.ParseSelect,
                               "CASE"      : self.ParseCase,
                               # In Parser.py:
                               "CONTAINS"  : self.ParseContained,
                               
                               }

        # The label stack is used for non-blocking do loops, where
        # more than one do loop might have the same continue (or action
        # statement) label.
        self.LabelStack = []
    
    # --------------------------------------------------------------------------
    def NotYet(self, tok, loc=None, sLabel=None, sName=None):
        raise NotYetImplemented("%s statement"%tok[1], self.scanner)
    # --------------------------------------------------------------------------
    # Parse:  execution-part-construct is executable-construct or format-stmt
    #                                  or entry-stmt or data-stmt
    #         executable-construct is action-stmt or associate-construct or
    #                                 case-construct or do-construct or
    #                                 forall-construct or if-construct or
    #                                 select-type-construct or where-construct
    #
    # Parses a block of statements and appends each statement to the current
    # self.sub object. Return value:
    # either a pair (token, execution-block), or a tuple (token,
    # execution-block, end-statement) is returned (see dEnd below). Parameters:
    #
    # tok -- Next token.
    #
    # dEnd -- Dictionary containing all keywords which end the current block
    #         as keys of an dictionary. If the value of the dictionary for a
    #         keyword is 1, the next token (which is the keyword) and the
    #         execution block is returned, otherwise the value must be a parser
    #         function which is then called. In this case, the end object is
    #         returned in addition to the next token and the execution block.
    #       
    # bOnlyOneStatement -- If this is true, only one statement is parsed
    #                      (and returned). This is used for if-statments
    #                      (not if-then-statements)
    #
    # nIndentModifier -- value which is at the beginning added to self.nindent,
    #                    and later subtracted. Used when parsing an indented
    #                    block
    def ParseStatements(self, tok=None, dEnd={}, bOnlyOneStatement=0,
                        nIndentModifier=0):
        if not tok: tok=self.GetNextToken()
        self.nIndent = self.nIndent+nIndentModifier
        sName        = ""
        sLabel       = None
        # Flag which indicates if we are already in the execution part
        # (used to identify e.g. an assignment to a variable called 'data',
        # or 'open'). This does not solve the problem of using keywords as
        # identifiers in all cases, but it helps in most cases (it doesn't work
        # if the assignment to (e.g.) 'data' is the first statement after the
        # specification part)
        
        while 1:
            # Check for end of file
            # ---------------------
            if not tok:
                self.nIndent = self.nIndent-nIndentModifier
                return tok

            # Check for label:
            if tok[0]==Token.tok_LABEL:
                sLabel=tok[1]
                tok = self.GetNextToken()
                if not tok:            # shouldn't happen: label w\out statement
                    self.nIndent = self.nIndent-nIndentModifier
                    return tok


            # Check for certain 'extentions' to the grammar: comment lines,
            # compiler directives, and preprocessor directives are stored in
            # the subroutine object as special objects.
            # ------------------------------------------------------------------
            loc      = self.scanner.GetLocation()

            if tok[0]==Token.tok_DIRECTIVE:
                self.sub.AppendStatement(CompilerDirective(tok[1], loc))
                self.scanner.GetNextToken()       # skip separator
                tok = self.scanner.GetNextToken()
                continue
            if tok[0]==Token.tok_PREDIRECTIVE:
                self.sub.AppendStatement(PreDirective(tok[1], loc))
                self.scanner.GetNextToken()       # skip separator
                tok = self.scanner.GetNextToken()
                continue
            if tok[0]==Token.tok_COMMENTLINE:
                self.sub.AppendStatement(CommentLine(tok[1], loc))
                self.scanner.GetNextToken()       # skip separator
                tok = self.scanner.GetNextToken()
                continue
            
            # Find the parser function to call for the read keyword
            # -----------------------------------------------------
            sKeyword = string.upper(tok[1])

            # First look in the list of end keywords
            # --------------------------------------
            f = dEnd.get(sKeyword, None)
            if f:
                tok, obj = apply(f, (tok, loc, sLabel, sName))
                if obj:
                    self.sub.AppendStatement(obj)
                self.nIndent = self.nIndent-nIndentModifier
                return tok
            
            # Not an end of block statement, so call the parser function
            # ----------------------------------------------------------
            if not self.sub.bIsExec():
                f = self.dDecl2Function.get(sKeyword)
            else:
                f = None
            if not f:
                f = self.dExec2Function.get(sKeyword)
                if f: self.sub.SetIsExec(1)
            #print "keyword",sKeyword, loc, self.sub.bIsExec()
            if f:
                try:
                    tok, obj = apply(f, (tok, loc, sLabel, sName) )
                    if obj:
                        obj.SetEndLocation(self.scanner.GetPreviousLocation())
                    # This is used for parsing if statements (without 'then')
                    # the statement shouldn't be added to the current
                    # subroutine
                    if bOnlyOneStatement:
                        self.nIndent = self.nIndent-nIndentModifier
                        return tok, obj
                    # A none object indicates, that the object was already
                    # added to the subroutine. This happens e.g. in the case
                    # of an if statement: when parsing the if statement, the
                    # if object is added to the subroutine, then ParseStatements
                    # is called to read the statements, elseif, endif, ...
                    # statements. So, when the if returns, nothing should be
                    # added to the subroutine, since all parts of the if
                    # statement (include the endif) have already been added.
                    if obj:
                        self.sub.AppendStatement(obj)

#                 except SystemExit, e:
#                     print "==================================================="
#                     print e
#                     print "==================================================="
#                     self.nIndent = self.nIndent-nIndentModifier
#                     while tok and tok[0]!=Token.tok_SEPARATOR:
#                         tok = self.GetNextToken()
#                     if not tok: return tok
#                     tok = self.GetNextToken()
                except NotYetImplemented, e:
                    print "==================================================="
                    print e
                    print "==================================================="
                    self.nIndent = self.nIndent-nIndentModifier
                    while tok and tok[0]!=Token.tok_SEPARATOR:
                        tok = self.GetNextToken()
                    if not tok: return tok
                    tok = self.GetNextToken()
                except:
                    print "Error in'%s'"%self.scanner.GetFileLocation()
                    print "Line: '%s'"%self.scanner.GetCurrentLine()
                    self.bErrorDuringParsing = 1
                    excp, value, tb = sys.exc_info()
                    print_exception(excp, value, tb)
                    while tok and tok[0]!=Token.tok_SEPARATOR:
                        tok = self.GetNextToken()
                    if not tok: return tok
                    tok = self.GetNextToken()
            else:
                nexttoken = self.GetNextToken()
                # Test if this is the name of a statement. A name is
                # identified by a ':' after a literal. Unfortunately,
                # if the next token is not a ":", we have an assignment,
                # and we have to unget this last token.
                if nexttoken[1]==":":
                    sName = tok[1]+nexttoken[1]
                    tok   = self.GetNextToken()
                    continue
                
                # Now it must be an assignment or 
                # a pointer assignment statement
                # -------------------------------
                self.scanner.UnGet(nexttoken)
                try:
                    tok, obj = self.ParseAssignment(tok,
                                                    self.scanner.GetLocation(),
                                                    sLabel, sName)
                except ValueError:
                    print 'Problem with statement',self.scanner.GetFileLocation()
                    print self.scanner.GetCurrentLine()
                    print 'This statement is ignored'
                    obj = None
                    tok = self.GetBeginOfNextStatement()

                if bOnlyOneStatement:
                    self.nIndent = self.nIndent-nIndentModifier
                    return tok, obj
                # This if statement is basically meant for error handling
                # only, since in this case obj is None
                if obj:
                    self.sub.AppendStatement(obj)

            # Reset the label and name statement variable
            # -------------------------------------------
            sLabel = None
            sName  = None

            # Now check if on the top of the stack is a 'none'. This is
            # only the case if we are parsing a non-block do loop, and
            # the statement ending a (more) inner do loop was found.
            # This means, that we have to end parsing the (more outer)
            # loop now, and do not have an end statement for this
            # do block. This is indicated by appending a 'none' as
            # to self.sub 
            # ParseDo will move the last statement (the just appended
            # none) to ParseDo.end, where it is treated correctly.
            if self.LabelStack and self.LabelStack[-1]==None:
                del self.LabelStack[-1]
                self.nIndent = self.nIndent-nIndentModifier
                return tok

            # See if a do loop is parsed and the label of the current
            # statement is the same as an end-label of the last do loop.
            # If so, that means that the last do loop and all previous
            # do loops with the same end-label are completed (this is for
            # non-blocked do loops). In this case set the end-label for
            # all those completed do loops to none, which signals that
            # these do loops are non-blocked ones and so do not have
            # an end statement. The 'higher level' ParseStatements
            # calls will check if the LabelStack entry was set to None
            # (which will tell ParseDo that this is a non-blocked do)
            # and return, without trying to read the closing statement
            # [see if-statement above where this is checked]
            if self.LabelStack and self.sub and \
               self.sub[-1].LabelIs(self.LabelStack[-1]):
                del self.LabelStack[-1]
                if self.LabelStack and \
                   self.sub[-1].LabelIs(self.LabelStack[-1]):
                    for i in range(len(self.LabelStack)):
                        if self.sub[-1].LabelIs(self.LabelStack[i]):
                            self.LabelStack[i]=None
                self.nIndent = self.nIndent-nIndentModifier
                return tok

    # --------------------------------------------------------------------------
    # Error handling function - find the begin of the next statement
    def GetBeginOfNextStatement(self):
        # This unget isn't nice, but sometimes if a short statement isn't
        # detected correctly, the next token might already be part of the
        # second-next statement, therefore ignoring one statement. By doing
        # an unget first, we seem to get more useful results.
        self.scanner.UnGet(None)
        tok = self.GetNextToken()
        while tok and tok[0]!=Token.tok_SEPARATOR:
            tok = self.GetNextToken()
        return self.GetNextToken()
    # --------------------------------------------------------------------------
    # This function is called from ParseStatements and ParseSpecification -
    def ParseInclude(self, tok, loc=None, sLabel=None, sName=None):
        tokName = self.GetNextToken()
        include = Include(loc=loc, nIndent=self.nIndent, sInclude=tok[1],
                          sFilename=tokName[1])
        tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        # The include filename is a string which includes '' - so these
        # quotes have to be removed.
        self.scanner.DoInclude(tokName[1][1:-1])
        return self.GetNextToken(), include
                          
    # --------------------------------------------------------------------------
    # allocate-stmt is ALLOCATE ( [ type-spec :: ] allocation-list
    #                             [, alloc-opt-list ] )
    # alloc-opt	is STAT = stat-variable or ERRMSG = errmsg-variable or
    #              SOURCE = source-variable
    # allocation is allocate-object [ ( allocate-shape-spec-list ) ]
    # allocate-shape-spec is [ allocate-lower-bound : ] allocate-upper-bound
    # allocate-object is variable-name or structure-component
    def ParseAllocate(self, tok, loc=None, sLabel=None, sName=None):
        return self.SubAllocateParam(tok, loc, sLabel, Allocate,
                                     ["STAT","ERRMSG","SOURCE"])
    # --------------------------------------------------------------------------
    # assignment-stmt is variable = expr
    def ParseAssignment(self, tok, loc=None, sLabel=None, sName=None):
        # We have to test if we are dealing with a statement function
        var=self.sub.GetVariable(tok[1], bAutoAdd=0)
        cl = Assignment
        # A statement function is identified by having an opening parenthesis
        # after the name, but not being declared as an array
        if not (var and var.bIsArray()):
            tokNext = self.GetNextToken()
            if tokNext[1]=='(':
                cl = StatementFunction
            else:
                self.sub.SetIsExec(1) # It's an assignment
            self.scanner.UnGet(tokNext)
        else:
            # It is an assignment, so we set the 'parsing executable
            # statements' flag
            self.sub.SetIsExec(1)
        tokEqual, lhs = self.ParsePrimary(tok)
        
        assert tokEqual[1]=="=" or tokEqual[1]=='=>'
        tok, rhs = self.ParseExpression(self.GetNextToken())
        assign = cl(sLabel, loc, self.nIndent,
                    lhs, tokEqual[1], rhs)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), assign
        
    # --------------------------------------------------------------------------
    # call-stmt is CALL procedure-designator [ ( [ actual-arg-spec-list ] ) ]
    # procedure-designator is procedure-name or
    #                         data-ref % procedure-component-name
    #                         data-ref % binding-name
    # actual-arg-spec is [ keyword = ] actual-arg
    # actual-arg is expr or variable or procedure-name or alt-return-spec
    # alt-return-spec is * label
    def ParseCall(self, tok, loc=None, sLabel=None, sName=None):
        # The procedure-designator can be an expression, but we can't
        # simply use ParseExpression, since it would (try to) parse
        # the actual arguments as well (as an array expression or function
        # call).
        tokName = self.GetNextToken()
        nexttok = self.GetNextToken()
        if nexttok and nexttok[1]=="%":
            raise NotYetImplemented("data-ref for calls: a%b",self.scanner)
        
        call = Call(sLabel, loc, tok[1], tokName[1], self.nIndent)
        self.sub.AddCall(tok[1], loc, "subroutine")
        tok = nexttok

        if tok[1]!="(":
            assert tok[0]==Token.tok_SEPARATOR
            return self.GetNextToken(), call
        tok = self.ParseProcedureArgs(call, tok)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), call
    # --------------------------------------------------------------------------
    # Parses the arguments of a function or subroutine call
    def ParseProcedureArgs(self, call, tok):
        call.SetParOpen(tok[1])
        # Now parse the actual arguments
        tok = self.GetNextToken()
        while tok[1]!=")":
            # First test if this is a "keyword=arg" argument
            tokNext = self.GetNextToken()
            if tokNext[1]=="=":
                keyword=tok[1]
                tokLookAhead=self.GetNextToken()
                if tokLookAhead[1]=="*":
                    tokLabel=self.GetNextToken()
                    tokSecondNext=self.GetNextToken()
                    if tokSecondNext[1]==",":
                        call.AddKeywordAltReturn(sKeyword=keyword,
                                                 sEqual=tokNext[1],
                                                 sStar=tokLookAhead[1],
                                                 sLabel=tokLabel[1],
                                                 sComma=tokSecondNext[1])
                        tokSecondNext = self.GetNextToken()
                    else:
                        call.AddKeywordAltReturn(sKeyword=keyword,
                                                 sEqual=tokNext[1],
                                                 sStar=tokLookAhead[1],
                                                 sLabel=tokLabel[1])
                else:
                    tokSecondNext, obj = self.ParseExpression(tokLookAhead)
                    if tokSecondNext[1]==",":
                        call.AddKeywordArgument(sKeyword=tok[1],
                                                sEqual=tokNext[1], obj=obj,
                                                sComma = tokSecondNext[1])
                        tokSecondNext = self.GetNextToken()
                    else:
                        call.AddKeywordArgument(sKeyword=tok[1],
                                                sEqual=tokNext[1], obj=obj)
                tok=tokSecondNext
                continue
            
            self.scanner.UnGet(tokNext)
            if tok[1]=="*":
                tokLabel = self.GetNextToken()
                tokComma = self.GetNextToken()
                if tokComma[1]==",":
                    call.AddAltReturn(sStar=tok[1], sLabel=tokLabel[1],
                                      sComma=tokComma[1])
                    tok = self.GetNextToken()
                else:
                    call.AddAltReturn(sStar=tok[1], sLabel=tokLabel[1])
                    tok = tokComma
            else:
                tokComma, arg = self.ParseExpression(tok)
                if tokComma[1]==",":                    
                    call.AddArgument(arg=arg, sComma=tokComma[1])
                    tok = self.GetNextToken()
                else:
                    call.AddArgument(arg=arg)
                    tok = tokComma
        call.SetParClose(tok[1])
        #tok = self.GetNextToken()
        return self.GetNextToken()
    # --------------------------------------------------------------------------
    # close-stmt is CLOSE ( close-spec-list )
    # close-spec is [ UNIT = ] file-unit-number or IOSTAT = scalar-int-variable
    #            or IOMSG = iomsg-variable or ERR = label
    #            or STATUS = scalar-default-char-expr
    def ParseClose(self, keywordtoken, loc=None, sLabel=None, sName=None):
        close = Close(sLabel, loc, self.nIndent, keywordtoken[1],
                      self.GetNextToken()[1])
        tok   = self.ParseIOControlSpec(self.GetNextToken(), close)
        close.SetParClose(tok[1])
        tok   = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), close
    # --------------------------------------------------------------------------
    # continue-stmt is CONTINUE
    def ParseContinue(self, keywordtoken, loc=None, sLabel=None, sName=None):
        tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), Continue(sLabel, loc,
                                             keywordtoken[1],
                                             self.nIndent)

    # --------------------------------------------------------------------------
    def ParseDeallocate(self, tok, loc=None, sLabel=None, sName=None):
        return self.SubAllocateParam(tok, loc, sLabel, Deallocate,
                                     ["STAT","ERRMSG"])
    # --------------------------------------------------------------------------
    # nullify-stmt is NULLIFY ( pointer-object-list )
    # pointer-object is variable-name or structure-component or	proc-pointer-name
    def ParseNullify(self, tok, loc=None, sLabel=None, sName=None):
        nullify = Nullify(sLabel, loc, tok[1],
                          self.GetNextToken()[1], self.nIndent)
        tok = self.GetNextToken()
        while tok[1]!=')':
            tok, expr = self.ParseExpression(tok)
            if tok[1]==",":
                nullify.AddExpression(expr, tok[1])
                tok = self.GetNextToken()
            else:
                nullify.AddExpression(expr)
        nullify.SetParClose(tok[1])
        tok=self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), nullify
    # --------------------------------------------------------------------------
    # do-construct       is block-do-construct or nonblock-do-construct
    # block-do-construct is do-stmt do-block end-do
    # do-stmt            is label-do-stmt or nonlabel-do-stmt
    # label-do-stmt      is [ do-construct-name : ] DO label [ loop-control ]
    # nonlabel-do-stmt   is [ do-construct-name : ] DO [ loop-control ]
    # loop-control       is [ , ] do-variable = scalar-int-expr,
    #                             scalar-int-expr  [ , scalar-int-expr ]
    #                    or [ , ] WHILE ( scalar-logical-expr )
    # do-variable        is scalar-int-variable
    # do-block           is block
    # end-do             is end-do-stmt or continue-stmt
    # end-do-stmt        is END DO [ do-construct-name ]
    # continue-stmt      is CONTINUE

    def ParseDo(self, tok, loc=None, sLabel=None, sName=None):
        tokNext  = self.GetNextToken()
        sDoLabel = None
        if tokNext[0]==Token.tok_NUMBER:
            sDoLabel = tokNext[1]
            tokNext = self.GetNextToken()
        sOptComma=None
        if tokNext[1]==',':
            sOptComma = tokNext[1]
            tokNext = self.GetNextToken()
            
        if tokNext[0]==Token.tok_SEPARATOR:
            do = ControlLessDo(sLabel, sName, loc, tok[1],
                               sDoLabel, self.nIndent)
            tok = tokNext
        elif string.upper(tokNext[1])=='WHILE':
            do = DoWhile(sLabel, sName, loc, tok[1], sDoLabel,
                         sOptComma, tokNext[1], self.GetNextToken()[1],
                         self.nIndent)
            tok, exp = self.ParseExpression(self.GetNextToken())
            assert tok[1]==')'
            do.SetExpression(exp, tok[1])
            tok = self.GetNextToken()
        else:
            do  = Do(sLabel, sName, loc, tok[1], sDoLabel, sOptComma,
                     self.nIndent)
            tok, var = self.ParsePrimary(tokNext)
            do.SetVariable(var, tok[1])
            assert tok[1]=="="
            tok, exp = self.ParseExpression(self.GetNextToken())
            do.SetFrom(exp, tok[1])
            assert tok[1]==","
            tokComma, exp = self.ParseExpression(self.GetNextToken())
            do.SetTo(exp)
            if tokComma[1]==",":
                tok, exp = self.ParseExpression(self.GetNextToken())
                do.SetStep(tokComma[1], exp)
            else:
                tok = tokComma

        assert tok[0]==Token.tok_SEPARATOR
        if sDoLabel:
            self.LabelStack.append(int(sDoLabel))
        else:
            self.LabelStack.append(-1)
        self.sub.AppendStatement(do)
        
        do.SetEndLocation(self.scanner.GetPreviousLocation())
        tok = self.GetNextToken()
        tok = self.ParseStatements(tok,
                                   dEnd={"END":  self.ParseEndDo,
                                         "ENDDO":self.ParseEndDo},
                                   nIndentModifier=1)
        # Return none, since the Do statement was already added (at the
        # beginning of this method). This is necessary to ensure that
        # the statements which are part of the do block are added
        # after the do statement!
        return tok, None
    # --------------------------------------------------------------------------
    # else-if-stmt is ELSE IF ( scalar-logical-expr ) THEN [ if-construct-name ]
    # else-stmt	   is ELSE [ if-construct-name ]
    def ParseElseOrElseIf(self, tok, loc=None, sLabel=None, sName=None):
        if string.upper(tok[1])=="ELSEIF":
            if isinstance(tok[1], AttributeString):
                sElse, sIf = tok[1].tSplitString(4)
            else:
                sElse = tok[1][0:4]
                sIf   = tok[1][4: ]
        else:
            sElse=tok[1]
            tokNext = self.GetNextToken()
            if string.upper(tokNext[1])=="IF":
                sIf = tokNext[1]
            else:
                self.scanner.UnGet(tokNext)
                sIf = None
        # Check if we are parsing an else if or an else:
        if sIf:
            obj = ElseIf(sLabel, loc, sElse, sIf, self.nIndent-1)
            tokParOpen = self.GetNextToken()
            assert tokParOpen[1]=="("
            tokParClose, expr = self.ParseExpression(self.GetNextToken())
            obj.AddExpr(tokParOpen[1], expr, tokParClose[1])
            assert tokParClose[1]==")"
            tok = self.GetNextToken()
            assert string.upper(tok[1])=="THEN"
            obj.SetThen(tok[1])
            
        else:
            obj = Else(sLabel, loc, sElse, self.nIndent-1)
        
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            obj.SetName(tok[1])                  # Name
            tok = self.GetNextToken()
        return self.GetNextToken(), obj
    # --------------------------------------------------------------------------
    # This method is called if an 'END' or an 'END...' is encountered
    # It will NOT parse a potential name following the end do, since
    # this function can not determine if a following label is actually
    # a do-construct-name or an variablename (at least not without
    # having information about the end of a statement, e.g. ';' or
    # newline).
    def ParseEndDo(self, keywordtoken, loc=None, sLabel=None, sName=None):
        sEnd, sDo = self.tKeywordSplit(keywordtoken, "ENDDO", 3)
        assert string.upper(sDo)=="DO"
        enddo = EndDo(sLabel, loc, sEnd=sEnd, sDo=sDo, nIndent=self.nIndent-1)
        tok = self.GetNextToken()

        if tok[0]!=Token.tok_SEPARATOR:
            enddo.SetName(tok[1])
            tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        del self.LabelStack[-1]
        return self.GetNextToken(), enddo
    # --------------------------------------------------------------------------
    # end-if-stmt is END IF [ if-construct-name ]
    def ParseEndOrEndif(self, tok, loc=None, sLabel=None, sName=None):
        sEnd, sIf = self.tKeywordSplit(tok, "ENDIF",3)
        assert string.upper(sIf)=="IF"
        endif = EndIf(sLabel, loc, sEnd=sEnd, sIf=sIf, nIndent=self.nIndent-1)
        tok   = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            endif.SetName(tok[1])                # Name
            tok = self.GetNextToken()
        return self.GetNextToken(), endif
        
    # --------------------------------------------------------------------------
    # end-subroutine-stmt is END [ SUBROUTINE [ subroutine-name ] ]
    # end-function-stmt	is END [ FUNCTION [ function-name ] ]
    # end-program-stmt	is END [ PROGRAM [ program-name ] ]
    def ParseEndProgUnit(self, keywordtoken=None, loc=None, sLabel=None, sName=None):
        es  = EndProgUnit(sLabel=sLabel, loc=loc, sEnd=keywordtoken[1],
                          nIndent=self.nIndent-1)
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            tokname = self.GetNextToken()
            if tokname[0]!=Token.tok_SEPARATOR:
                es.SetName(tok[1], tokname[1])
                tok = self.GetNextToken()
            else:
                es.SetName(tok[1])
                tok = tokname
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), es
    # --------------------------------------------------------------------------
    # exit-stmt is EXIT [ do-construct-name ]
    def ParseExit(self, tok, loc=None, sLabel=None, sName=None):
        tokLabel = self.GetNextToken()
        if tokLabel[0]==Token.tok_SEPARATOR:
            sExitLabel = None
        else:
            sExitLabel = tokLabel[1]
            tokLabel = self.GetNextToken()
        exit = Exit(sLabel, loc, tok[1], sExitLabel=sExitLabel,
                    nIndent=self.nIndent)
        assert tokLabel[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), exit
    # --------------------------------------------------------------------------
    # exit-stmt is EXIT [ do-construct-name ]
    def ParseCycle(self, tok, loc=None, sLabel=None, sName=None):
        tokLabel = self.GetNextToken()
        if tokLabel[0]==Token.tok_SEPARATOR:
            sCycleLabel = None
        else:
            sCycleLabel = tokLabel[1]
            tokLabel = self.GetNextToken()
        cycle = Cycle(sLabel, loc, tok[1], sCycleLabel=sCycleLabel,
                    nIndent=self.nIndent)
        assert tokLabel[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), cycle
    # --------------------------------------------------------------------------
    # Now, format is parsed rather crude: every token is read and appended
    # to the format (including the opening and closing parenthesis), till the
    # end of statement is reached. It is pretty hard to really parse a format
    # statement without changing the scanner signficantly, since different
    # tokens must be produced for the scanner, consider: 3(1X,/)  (where '/)'
    # has to be returned as a single token (looks like an array constructor).
    def ParseFormat(self, tok, loc=None, sLabel=None, sName=None):
        form = Format(sLabel, loc, tok[1], self.nIndent)
        tok = self.GetNextToken()
        # Tricky: a valid format is "format(//,2x)" - but the scanner
        # returns (/ as a single token. So we only assert that the first
        # charaters is a (
        assert tok[1][0]=="("
        while tok[0]!=Token.tok_SEPARATOR:
            form.append(tok[1])
            tok = self.GetNextToken()
        return self.GetNextToken(), form
    # --------------------------------------------------------------------------
    # computed-goto-stmt is GO TO ( label-list ) [ , ] scalar-int-expr

    def ParseGoto(self, tok, loc=None, sLabel=None, sName=None):
        sGo, sTo = self.tKeywordSplit(tok, "GOTO", 2)
        assert string.upper(sTo)=="TO"
        tok = self.GetNextToken()
        
        # Computed goto
        if tok[1]=="(":
            cgoto = ComputedGoto(sLabel, loc, sGo=sGo, sTo=sTo, sParOpen=tok[1])
            tok = self.GetNextToken()
            while tok[1]!=")":
                tokComma = self.GetNextToken()
                if tokComma[1]==",":
                    cgoto.AddLabel(tok[1], tokComma[1])
                    tok = self.GetNextToken()
                else:
                    cgoto.AddLabel(tok[1])
                    assert tokComma[1]==")"
                    tok = tokComma
            cgoto.SetParClose(tok[1])
            tok = self.GetNextToken()
            if tok[1]==",":
                cgoto.AddComma(tok[1])
                tok = self.GetNextToken()
            tok, obj = self.ParseExpression(tok)
            cgoto.SetExp(obj)
            return self.GetNextToken(), cgoto

        goto = Goto(sLabel, loc, sGo=sGo, sTo=sTo, sGotoLabel=tok[1],
                    nIndent=self.nIndent)
        tok  = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), goto
    # --------------------------------------------------------------------------
    def ParseStop(self, tok, loc=None, sLabel=None, sName=None):
        stop = Stop( sLabel, loc, sStop=tok[1], nIndent=self.nIndent)
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            tok, obj = self.ParsePrimary(tok)
            stop.SetStopCode(obj)
            assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(),stop
    # --------------------------------------------------------------------------
    def ParsePause(self, tok, loc=None, sLabel=None, sName=None):
        pause = Pause( sLabel, loc, sPause=tok[1], nIndent=self.nIndent)
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            tok, obj = self.ParsePrimary(tok)
            pause.SetStopCode(obj)
            assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(),pause
    # --------------------------------------------------------------------------
    # if-construct is if-then-stmt block [ else-if-stmt block ] ...
    #                 [ else-stmt block ] end-if-stmt
    # if-then-stmt is [ if-construct-name : ] IF ( scalar-logical-expr ) THEN
    # else-if-stmt is ELSE IF ( scalar-logical-expr ) THEN [ if-construct-name ]
    # else-stmt    is ELSE [ if-construct-name ]
    # end-if-stmt  is END IF [ if-construct-name ]
    # if-stmt is      IF ( scalar-logical-expr ) action-stmt
    def ParseIf(self, tokIf, loc=None, sLabel=None, sName=None):
        tokParOpen = self.GetNextToken()
        assert tokParOpen[1]=="("
        tokParClose, ifcond = self.ParseExpression(self.GetNextToken())
        assert tokParClose[1]==")"
        
        tok = self.GetNextToken()

        if tok[0]==Token.tok_NUMBER:
            arithIf = ArithmeticIf(sLabel, loc, tokIf[1], tokParOpen[1],
                                   ifcond, tokParClose[1], self.nIndent)
            while tok[0]!=Token.tok_SEPARATOR:
                tokNext = self.GetNextToken()
                if tokNext[1]==',':
                    arithIf.AppendLabel(tok[1], tokNext[1])
                    tok = self.GetNextToken()
                else:
                    arithIf.AppendLabel(tok[1])
                    tok = tokNext
            return self.GetNextToken(), arithIf
                    
        if string.upper(tok[1])!="THEN":                   # if-stmt
            tok, statement = self.ParseStatements(tok, bOnlyOneStatement=1,
                                                  nIndentModifier=1)
            ifonly = IfOnly(sLabel, loc, tokIf[1], tokParOpen[1], ifcond,
                            tokParClose[1], statement, self.nIndent)
            self.sub.AppendStatement(ifonly)
            ifonly.SetEndLocation(self.scanner.GetPreviousLocation())
            return tok, None
        ifobj = If(sLabel, sName, loc, tokIf[1], self.nIndent,
                   tokParOpen[1], ifcond, tokParClose[1], tok[1])
        self.sub.AppendStatement(ifobj)
        ifobj.SetEndLocation(self.scanner.GetPreviousLocation())
        # Now we are parsing an if-then(-else) statement
        # ==============================================
        tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        tok = self.GetNextToken()
        while 1:
            tok = self.ParseStatements(tok,
                                       dEnd = {"ELSE"  :self.ParseElseOrElseIf,
                                               "ELSEIF":self.ParseElseOrElseIf,
                                               "END"   :self.ParseEndOrEndif,
                                               "ENDIF" :self.ParseEndOrEndif},
                                       nIndentModifier=1)
            if self.sub[-1].__class__==EndIf: break
            if not tok:
                raise Error("Line %d, column %d: Problem with If statement" %
                            (self.scanner.GetLinenumber(),
                             self.scanner.GetColumnnumber()))
        # Return none, since the If statement was already added (at the
        # beginning of this method). This is necessary to ensure that
        # the statements which are part of the if (or else-if or then) block
        # are added after the do statement!
        return tok, None
                
    # --------------------------------------------------------------------------
    # Parses an expression list like "a, (b(i), i=1, 2)"
    def ParseIOExpressionList(self, obj, tok):
        while tok[0]!=Token.tok_SEPARATOR:
            tok, exp = self.ParseExpression(tok)
            if tok[1]==",":
                obj.AddIOExpression(exp, tok[1])
                tok = self.GetNextToken()
            else:
                obj.AddIOExpression(exp)
        return tok, obj
    # --------------------------------------------------------------------------
    # print-stmt is PRINT format [ , output-item-list ]
    # format is default-char-expr or label or *
    def ParsePrint(self, tok, loc=None, sLabel=None, sName=None):
        pr = Print(sLabel, loc, tok[1], self.nIndent)
        tok = self.GetNextToken()
        if tok[1]=="*":
            pr.SetFormat(tok[1])
            tok = self.GetNextToken()
        elif tok[0]==Token.tok_NUMBER:
            pr.SetFormat(int(tok[1]))
            tok = self.GetNextToken()
        else:
            tok, obj = self.ParseExpression(tok)
            pr.SetFormat(obj)
        if tok[1]!=",":
            assert tok[0]==Token.tok_SEPARATOR
            return self.GetNextToken(), pr
        pr.SetComma(tok[1])
        tok, pr = self.ParseIOExpressionList(pr, self.GetNextToken())
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), pr
    # --------------------------------------------------------------------------
    # Parses a statement with the format 'keyword ([a=]b,[c=]d)'
    def ParseBasicIOStatement(self, cl, tok, loc=None, sLabel=None, sName=None):
        rewind = cl(sLabel, loc, self.nIndent, tok[1])
        tok = self.GetNextToken()
        if tok[1]=='(':
            rewind.SetParOpen(tok[1])
            tok = self.ParseIOControlSpec(self.GetNextToken(), rewind)
            assert tok[1]==')'
            rewind.SetParClose(tok[1])
        else:
            rewind.AddUnitNumber(tok[1])
        return self.GetNextToken(), rewind
    # --------------------------------------------------------------------------
    # rewind-stmt REWIND file-unit-number or REWIND ( position-spec-list )
    # position-spec is [ UNIT = ] file-unit-number  or IOMSG = iomsg-variable
    #               or IOSTAT = scalar-int-variable or ERR = label
    def ParseRewind(self, tok, loc=None, sLabel=None, sName=None):
        tok, rew = self.ParseBasicIOStatement(Rewind, tok, loc, sLabel, sName)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), rew
    # --------------------------------------------------------------------------
    # backspace-stmt is BACKSPACE file-unit-number
    #                or BACKSPACE ( position-spec-list )
    def ParseBackspace(self, tok, loc=None, sLabel=None, sName=None):
        tok, back=self.ParseBasicIOStatement(Backspace, tok, loc, sLabel, sName)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), back
    # --------------------------------------------------------------------------
    # endfile-stmt is ENDFILE file-unit-number or ENDFILE ( position-spec-list )
    def ParseEndfile(self, tok, loc=None, sLabel=None, sName=None):
        tok, endfile=self.ParseBasicIOStatement(Endfile, tok, loc, sLabel, sName)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), endfile
    # --------------------------------------------------------------------------
    # open-stmt is OPEN ( connect-spec-list )
    def ParseOpen(self, tok, loc=None, sLabel=None, sName=None):
        # Check if open is a variable name - this test works only if the
        # variable is a scalar! (you can declare a variable 'open(20)', and
        # then use it as "open(20) = 1"  - arrrrgh!
        var     = self.sub.GetVariable(tok[1], bAutoAdd=0)
        tokNext = self.GetNextToken()
        if var:
            if tokNext[1]!='(':
                self.scanner.UnGet(tokNext)
                return self.ParseAssignment(tok, loc=loc, sLabel=sLabel,
                                            sName=sName)
        o   = Open(sLabel, loc, self.nIndent, tok[1], tokNext[1])
        tok = self.ParseIOControlSpec(self.GetNextToken(), o)
        assert tok[1]==')'
        o.SetParClose(tok[1])
        assert self.GetNextToken()[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), o
    # --------------------------------------------------------------------------
    # read-stmt is READ ( io-control-spec-list ) [ input-item-list ]
    #           or READ format [ , input-item-list ]
    def ParseRead(self, tok, loc=None, sLabel=None, sName=None):
        tokPar = self.GetNextToken()
        if tokPar[1]=='(':
            read  = Read(sLabel, loc, self.nIndent, tok[1],tokPar[1])
            tok   = self.GetNextToken()
            tok   = self.ParseIOControlSpec(tok, read)
            read.SetParClose(tok[1])
            tok=self.GetNextToken()
        else:
            read  = Read(sLabel, loc, self.nIndent, tok[1])
            tok = self.GetNextToken()
            if tok[1]==',':
                read.SetFormat(tokPar[1], tok[1])
            else:
                read.SetFormat(tokPar[1])
            tok=self.GetNextToken()
        # Test for 'empty' read statements, e.g. "read 10"
        if not tok: return self.GetNextToken(), read
        tok, read = self.ParseIOExpressionList(read, tok)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), read
    # --------------------------------------------------------------------------
    # inquire-stmt is INQUIRE ( inquire-spec-list )
    #                 INQUIRE ( IOLENGTH = scalar-int-variable ) output-item-list
    def ParseInquire(self, tok, loc=None, sLabel=None, sName=None):
        tok, inquire = self.ParseBasicIOStatement(Inquire, tok, loc, sLabel, sName)
        tok, inquire = self.ParseIOExpressionList(inquire, tok)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), inquire
    # --------------------------------------------------------------------------
    # write-stmt      is WRITE ( io-control-spec-list ) [ output-item-list ]
    # io-control-spec is [ UNIT = ] io-unit or [ FMT = ] format
    #                 or [ NML = ] namelist-group-name
    #                 or ADVANCE = scalar-default-char-expr    ...
    def ParseWrite(self, tok, loc=None, sLabel=None, sName=None):
        tok, write = self.ParseBasicIOStatement(Write, tok, loc, sLabel, sName)
        tok, write = self.ParseIOExpressionList(write, tok)
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), write
    # --------------------------------------------------------------------------
    def ParseIOControlSpec(self, tok, obj):
        while tok[1]!=')':
            tokNext = self.GetNextToken()
            if tokNext[1]=='=':
                tokComma, exp = self.ParseExpression(self.GetNextToken())
                exp = OptionString(tok[1], tokNext[1], exp)
            else:
                self.scanner.UnGet(tokNext)
                if tok[1]=='*':
                    exp=tok[1]
                    tokComma = self.GetNextToken()
                else:
                    tokComma, exp = self.ParseExpression(tok)
            if tokComma[1]==',':
                obj.AddIOOpt(exp, tokComma[1])
                tok = self.GetNextToken()
            else:
                obj.AddIOOpt(exp)
                tok = tokComma
        return tok
    # --------------------------------------------------------------------------
    # This method is called if a 'return' is found. sName is actually
    # not used, but potentially passed in as a parameter from ParseStatements.
    def ParseReturn(self, tok, loc=None, sLabel=None, sName=None):
        tokNext = self.GetNextToken()
        if tokNext[0]!=Token.tok_SEPARATOR:
            ret = Return(sLabel, loc, tok[1], self.nIndent)
            tok, obj = self.ParseExpression(tokNext)
            ret.SetReturnValue(obj)
        else:
            ret = Return(sLabel, loc, tok[1], self.nIndent)
            
        return self.GetNextToken(), ret
    # --------------------------------------------------------------------------
    # select-case-stmt is [ case-construct-name : ] SELECT CASE ( case-expr )
    # case-expr        is scalar-int-expr or scalar-char-expr or
    #                     scalar-logical-expr
    def ParseSelect(self, tokSelect, loc=None, sLabel=None, sName=None):
        sSelect, sCase   = self.tKeywordSplit(tokSelect, "SELECTCASE",6)
        tokParOpen       = self.GetNextToken()
        tokParClose, exp = self.ParseExpression(self.GetNextToken())
        select           = Select(sLabel, sName, loc, sSelect, sCase,
                                  tokParOpen[1], exp, tokParClose[1],
                                  self.nIndent)
        self.sub.AppendStatement(select)
        select.SetEndLocation(self.scanner.GetPreviousLocation())
        tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        tok = self.GetNextToken()
        # The indentation is increased by two, but each case statement will
        # be stored with current indentation-1, so the case statements will
        # be indented by 1, while each other statement within the case
        # statements will be indented by 2 (relative to the select statement),
        # and indented by 1 relative to each case statement.
        tok = self.ParseStatements(tok,
                                   dEnd={"END":      self.ParseEndSelect,
                                         "ENDSELECT":self.ParseEndSelect},
                                   nIndentModifier=2)
        # Return none, since the select statement was already added (at the
        # beginning of this method). This is necessary to ensure that
        # the statements which are part of the select block are added
        # after the select statement!
        return tok, None
    # --------------------------------------------------------------------------
    # case-stmt        is CASE case-selector [case-construct-name]
    # case-selector    is ( case-value-range-list ) or DEFAULT
    # case-value-range is case-value or case-value :  or
    #                     : case-value or case-value : case-value
    def ParseCase(self, tokCase, loc=None, sLabel=None, sName=None):
        tok  = self.GetNextToken()
        # ParseSelect increases the indentation by 2, so to get the
        # case statements on the right level, 1 is subtracted. This has
        # the advantage that each statement belonging to a case will be
        # indented correctly, and we don't have to deal with ending the
        # indentation level for case statements.
        case = Case(sLabel, loc, tokCase[1], self.nIndent-1)
        if tok[1]=='(':
            case.SetParOpen(tok[1])
            while 1:
                tok = self.GetNextToken()
                tokComma, obj = self.ParseSectionSubscript(tok)
                if tokComma[1]==',':
                    case.AddSelector(obj, tokComma[1])
                else:
                    case.AddSelector(obj)
                    assert tokComma[1]==')'
                    case.SetParClose(tokComma[1])
                    break
        else:                           # must be DEFAULT now
            case.AddSelector(sDefault=tok[1])
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            case.SetName(tok[1])
            tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), case
    # --------------------------------------------------------------------------
    # end-select-stmt  is END SELECT [ case-construct-name ]
    def ParseEndSelect(self, keywordtoken, loc=None, sLabel=None, sName=None):
        sEnd, sSelect = self.tKeywordSplit(keywordtoken,"ENDSELECT",3)
        endselect = EndSelect(sLabel, loc, sEnd, sSelect, self.nIndent-2)
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            endselect.SetName(tok[1])
            tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), endselect
    # --------------------------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------------------------
    # This function checks if a two word keyword (like END DO) is written
    # as one word. If so, the string will be split into two parts, n specifying
    # the number of characters for the first word. If the keyword is written
    # as two words, the next token (which must be the second part of the
    # keyword) will be read and returned as well.
    def tKeywordSplit(self, tok, sCombinedName, n):
        sKeyword = string.upper(tok[1])
        if sKeyword==sCombinedName:
            if isinstance(tok[1],AttributeString):
                s1, s2 = tok[1].tSplitString(n) # split combined keywords
                                                # and preserve attributes 
            else:
                s1 = tok[1][0:n]                # split combined keywords
                s2 = tok[1][n: ]                # (there are no attributes)
        else:
            s1 = tok[1]                         # already two separate tokens
            s2 = self.GetNextToken()[1]
        return s1, s2
    # --------------------------------------------------------------------------
    # Used by ParseAllocate and ParseDeallocate, since the parameters are
    # identical.
    def SubAllocateParam(self, tok, loc, sLabel, Obj, lKeys):
        tokParen = self.GetNextToken()
        assert tokParen[1]=="("
        allocate = Obj(sLabel, loc=loc, sOp=tok[1],
                       sParOpen=tokParen[1], nIndent=self.nIndent)
        tok = self.GetNextToken()

        # First loop: parse the variables to allocate
        while tok[1]!=")":
            sKey = string.upper(tok[1])
            if sKey in lKeys: break
            tok, obj = self.ParseExpression(tok)
            if tok[1]==',':
                allocate.AddVariable(obj, tok[1])
                tok=self.GetNextToken()
            else:
                allocate.AddVariable(obj)

        # Second loop: parse the alloc-opt-list
        while tok[1]!=")":
            sName=tok[1]
            tokEqual=self.GetNextToken()
            assert tokEqual[1]=="="
            tok, obj = self.ParsePrimary(self.GetNextToken())
            if tok[1]==',':
                allocate.AddOption(sName, tokEqual[1], obj, tok[1])
                tok=self.GetNextToken()
            else:
                allocate.AddOption(sName, tokEqual[1], obj)
                
        allocate.SetParClose(tok[1])
        tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), allocate

# ==============================================================================
if __name__=="__main__":
    from Test.ParseExecutionTest import RunAllTests
    RunAllTests()
