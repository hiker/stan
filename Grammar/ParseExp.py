#! /usr/bin/env python

# This is used by Parser

import string
from   Scanner.Token         import Token
from   AOR.Variable          import Variable
from   AOR.Expression        import ArrayConstructor, ArraySpecWithName,       \
                                    ComplexConst, DataRef, Expression, Literal,\
                                    LiteralKind, MultExpression,               \
                                    ParenthesisExpression, PowerExpression,    \
                                    UnaryExpression, SectionSubscript, String, \
                                    TrueFalse
from   AOR.IO                import IODoList
from   AOR.Statements        import FunctionCall
from   Tools.Error           import NotYetImplemented

# This class parses an expression.
# R305    constant        is      literal-constant or named-constant
# R603    designator      is      object-name or array-element or
#                                 array-section or structure-component or
#                                 substring
# R614    structure-component is  data-ref
# R613    part-ref        is      part-name [ ( section-subscript-list ) ]
# R615    type-param-inquiry is   designator % type-param-name
# R619    section-subscript is    subscript or subscript-triplet or
#                                 vector-subscript

class ParseExp:
    
    # --------------------------------------------------------------------------
    # expr              is  [ level-5-expr defined-binary-op ]* level-5-expr
    # defined-binary-op is . letter [ letter ] ...  .
    def ParseExpression(self, tok):
        (tok, obj) = self.Level5Expr(tok)
        # Test if no real expr exists - in this case simple return the
        # previous object (i.e. whatever is returned from Level5Expr, which
        # might be a level-4-expr, ...).
        if not tok or tok[0]!=Token.tok_OPERATOR:
            return (tok, obj)
        # Now we do have a real expr, i.e. with a defined binary op.
        # Create the Expression object to store this expression.
        ExpObj = Expression()

        # Add the object returned from Level5Expr and the operator
        ExpObj.append(obj, tok[1])
        tok = self.GetNextToken()
        # Now loop over all further expressions.
        while 1:
            (tok, obj) = self.Level5Expr(tok)
            if tok[0]!=Token.tok_OPERATOR:
                ExpObj.append(obj)
                return (tok, ExpObj)
            ExpObj.append(obj, tok[1])
    # --------------------------------------------------------------------------
    # level-5-expr is [ equiv-operand equiv-op ]* equiv-operand
    # equiv-op     is .EQV. or .NEQV.
    def ParseBasicExpression(self, tok, SubExpressionParser, lOps,
                             classExpression = Expression):
        (tok, obj) = SubExpressionParser(tok)
        if not tok:
            return (tok, obj)
        s = string.upper(tok[1])
        if not (s in lOps):
            return (tok, obj)
        ExpObj = classExpression()
        ExpObj.append(obj, tok[1])
        tok = self.GetNextToken()
        # Now loop over all further expressions.
        while 1:
            (tok, obj) = SubExpressionParser(tok)
            if not tok:
                ExpObj.append(obj)
                return (tok, ExpObj)
            s = string.upper(tok[1])
            if not (s in lOps):
                ExpObj.append(obj)
                return (tok, ExpObj)
            ExpObj.append(obj, tok[1])
            tok = self.GetNextToken()
    # --------------------------------------------------------------------------
    # level-5-expr is [ equiv-operand equiv-op ]* equiv-operand
    # equiv-op     is .EQV. or .NEQV.
    def Level5Expr(self, tok):
        return self.ParseBasicExpression(tok, self.EquivOperand,
                                         ['.EQV', '.NEQV.'])
    # --------------------------------------------------------------------------
    # equiv-operand is [ or-operand .OR. ]* or-operand
    def EquivOperand(self, tok):
        return self.ParseBasicExpression(tok, self.OrOperand, ['.OR.'])
    # --------------------------------------------------------------------------
    # or-operand is [ and-operand .AND. ]* and-operand
    def OrOperand(self, tok):
        return self.ParseBasicExpression(tok, self.AndOperand, ['.AND.'])
    # --------------------------------------------------------------------------
    # and-operand is [ .NOT. ] level-4-expr
    def AndOperand(self, tok):
        sNot = tok[1]
        s = string.upper(sNot)
        if s==".NOT.":
            (tok, obj) = self.Level4Expr(self.GetNextToken())
            return (tok, UnaryExpression(sNot, obj))
        return self.Level4Expr(tok)
    # --------------------------------------------------------------------------
    # level-4-expr is [ level-3-expr rel-op ] level-3-expr
    # rel-op       is .EQ. or .NE. or .LT. or .LE. or .GT. or .GE.
    #                      or ==   or /=   or < or <=  or > or >=
    def Level4Expr(self, tok):
        return self.ParseBasicExpression(tok, self.Level3Expr,
                                    ['.EQ.', '.NE.', '.LT.', '.LE.', '.GT.',
                                     '.GE.', '=='  , '/='  , '<'   , '<='  ,
                                     '>'   , '>='                           ])
    # --------------------------------------------------------------------------
    # level-3-expr is [ level-2-expr // ]* level-2-expr
    def Level3Expr(self, tok):
        return self.ParseBasicExpression(tok, self.Level2Expr, ['//'])
    # --------------------------------------------------------------------------
    # level-2-expr is [add-op] [ add-operand  add-op ]* add-operand
    # add-op       is + or -
    def Level2Expr(self, tok):
        return self.ParseBasicExpression(tok, self.AddOperand, ['+','-'])
    # --------------------------------------------------------------------------
    # add-operand is [ mult-operand mult-op ]* mult-operand
    # mult-op     is * or /
    def AddOperand(self, tok):
        return self.ParseBasicExpression(tok, self.MultOperand, ['*','/'],
                                         classExpression = MultExpression)
    # --------------------------------------------------------------------------
    # mult-operand is level-1-expr [ ** level-1-expr ]*
    # This is actually parsed and stored as
    # mult-operand is [level-1-expr **]* level-1-expr
    # The difference beeing that a**b**c is a**(b**c) in the original grammar,
    # while it is (a**b)**c here - which doesn't really matter for our purpose.
    def MultOperand(self, tok):
        return self.ParseBasicExpression(tok, self.Level1Expr, ['**'],
                                         classExpression = PowerExpression)
    # --------------------------------------------------------------------------
    # level-1-expr     is [ defined-unary-op ] primary
    # defined-unary-op is . letter [ letter ] ...  .
    def Level1Expr(self, tok):
        if tok[0]==Token.tok_OPERATOR:
            sOperator = tok[1]
            tok = self.GetNextToken()
            (tok2, obj) = self.ParsePrimary(tok)
            return (tok2, UnaryExpression(sOperator, obj))
        return self.ParsePrimary(tok)
    # --------------------------------------------------------------------------
    # primary is constant or designator or array-constructor or
    #            structure-constructor or function-reference or
    #            type-param-inquiry or type-param-name    or ( expr )
    # JH TODO primary is designator or array-constructor or
    #            structure-constructor or function-reference or
    #            type-param-inquiry or type-param-name    or ( expr )
    # JH TODO: designator is array-element or array-section or
    #           structure-component or substring
    # ParsePrimary is also used to parse the name of an procedure, which can
    # be data-ref % procedure-component-name. In this case, a '('
    # The parameter bNoFuncCall can be set to 1 if the current expression
    # should not be parsed as a function call. This can happen when parsing
    # a variable declaration, e.g. "real a(100)", since when parsing the
    # variable name 'a', a is not yet entered in the list of variables
    # as being an array, so it would be parsed as a function call instead
    # (see ParseSpecification for examples).
    def ParsePrimary(self, tok, bNoFuncCall=0):
        # Check for a number first
        if tok[0]==Token.tok_NUMBER:
            t = self.GetNextToken()
            # Handle kind constants
            if t[1]=="_":
                t = self.GetNextToken()
                return (self.GetNextToken(),LiteralKind(tok[1],t[1]))
            return (t,Literal(tok[1]))

        if tok[1]=="(":
            sParOpen=tok[1]
            tok = self.GetNextToken()
            tok, obj = self.ParseExpression(tok)
            # Check if this is a parenthesis expression or a complex number:
            if tok[1]==",":
                sComma=tok[1]
                # Now we can either have a complex constant (e.g. (1,2) ), or
                # an implied do loop (e.g. (i,i=1,2). Of course, an implied do
                # loop is not allowed as a 'normal' expression, but it is
                # more convenient to parse this here for all IO calls
                tok, obj2 = self.ParseExpression(self.GetNextToken())
                if tok[1]=="," or tok[1]=="=":
                    tok, obj = self.ParseIODoLoop(sParOpen, obj, sComma,
                                                  obj2, tok)
                else:
                    obj = ComplexConst(sParOpen, obj, sComma, obj2, tok[1] )
            else:
                # It is a parenthesis expression
                obj = ParenthesisExpression(sParOpen=sParOpen, obj=obj,
                                            sParClose=tok[1])
            assert tok[1]==")"
            return self.GetNextToken(), obj

        if tok[1]=="(/":
            return self.ParseArrayConstructor(tok)
            
        # Check for a constant like .true. or .false.
        if tok[0]==Token.tok_TRUEFALSE:
            return (self.GetNextToken(), TrueFalse(tok[1]) )

        # More missing here!!!???
        if tok[0]==Token.tok_QUOTE:
            return self.GetNextToken(), String(tok[1])
        elif tok[0]==Token.tok_QUOTE_START:
            s = String(tok[1])
            tok = self.GetNextToken()
            while tok[0]!=Token.tok_QUOTE_END:
                s.AddContString(tok[1])
                tok = self.GetNextToken()
            s.AddContString(tok[1])
            return self.GetNextToken(), s
        else:
            # Now we know it's a variable name or a function call
            tokNext = self.GetNextToken()
            if tokNext and tokNext[1]=="(":
                var = self.sub.GetVariable(tok[1], bAutoAdd=0)
                # Test for variable or function call: a function call
                # is parsed if the name is not defined, or it is defined
                # but not with a dimension (i.e. external f; integer f ...)
                if not (var and var.bIsArray() ) and not bNoFuncCall:
                    f = FunctionCall(tok[1])
                    self.sub.AddFunctionCall(tok[1], self.scanner.GetLocation())
                    tok = self.ParseProcedureArgs(f, tokNext)
                    return tok, f
                # If var is not defined (which can happen if e.g. a variable
                # is encountered first in a common block or equivalence
                # statement), add the variable so that var is defined.
                if not var:
                    var = self.sub.GetVariable(tok[1], bAutoAdd=1)
                    
                tok, var = self.ParseArrayExpression(var, tokNext[1])
                if not var.oGetVariable().bIsArray():
                    var.oGetVariable().SetAttribute('dimension',var.GetArraySpec())
            else:
                var = self.sub.GetVariable(tok[1])
                tok = tokNext
            if tok and tok[1]=="%":
                tok, var = self.ParseTypeRef(var, tok[1], self.GetNextToken())
                # Test for substring expressions, e.g. a(i)%b(i)(1:2)
                # Using ParseArrayExpression for substring is more than
                # an overkill, it is just very simple to do :)
            if tok and tok[1]=="(":
                tok,var = self.ParseArrayExpression(var, tok[1])
            return (tok, var)
        
    # --------------------------------------------------------------------------
    def ParseArrayConstructor(self, tok):
        ac = ArrayConstructor(tok[1])
        tok = self.GetNextToken()
        while tok[1]!="/)":
            tok, obj = self.ParseExpression(tok)
            if tok[1]==",":
                ac.append(obj, tok[1])
                tok = self.GetNextToken()
            else:
                ac.append(obj)
                ac.SetParClose(tok[1])
                return self.GetNextToken(), ac
    # --------------------------------------------------------------------------
    # data-ref is part-ref [ % part-ref ] ...
    # Token is already the next token of the second part-ref (i.e. the
    # characters following the % sign) - especially token itsels is not a
    # variable
    def ParseTypeRef(self, var, sPercent, tok):
        dr = DataRef(var, sPercent)
        while 1:
            lit = Literal(tok[1])
            tok=self.GetNextToken()
            if tok and tok[1]=="(":
                tok, lit = self.ParseArrayExpression(lit, tok[1])
            if not tok or tok[1]!="%":
                dr.append(lit)
                return (tok, dr)
            dr.append(lit, tok[1])
            tok=self.GetNextToken()
    # --------------------------------------------------------------------------
    # section-subscript is subscript or subscript-triplet or vector-subscript
    # subscript-triplet is [ subscript ] : [ subscript ] [ : stride ]
    # subscript         is scalar-int-expr
    # vector-subscript  is int-expr
    def ParseArrayExpression(self, var, sParOpen):
        ar  = ArraySpecWithName(var=var, sParOpen=sParOpen)
        tok = self.GetNextToken()
        while tok[1]!=")":
            tok, ss = self.ParseSectionSubscript(tok)
            if tok[1]==",":
                ar.AddSubscript(ss, tok[1])
                tok = self.GetNextToken()
            else:
                ar.AddSubscript(ss)
        ar.SetParClose(tok[1])
        return self.GetNextToken(), ar
    
    # --------------------------------------------------------------------------
    def ParseSectionSubscript(self, tok):
        if tok[1]!=":":
            tok, oLower = self.ParseExpression(tok)
        else:
            oLower = None
        sColon1 = tok[1]
        if sColon1!=":":
            return tok, SectionSubscript(oLower)
        else:
            tok = self.GetNextToken()
            # Now test if an upper boundary is given as well
            oUpper  = None
            sColon2 = None
            oStride = None
            if tok[1]!=")" and tok[1]!=",":
                if tok[1]!=":":
                    tok, oUpper = self.ParseExpression(tok)
                # Now test for stride
                if tok[1]==":":
                    sColon2 = tok[1]
                    tok, oStride = self.ParseExpression(self.GetNextToken())
            return tok, SectionSubscript(oLower, sColon1, oUpper,
                                         sColon2, oStride)
        
    # --------------------------------------------------------------------------
    # io-implied-do is ( io-implied-do-object-list , io-implied-do-control )
    # io-implied-do-object is input-item or output-item
    # output-item is expr or io-implied-do
    # input-item is variable or io-implied-do
    # io-implied-do-control is do-variable = scalar-int-expr, scalar-int-expr
    #                          [ , scalar-int-expr ]
    # obj1 is the first expression, obj2 the second expression. The scanner
    # has already read the ',' or the '=' [from (i, i=1,2) or (i,j,i=1,2)].
    # The returned token must be the closing parenthesis!!
    def ParseIODoLoop(self, sParOpen, obj1, sComma1, obj2, tok):
        iol = IODoList(sParOpen, obj1, sComma1)
        obj = obj2
        while tok and tok[1]!="=":
            iol.AddExpr(obj, tok[1])
            tok, obj = self.ParseExpression(self.GetNextToken())
        iol.SetVar(obj, tok[1])
        tok, obj = self.ParseExpression(self.GetNextToken())
        iol.SetFrom(obj, tok[1])
        assert tok[1]==","
        tokComma, obj = self.ParseExpression(self.GetNextToken())
        iol.SetTo(obj)
        if tokComma[1]==",":
            tok, obj = self.ParseExpression(self.GetNextToken())
            iol.SetStep(tokComma[1], obj)
            iol.SetParClose(tok[1])
            return tok, iol
        else:
            iol.SetParClose(tokComma[1])
            return tokComma, iol
    # --------------------------------------------------------------------------
    
# ==============================================================================
if __name__=="__main__":
    from Test.ParseExpTest import RunAllTests
    RunAllTests()
