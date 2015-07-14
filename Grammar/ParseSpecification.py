#! /usr/bin/env python

# This is used by Parser

import string
from   Scanner.Token         import Token
from   AOR.Variable          import Variable
from   AOR.AttributeString   import AttributeString
from   AOR.Expression        import BasicExpression, OneArraySpec, \
                                    ArraySpecWithName
from   AOR.Declaration       import Common, CrayPointer, CrayPointerTuple, \
                                    Data, DataStatementSet, DataValueList, \
                                    Declaration, Dimension, Equivalence, \
                                    EquivalenceItem, External, Implicit, \
                                    Intrinsic, Intent, Namelist,\
                                    ModuleProcedure, Parameter, Pointer, \
                                    Private, Public, Save, \
                                    Type, Use, UserType, VariableWithInit, \
                                    VariableWithLen
from   AOR.Subroutine        import SubroutineStatement
from   AOR.Interface         import InterfaceStatement, EndInterfaceStatement
from   AOR.ProgUnit          import ProgUnit
from   AOR.ProgUnit          import EndProgUnit
from   Tools.Error           import NotYetImplemented, Warning

# Parse: R204 specification-part is [ use-stmt ] ...
#                                   [ import-stmt ] ...
#                                   [ implicit-part ] ...
#                                   [ declaration-construct ] ...
class ParseSpecification:

    def __init__(self):
        pass
    # --------------------------------------------------------------------------
    # common-stmt is COMMON [ / [ common-block-name ] / ] common-block-object-list
    #            [ [ , ] / [ common-block-name ] /common-block-object-list ] ...
    # common-block-object is variable-name [ ( explicit-shape-spec-list ) ]
    #                     or proc-pointer-name
    def ParseCommon(self, tokCommon, loc, sLabel=None, sName=None):
        if tokCommon[1].upper()=="GLOBAL":
            tok  = self.GetNextToken()
            com  = Common(loc, tok[1], self.nIndent, sGlobal=tokCommon[1])
        else:
            com  = Common(loc, tokCommon[1], self.nIndent)
        tok      = self.GetNextToken()
        tokComma = (None, None)
        while tok[0]!=Token.tok_SEPARATOR:
            # First: parse the common block name 
            if tok[1]=="//":           # unnamed common block
                com.AddCommonBlockName(sComma = tokComma[1], sSlash1=tok[1])
                tok = self.GetNextToken()
            elif tok[1]=="/":
                tok2 = self.GetNextToken()
                tok3 = self.GetNextToken()
                com.AddCommonBlockName(sComma = tokComma[1], sSlash1=tok[1],
                                       sName=tok2[1], sSlash2=tok3[1]       )
                tok = self.GetNextToken()
            else:
                # Empy common block, without //
                com.AddCommonBlockName()

            #Now read the object list
            while tok[0]!=Token.tok_SEPARATOR and tok[1]!="/" and tok[1]!="//":
                tok, exp = self.ParsePrimary(tok, bNoFuncCall=1)
                var = exp.oGetVariable()
                var.SetAttribute('common',com)
                if self.scanner.bIsIncludeFile():
                    var.SetAttribute('include',
                                     self.scanner.sGetIncludeFilename())
                if not tok or tok[0]==Token.tok_SEPARATOR:
                    com.AddCommonObject(exp)
                    return  self.GetNextToken(), com
                
                # *sigh* This bloody [,] - it means we have to use a lookahead
                # here to figure out if after a ',' another common-block-object
                # follows or if a new common block starts :( In the latter case
                # the comma must be added in front of the common block and 
                if tok[1]==",":
                    tok2 = self.GetNextToken()
                    if tok2[1]=="/" or tok2[1]=="//":
                        com.AddCommonObject(exp)
                        tokComma = tok
                        tok      = tok2
                        break
                    com.AddCommonObject(exp, tok[1])
                    tok = tok2
                else:
                    com.AddCommonObject(exp)
                    
        return self.GetNextToken(), com
    
    # --------------------------------------------------------------------------
    # namelist-stmt is NAMELIST  / namelist-group-name / namelist-group-object-list
    #                    [ [ , ] / namelist-group-name / namelist-group-object-list ] .,,
    # namelist-group-object	is	variable-name
    def ParseNamelist(self, tokCommon, loc, sLabel=None, sName=None):
        namelist  = Namelist(loc, tokCommon[1], self.nIndent)
        tok      = self.GetNextToken()
        tokComma = (None, None)
        while tok[0]!=Token.tok_SEPARATOR:
            # First: parse the name
            assert tok[1]=="/"
            tok2 = self.GetNextToken()
            tok3 = self.GetNextToken()
            assert tok3[1]=="/"
            namelist.AddNamelistName(sComma = tokComma[1], sSlash1=tok[1],
                                     sName=tok2[1], sSlash2=tok3[1]       )
            tok = self.GetNextToken()

            #Now read the object list
            while tok[0]!=Token.tok_SEPARATOR and tok[1]!="/" and tok[1]!="//":
                tok, exp = self.ParsePrimary(tok, bNoFuncCall=1)
                var = exp.oGetVariable()
                var.SetAttribute('namelist',namelist)
                if self.scanner.bIsIncludeFile():
                    var.SetAttribute('include',
                                     self.scanner.sGetIncludeFilename())
                if not tok or tok[0]==Token.tok_SEPARATOR:
                    namelist.AddNamelistObject(exp)
                    return  self.GetNextToken(), namelist
                
                # *sigh* This bloody [,] - it means we have to use a lookahead
                # here to figure out if after a ',' another common-block-object
                # follows or if a new common block starts :( In the latter case
                # the comma must be added in front of the common block and 
                if tok[1]==",":
                    tok2 = self.GetNextToken()
                    if tok2[1]=="/" or tok2[1]=="//":
                        namelist.AddNamelistObject(exp)
                        tokComma = tok
                        tok      = tok2
                        break
                    namelist.AddNamelistObject(exp, tok[1])
                    tok = tok2
                else:
                    namelist.AddNamelistObject(exp)
                    
        return self.GetNextToken(), namelist
    
    # --------------------------------------------------------------------------
    # data-stmt-object	is variable or data-implied-do
    def ParseDataStatementObjectList(self, tok, sLabel=None, sName=None):
        if tok[1]==',':
            datastatement = DataStatementSet(sComma=tok[1])
            tok = self.GetNextToken()
        else:
            datastatement = DataStatementSet()
        while tok[1]!='/':
            if tok[1]=='(':
                # ParsePrimary will parse either a variable or an implied do
                # loop (which of course not an expression, but it is very
                # convenient to do so)
                tok, obj = self.ParsePrimary(tok)
            else:
                # We can not use ParseExpression here, since a data statement
                # might be 'data a/1/', so ParseExpression would try to parse
                # a / expression.
                tok, obj = self.ParsePrimary(tok)
                
            if tok[1]==',':
                datastatement.AddObject(obj, tok[1])
                tok = self.GetNextToken()
            else:
                datastatement.AddObject(obj)
                return tok, datastatement
    # --------------------------------------------------------------------------
    # Parses a list of [ data-stmt-repeat * ] data-stmt-constant
    def ParseDataValueList(self, tokSlash):
        dvl = DataValueList(tokSlash[1])
        tok = self.GetNextToken()
        while tok[1]!='/':
            # Level1 expressions allow a unary -, so 'data x/-5/' will be
            # accepted, which wouldn't be accepted if ParseExpression is used.
            tok, obj = self.Level1Expr(tok)
            if tok[1]=='*':
                repeat = BasicExpression()
                repeat.append(obj, sOperator=tok[1])
                tok, obj = self.Level1Expr(self.GetNextToken())
                repeat.append(obj)
                obj = repeat
            if tok[1]==',':
                dvl.AddValue(obj, tok[1])
                tok = self.GetNextToken()
            else:
                dvl.AddValue(obj)
                dvl.AddSlash(tok[1])
                return self.GetNextToken(), dvl
    # --------------------------------------------------------------------------
    # data-stmt         is DATA data-stmt-set [ [ , ] data-stmt-set ] ...
    # data-stmt-set     is data-stmt-object-list / data-stmt-value-list /
    # data-stmt-object	is variable or data-implied-do
    # data-implied-do   is ( data-i-do-object-list , data-i-do-variable =
    #                      scalar-int-expr , scalar-int-expr
    #                      [ , scalar-int-expr ] )
    # data-i-do-object	is array-element or scalar-structure-component or
    #                      data-implied-do
    # data-stmt-value	is [ data-stmt-repeat * ] data-stmt-constant
    # data-stmt-repeat	is scalar-int-constant or scalar-int-constant-subobject
    def ParseData(self, tok, loc, sLabel=None, sName=None):
        data = Data(loc, tok[1], self.nIndent)
        tok = self.GetNextToken()
        while tok[0]!=Token.tok_SEPARATOR:
            tok, datastatement = self.ParseDataStatementObjectList(tok)
            assert tok[1]=='/'
            tok,dvl = self.ParseDataValueList(tok)
            datastatement.AddValueList(dvl)
            data.AddDataStatement(datastatement)

        return self.GetNextToken(), data
            
    # --------------------------------------------------------------------------
    #DIMENSION [ :: ] array-name (array-spec) [,array-name (array-spec) ] ...
    def ParseDimension(self, tok, loc, sLabel=None, sName=None):
        dim   = Dimension(loc, tok[1], self.nIndent)
        tok   = self.GetNextToken()
        if tok[1]==":":
            dim.AddDoubleColons(tok[1], self.GetNextToken()[1])
            tok = self.GetNextToken()

        while 1:
            var          = self.sub.GetVariable(tok[1])
            tok, arrspec = self.ParseArraySpec(tok=self.GetNextToken(),var=var)
            var.SetAttribute('dimension', arrspec.GetArraySpec())
            if tok and tok[1]==",":
                dim.AddArraySpec(arrspec, tok[1])
            else:
                dim.AddArraySpec(arrspec)
                break
            tok   = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), dim
    # --------------------------------------------------------------------------
    # equivalence-stmt is EQUIVALENCE equivalence-set-list
    # equivalence-set is ( equivalence-object , equivalence-object-list )
    # equivalence-object is variable-name or array-element or substring
    def ParseEquivalence(self, tokEq, loc, sLabel=None, sName=None):
        eq         = Equivalence(loc, tokEq[1], self.nIndent)
        tok        = self.GetNextToken()
        while tok[1]=='(':
            eqitem = EquivalenceItem(tok[1])
            tok = self.GetNextToken()
            while tok[1]!=')':
                tokComma, obj = self.ParsePrimary(tok)
                if tokComma[1]==',':
                    eqitem.AddObject(obj, tokComma[1])
                    tok = self.GetNextToken()
                else:
                    eqitem.AddObject(obj)
                    assert tokComma[1]==')'
                    eqitem.SetParClose(tokComma[1])
                    tok=self.GetNextToken()
                    break
            # Originally this was:
            #for i in eqitem.GetAllUsedVariables():
            # but this would fail if GetAllUsedVariables returned
            # common blocks (because one of the used variables was=
            # part of a common block).
            for i in eqitem.GetAllEquivalentVariables():
                i.SetAttribute('equivalence',eqitem)
            if tok[1]==',':
                eq.AddObject(eqitem, tok[1])
                tok = self.GetNextToken()
            else:
                eq.AddObject(eqitem)
                assert tok[0]==Token.tok_SEPARATOR
                return self.GetNextToken(), eq
    # --------------------------------------------------------------------------
    def ParseExternal(self, tok, loc, sLabel=None, sName=None):
        ext = External(loc, tok[1], self.nIndent)
        tok = self.GetNextToken()
        if tok[1]==':':
            ext.AddDoubleColon(tok[1], self.GetNextToken()[1])
            tok = self.GetNextToken()
        while tok[0]!=Token.tok_SEPARATOR:
            tokComma = self.GetNextToken()
            if tokComma[1]==',':
                ext.AddExternal(tok[1], tokComma[1])
                tok = self.GetNextToken()
            else:
                ext.AddExternal(tok[1])
                tok = tokComma
        return self.GetNextToken(), ext
    # --------------------------------------------------------------------------
    # implicit-stmt is IMPLICIT implicit-spec-list or IMPLICIT NONE
    # implicit-spec is declaration-type-spec ( letter-spec-list )
    # letter-spec   is letter [ - letter ]
    def ParseImplicit(self, tokImplicit, loc, sLabel=None, sName=None):
        tok = self.GetNextToken()
        if tok[1]=="=" or tok[1]=="(":
            self.scanner.UnGet(tok)
            return self.ParseAssignment(tokImplicit, loc=loc, sLabel=sLabel,
                                        sName=sName)
        impl = Implicit(tokImplicit[1], loc=loc, nIndent=self.nIndent)
        if string.upper(tok[1])=="NONE":
            impl.SetImplicitNone(tok[1])
            tok = self.GetNextToken()
        else:
            tokParOpen, type = self.ParseBasicType(tok)
            assert tokParOpen[1]=="("
            # The big problem here: "implicit(a-b)(d-e)". a-b is a kind
            # information, while d-e is the actual implicit statement :(((
            # Do distinguish these two cases, we need a rather large lookahead:
            # So we read all tokens and store them in a list, till we find the
            # closing first parenthesis. If another parenthesis is following,
            # we unget whatever we stored in the list and parse it again as
            # kind information. Otherwise we use the information in the list
            # to get the implicit information
            # At the beginning of the part marked
            # "Parse the actual implicit information"
            # tokParOpen must be the opening parenthesis, and l must contain
            # all tokens till the closing parenthesis. tok must be the
            # tok_SEPARATOR token.

            nOpen=1                     # Count the number of opened parenthesis
            l=[]
            tok = self.GetNextToken()
            while tok[0]!=Token.tok_SEPARATOR:
                l.append(tok)
                if tok[1]=="(":
                    nOpen=nOpen+1
                elif tok[1]==")":
                    nOpen=nOpen-1
                    if nOpen==0: break
                tok = self.GetNextToken()
            tok = self.GetNextToken()
            if tok[1]=="(":
                # Worst case: whatever we have read up to now, was actually
                # kind information. So unget everything, and parse the kind
                # information correctly.
                self.scanner.UnGet(tok)
                for i in range(len(l)-1, -1, -1):
                    self.scanner.UnGet(l[i])
                # Now, tokParOpen is the opening parenthesis, read above
                tokParOpen, type = self.ParseKindCharSelector(tokParOpen, type)
                assert tokParOpen[1]=="("
                # Now read everything till the end of the statement, and store
                # it in the list l. So we have the same state when leaving
                # the if statement: l contains all tokens excluding the
                # separator (and the opening parenthesis). 
                tok = self.GetNextToken()
                l=[]
                while tok[0]!=Token.tok_SEPARATOR:
                    l.append(tok)
                    tok=self.GetNextToken()
            impl.SetType(type)
            
            # Parse the actual implicit information
            # -------------------------------------
            impl.SetParOpen(tokParOpen[1])
            i = 0                            # index in list of tokens
            while l[i][1]!=")":
                if l[i+1][1]=="-":
                    if l[i+3][1]==",":
                        impl.AddLetter(l[i][1],l[i+1][1],l[i+2][1],
                                       sComma=l[i+3][1])
                        self.sub.SetImplicit(type, l[i][1],l[i+2][1])
                        i=i+4
                    else:
                        impl.AddLetter(l[i][1],l[i+1][1],l[i+2][1])
                        self.sub.SetImplicit(type, l[i][1],l[i+2][1])
                        i=i+3
                else:
                    if l[i+1][1]==",":
                        impl.AddLetter(l[i][1], sComma=l[i+1][1])
                        self.sub.SetImplicit(type, l[i][1])
                        i=i+2
                    else:
                        impl.AddLetter(l[i][1])
                        self.sub.SetImplicit(type, l[i][1])
                        i=i+1
            impl.SetParClose(l[i][1])

        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), impl
    # --------------------------------------------------------------------------
    # interface-stmt is INTERFACE [ generic-spec ] or ABSTRACT INTERFACE
    # generic-spec   is generic-name or	OPERATOR ( defined-operator ) or
    # interface-body is function-stmt [ specification-part ] end-function-stmt
    #                or subroutine-stmt [ specification-part ]
    #                   end-subroutine-stmt
    # procedure-stmt is [ MODULE ] PROCEDURE procedure-name-list
    #                   ASSIGNMENT ( = ) or dtio-generic-spec
    #dtio-generic-spec is READ (FORMATTED) or READ (UNFORMATTED) or
    #                  WRITE (FORMATTED) or WRITE (UNFORMATTED)
    def ParseInterface(self, tok, loc, sLabel=None, sName=None):
        iface = InterfaceStatement(loc, sInterface=tok[1])
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            if string.upper(tok[1])=="OPERATOR":
                while tok[0]!=Token.tok_SEPARATOR:
                    iface.AddGenericSpec(tok[1])
                    tok = self.GetNextToken()
            else:
                iface.AddGenericSpec(tok[1])
                tok = self.GetNextToken()

        assert tok[0]==Token.tok_SEPARATOR

        self.sub.AppendStatement(iface)
        iface.SetEndLocation(self.scanner.GetPreviousLocation())
        tok = self.GetNextToken()
        # If we simple parse the interface. all variables in the interface will
        # be added to the current subroutine, which is wrong. Setting a flag to
        # indicate 'a interface is being parse; don't add any variables to the
        # current program unit' is somewhat complicated: quite a few places need
        # to be changed, and even more because no 'variable' object can easily
        # be returned. So instead a dummy program unit is created which stores
        # the information about variable (which could be used later for
        # something?) and replaces the actual program unit.
        # Unfortunately, this means that all lines of the interface will be
        # added to this dummy program unit instead of the actual program unit.
        # So all lines of the dummy have to be added to the program unit after
        # parsing the interface.
        savesub  = self.sub
        self.sub = ProgUnit()
        tok = self.ParseStatements(tok, dEnd={'END': self.ParseEndInterface,
                                              'ENDINTERFACE':
                                              self.ParseEndInterface},
                                   nIndentModifier=1)
        # Now move all lines from the dummy program unit to the actual
        # program unit:
        for i in self.sub:
            savesub.AppendStatement(i)
        self.sub = savesub
        
        # Return none, since the interface statement was already added (at the
        # beginning of this method). This is necessary to ensure that the
        # statements which are part of the select block are added after the
        # select statement!
        return tok, None

    # --------------------------------------------------------------------------
    # end-interface-stmt is END INTERFACE [ generic-spec ]
    def ParseEndInterface(self, tok, loc, sLabel=None, sName=None):
        sEnd, sInterface = self.tKeywordSplit(tok,"ENDSELECT",3)
        endInterface = EndInterfaceStatement(loc, sEnd, sInterface,
                                             self.nIndent-1)
        tok = self.GetNextToken()
        if tok[0]!=Token.tok_SEPARATOR:
            endInterface.SetName(tok[1])
            tok = self.GetNextToken()
        assert tok[0]==Token.tok_SEPARATOR
        return self.GetNextToken(), endInterface
    # --------------------------------------------------------------------------
    # intrinsic-stmt is INTRINSIC [ :: ] intrinsic-procedure-name-list
    def ParseIntrinsic(self, tok, loc, sLabel=None, sName=None):
        intri = Intrinsic(loc, tok[1], self.nIndent)
        tok = self.GetNextToken()
        if tok[1]==":":
            intri.AddDoubleColons(tok[1], self.GetNextToken()[1])
            tok = self.GetNextToken()
        while tok[0]!=Token.tok_SEPARATOR:
            tokComma = self.GetNextToken()
            if tokComma[1]==",":
                intri.AddIntrinsic(tok[1], tokComma[1])
                tok = self.GetNextToken()
            else:
                intri.AddIntrinsic(tok[1])
                tok = tokComma
        return self.GetNextToken(), intri
    # --------------------------------------------------------------------------
    # procedure-stmt is [ MODULE ] PROCEDURE procedure-name-list
    def ParseModuleProcedure(self, tok, loc, sLabel=None, sName=None):
        if string.upper(tok[1])=="MODULE":
            proc = ModuleProcedure(loc, tok[1], self.GetNextToken()[1],
                                   self.nIndent)
        else:
            proc = ModuleProcedure(loc, sModule=None, sProcedure=tok[1],
                                   nIndent=self.nIndent)
        tok = self.GetNextToken()
        while tok[0]!=Token.tok_SEPARATOR:
            tokComma = self.GetNextToken()
            if tokComma[1]==',':
                proc.AddProcedure(tok[1], tokComma[1])
                tok = self.GetNextToken()
            else:
                proc.AddProcedure(tok[1])
                tok = tokComma
        return self.GetNextToken(), proc
    # --------------------------------------------------------------------------
    # parameter-stmt     is PARAMETER ( named-constant-def-list )
    # named-constant-def is named-constant = initialization-expr
    def ParseParameter(self, tokParam, loc, sLabel=None, sName=None):
        tok = self.GetNextToken()
        assert tok[1]=="("
        para = Parameter(loc, tokParam[1], self.nIndent, tok[1])
        while 1:
            var      = self.sub.GetVariable(self.GetNextToken()[1])
            tokEqual = self.GetNextToken()
            assert tokEqual[1]=="="
            tok      = self.GetNextToken()
            tok, obj = self.ParseExpression(tok)
            if tok[1]==",":
                para.AddVarValue(var=var, sEqual=tokEqual[1], obj=obj,
                                 sComma=tok[1] )
            else:
                para.AddVarValue(var=var, sEqual=tokEqual[1], obj=obj )
            if tok[1]==")":
                para.SetParClose(tok[1])
                tok = self.GetNextToken()
                assert tok[0]==Token.tok_SEPARATOR
                return self.GetNextToken(), para

    # --------------------------------------------------------------------------
    # Two formats are possible: The F90 pointer:
    # pointer-stmt is POINTER [ :: ] pointer-decl-list
    # pointer-decl is object-name [ ( deferred-shape-spec-list ) ] or
    #                 proc-entity-name
    # Format 2 (provided for backward compatibility): Cray Pointers
    # POINTER (pointer-variable, data-variable-declaration)
    #        [(pointer-variable, data-variable-declaration)]...
    def ParsePointer(self, tokPointer, loc, sLabel=None, sName=None):
        tokParen = self.GetNextToken()
        # Test for Cray Pointers
        if tokParen[1]=='(':
            pointer = CrayPointer(loc, tokPointer[1], self.nIndent)
            while 1:
                tokComma, var = self.ParsePrimary(self.GetNextToken())
                assert tokComma[1]==','
                tokParClose, data = self.ParsePrimary(self.GetNextToken())
                assert tokParClose[1]==')'
                pTuple = CrayPointerTuple(tokParen[1], var, tokComma[1],
                                          data, tokParClose[1])
                tok = self.GetNextToken()
                if tok[1]==",":
                    pointer.AddPointer(pTuple, tok[1])
                    tokParen = self.GetNextToken()
                else:
                    pointer.AddPointer(pTuple)
                    assert tok[0]==Token.tok_SEPARATOR
                    return self.GetNextToken(), pointer
                
        else:
            pointer = Pointer(loc, tokPointer[1], self.nIndent)
            if tokParen[1]==':':
                pointer.AddDoubleColons(tokParen[1], self.GetNextToken()[1])
                tokParen = self.GetNextToken()
            while 1:
                tok, exp = self.ParsePrimary(tokParen)
                if tok[1]==',':
                    pointer.AddPointer(exp, tok[1])
                    tokParen = self.GetNextToken()
                else:
                    pointer.AddPointer(exp)
                    assert tok[0]==Token.tok_SEPARATOR
                    return self.GetNextToken(), pointer
            
    # --------------------------------------------------------------------------
    def ParsePublicPrivate(self, tokKeyword, loc, sLabel=None, sName=None):
        sKeyword = string.upper(tokKeyword[1])
        tok  = self.GetNextToken()
        if sKeyword=="PRIVATE":
            obj = Private(loc, tokKeyword[1], self.nIndent)
        else:
            obj = Public(loc, tokKeyword[1], self.nIndent)
            
        if tok[1]==":":
            obj.AddDoubleColons(tok[1], self.GetNextToken()[1])
            tok  = self.GetNextToken()
        while tok[0]!=Token.tok_SEPARATOR:
            tokComma  = self.GetNextToken()
            if sKeyword=="PUBLIC":
                self.sub.GetVariable(tok[1], d={sKeyword:1}, bAutoAdd=1)
            if tokComma[1]==",":
                obj.AddObject(tok[1], sComma=tokComma[1])
                tok  = self.GetNextToken()
            else:
                obj.AddObject(tok[1])
                tok = tokComma
        return self.GetNextToken(), obj
                
    # --------------------------------------------------------------------------
    # save-stmt is SAVE [ [ :: ] saved-entity-list ]
    # saved-entity is object-name or proc-pointer-name or / common-block-name /
    def ParseSave(self, tokSave, loc, sLabel=None, sName=None):
        tok  = self.GetNextToken()
        save = Save(loc, tokSave[1], self.nIndent)
        if tok[1]==":":
            save.AddDoubleColons(tok[1], self.GetNextToken()[1])
            tok  = self.GetNextToken()
        while tok[0]!=Token.tok_SEPARATOR:
            if tok[1]=="/":
                tok2      = self.GetNextToken()
                tok3      = self.GetNextToken()
                tokComma  = self.GetNextToken()
                if tokComma[1]==",":
                    save.AddCommonBlock(tok[1], tok2[1], tok3[1],
                                        sComma=tokComma[1])
                    tok  = self.GetNextToken()
                else:
                    save.AddCommonBlock(tok[1], tok2[1], tok3[1])
                    tok = tokComma
            else:
                tokComma  = self.GetNextToken()
                var = self.sub.GetVariable(tok[1], {"save":1}, bAutoAdd=1)
                if tokComma[1]==",":
                    save.AddObject(var, sComma=tokComma[1])
                    tok  = self.GetNextToken()
                else:
                    save.AddObject(var)
                    tok = tokComma
        return self.GetNextToken(), save
                
    # --------------------------------------------------------------------------
    def ParseSubroutineStatement(self, tok, loc, sLabel=None, sName=None):
        tokName = self.GetNextToken()
        subStatement = SubroutineStatement(loc=loc, lPrefix=[],
                                           sSub=tok[1],
                                           sName=tokName[1],
                                           nIndent=self.nIndent)

        tok = self.ParseArguments(self.GetNextToken(), subStatement)
        if tok[1]==",":
            # Following now: BIND ( C [ , NAME = scalar-char-initialization-expr ] )
            raise Error("language-binding-spec currently not supported")

        assert tok[0]==Token.tok_SEPARATOR
        self.sub.AppendStatement(subStatement)
        subStatement.SetEndLocation(self.scanner.GetPreviousLocation())
        # parseEndProgUnit is defined in ParseExecution
        tok = self.ParseStatements(self.GetNextToken(),
                                   dEnd = {'ENDSUBROUTINE' :
                                           self.SpeciParseEndProgUnit,
                                           'END': self.SpeciParseEndProgUnit},
                                   nIndentModifier=1)
        return tok, None
    # --------------------------------------------------------------------------
    # A simple wrapper for ParseEndprogUnit, which is necessary because the
    # parameters for all functions when parsing the specification part are
    # different from the parameters needed in the execution part.
    def SpeciParseEndProgUnit(self, tok, loc, sLabel=None, sName=None):
        return self.ParseEndProgUnit(sLabel=None, keywordtoken=tok, sName=None,
                                     loc=loc)
    # --------------------------------------------------------------------------
    # This method sets all attributes contained in the declaration DECL
    # to the variable VAR, e.g.:  integer, dimension(20) :: a
    # would set the 'dimension' attribute in the variable a
    def SetAllAttributes(self, var, decl):
        for i in decl.GetAttributes():
            if i.__class__ == ArraySpecWithName:
                var.SetAttribute('dimension', i.GetArraySpec())
            elif i.__class__ == Intent:
                var.SetAttribute('intent', i)
            # We have to handle more special attributes for sure!!!
            elif i.__class__ == str or i.__class__ == AttributeString:
                var.SetAttribute(i.lower())
            else:
                i.__class__
                var.SetAttribute(i)
            
    # --------------------------------------------------------------------------
    # type-declaration-stmt is declaration-type-spec [ [ , attr-spec ] ... :: ]
    #                          entity-decl-list
    # entity-decl is object-name [(array-spec)] [*char-length] [initialization]
    def ParseTypeDeclaration(self, tok, loc, sLabel=None, sName=None):
        tokComma, type = self.ParseTypeSpec(tok)
        if tokComma[1]==",":
            decl           = Declaration(sType=type, sComma=tokComma[1],
                                         loc=loc, nIndent=self.nIndent)
        else:
            decl           = Declaration(sType=type, loc=loc, nIndent=self.nIndent)

        # now loop for attributes
        while tokComma[1]==",":
            tok  = self.GetNextToken()
            sAtt = string.upper(tok[1])
            if sAtt=="DIMENSION":
                tok2=self.GetNextToken()
                tokComma,att = self.ParseArraySpec(sName=tok[1],
                                                   tok=tok2)
            elif sAtt=="INTENT":
                tokParOpen = self.GetNextToken()
                assert tokParOpen[1]=="("
                tokIntent = self.GetNextToken()
                tokParClose = self.GetNextToken()
                assert tokParClose[1]==")"
                att = Intent(tok[1], tokParOpen[1], tokIntent[1],
                             tokParClose[1])
                tokComma = self.GetNextToken()
            else:
                tokComma = self.GetNextToken()
                att = tok[1]
            if tokComma[1]==",":
                decl.AddAttribute(att, tokComma[1])
            else:
                decl.AddAttribute(att)

        if tokComma[1]==":":
            decl.AddDoubleColons(tokComma[1], self.GetNextToken()[1])
            tok = self.GetNextToken()
        else:
            tok = tokComma
        # Next: loop over the list of variables
        while 1:
            var = self.sub.GetVariable(tok[1], {'type':type})
            self.SetAllAttributes(var, decl)
            tok = self.GetNextToken()
            if tok and tok[1]=="(":
                tok,arrspec = self.ParseArraySpec(tok=tok, var=var)
                var.SetAttribute('dimension',arrspec.GetArraySpec())
                declvar = arrspec
                var = declvar
            if tok and tok[1]=='*':
                tok1 = self.GetNextToken()
                if tok1[0]==Token.tok_NUMBER:
                    self.scanner.UnGet(tok1)
                    tokNext, len = self.ParseExpression(self.GetNextToken())
                    declvar = VariableWithLen(var, tok[1], len)
                    tok = tokNext
                else: 
                    declvar = VariableWithLen(var, tok[1])
                    declvar.SetParenthesisStar(tok1[1], self.GetNextToken()[1],
                                               self.GetNextToken()[1])
                    tok = self.GetNextToken()
                    
            else:
                declvar=var
            if tok and tok[1]!=",":
                # Now test if an initialization part is following
                if tok[1]=='=':
                    tokEqual=tok
                    tok, exp = self.ParseExpression(self.GetNextToken())
                    declvar.SetAttribute("init",exp)
                    declvar = VariableWithInit(declvar, sEqual=tokEqual[1],
                                               value=exp)
                elif tok[1]=='/':
                    tok, dvl = self.ParseDataValueList(tok)
                    declvar.SetAttribute("init",dvl)
                    declvar = VariableWithInit(declvar, dataobj=dvl)

            if tok[1]==",":
                decl.AddDeclaredVariable(declvar, tok[1])
                tok = self.GetNextToken()
            else:
                decl.AddDeclaredVariable(declvar)

            if tok[0]==Token.tok_SEPARATOR:
                return (self.GetNextToken(), decl)

            #tok = self.GetNextToken()

# --------------------------------------------------------------------------
    # USE [ [ , module-nature ] :: ] module-name [ , rename-list ]
    # USE [ [ , module-nature ] :: ] module-name ,  ONLY : [ only-list ]
    # module-nature is INTRINSIC or NON_INTRINSIC
    # rename is local-name => use-name or
    #    OPERATOR (local-defined-operator) =>  OPERATOR (use-defined-operator)
    def ParseUse(self, tokUse, loc, sLabel=None, sName=None):
        use = Use(loc, tokUse[1], self.nIndent)
        tok = self.GetNextToken()
        if tok[1]==",":
            use.SetNature(tok[1], self.GetNextToken()[1] )
            tok = self.GetNextToken()
            assert tok[1]==":"
        if tok[1]==":":
            tok1 = self.GetNextToken()
            assert tok1[1]==":"
            use.AddDoubleColon(tok[1], tok1[1])
            tok = self.GetNextToken()
        use.SetName(tok[1])
        module = self.project.oGetObjectForIdentifier(tok[1], "module")
        if not module:
            Warning("Module '%s' not found"%tok[1])
            
        tokComma=self.GetNextToken()
        # done if no , is following
        if not tokComma or tokComma[1]!=",":
            assert tokComma[0]==Token.tok_SEPARATOR
            if module:
                module.CopyDeclarationTo(self.sub)
            return (self.GetNextToken(), use)

        use.AddComma(tokComma[1])
        # Now we have either an only or an rename use statement
        tok=self.GetNextToken()
        if string.upper(tok[1])=="ONLY":
            use.AddOnlyString(tok[1], self.GetNextToken()[1])
            while 1:
                tok      = self.GetNextToken()
                var      = self.sub.AddVariable(tok[1], {"module":use.GetName()})
                tokComma = self.GetNextToken()
                if module:
                    module.CopyDeclarationTo(self.sub, sVar=tok[1])
                if tokComma[1]!=",":
                    use.AddOnly(var)
                    assert tokComma[0]==Token.tok_SEPARATOR
                    return (self.GetNextToken(), use)
                use.AddOnly(var, sComma=tokComma[1])
        else:
            tokFrom = tok
            while 1:
                if string.upper(tokFrom[1])=="OPERATOR":
                    raise NotYetImplemented("Renaming Operators", self.scanner)
                tokArrow = self.GetNextToken()
                assert tokArrow[1]=="=>"
                tokTo = self.GetNextToken()
                var   = self.sub.AddVariable(tokTo[1], {"module":use.GetName(),
                                                        "renamedfrom":tokFrom[1]})
                tokComma=self.GetNextToken()
                if module:
                    module.CopyDeclarationTo(self.sub, sVar=tokTo[1],
                                             sRenamedTo=tokFrom[1])
                if tokComma[1]!=",":
                    use.AddRename(tokFrom[1], tokArrow[1], tokTo[1])
                    assert tokComma[0]==Token.tok_SEPARATOR
                    return (self.GetNextToken(), use)
                use.AddRename(tokFrom[1], tokArrow[1], tokTo[1], tokComma[1])
                tokFrom = self.GetNextToken()
        
    # --------------------------------------------------------------------------
    # Helper functions
    # --------------------------------------------------------------------------
    # (array-spec) is explicit-shape-spec-list or assumed-shape-spec-list
    #                 or deferred-shape-spec-list or assumed-size-spec
    # or:
    # array-spec:   [ scalar-int-expr : ] scalar-int-expr,...   or
    #               [ scalar-int-expr ] :                ,...   or
    #               :                                    ,...   or
    #               [[ scalar-int-expr : ] scalar-int-expr,]...,
    #                                       [ scalar-int-expr : ] *
    def ParseArraySpec(self, tok=None, sName="", var=""):
        arrayspec = ArraySpecWithName(sName=sName, var=var)
        assert tok[1]=="("
        arrayspec.SetParOpen(tok[1])
        tok = self.GetNextToken()
        while tok[1]!=")":
            if tok[1]=="*":
                oas = OneArraySpec(lower = tok[1])
                tok      = self.GetNextToken()
            elif tok[1]==":":
                oas = OneArraySpec(sColon=tok[1])
                tok=self.GetNextToken()
            else:
                tokColon, lower=self.ParseExpression(tok)
                if tokColon[1]==":":
                    tok = self.GetNextToken()
                    if tok[1]=="*":
                        oas = OneArraySpec(lower=lower, sColon=tokColon[1],
                                           upper=tok[1])
                        tok = self.GetNextToken()
                    elif tok[1]!="," and tok[1]!=")":
                        tok, upper=self.ParseExpression(tok)
                        oas = OneArraySpec(lower=lower, sColon=tokColon[1],
                                           upper = upper)
                    else:
                        oas = OneArraySpec(lower=lower, sColon=tokColon[1])
                else:
                    oas = OneArraySpec(lower=lower)
                    tok = tokColon
            if tok[1]==",":
                arrayspec.AddSubscript(oas, tok[1])
                tok=self.GetNextToken()
            else:
                arrayspec.AddSubscript(oas)
            
        arrayspec.SetParClose(tok[1])
        tok = self.GetNextToken()
        return (tok, arrayspec)
    # --------------------------------------------------------------------------
    # Parses a basic type (integer, char, double precision, ...) and returns
    # a type object. Important thing here is to handle 'doubleprecision' (or
    # 'double precision') correctly. It will not parse any kind information!
    def ParseBasicType(self, tok):
        sType = string.upper(tok[1])
        if sType=='DOUBLEPRECISION':
            if isinstance(tok[1], AttributeString):
                s1, s2 = tok[1].tSplitString(6)
            else:
                s1 = tok[1][0:6]
                s2 = tok[1][6: ]
            type=Type(sType=s1, sType2 = s2)
        elif sType=="DOUBLE":
            tokPrecis=self.GetNextToken()
            type=Type(sType=tok[1], sType2 = tokPrecis[1])
        elif sType=="TYPE":
            tokParOpen = self.GetNextToken()
            tokParClose, subtype = self.ParseBasicType(self.GetNextToken())
            type=UserType(tok[1], tokParOpen[1], subtype, tokParClose[1])
        else:
            type = Type(sType=tok[1])
        return self.GetNextToken(), type

    # --------------------------------------------------------------------------
    # kind-selector is ( [ KIND = ] scalar-int-initialization-expr )
    # char-selector is length-selector or ( LEN = type-param-value ,
    #                                    KIND = scalar-int-initialization-expr )
    #       or ( type-param-value ,  [ KIND = ] scalar-int-initialization-expr )
    # or ( KIND = scalar-int-initialization-expr  [ , LEN = type-param-value ] )
    # As a (non standard) extension, it will also accept a single number,
    # this will allow a declaration like integer *8
    # tok must be ( or *
    def ParseKindCharSelector(self, tok, type):
        if tok[1]=='*':
            type.SetStar(tok[1])
            tok = self.GetNextToken()
            if tok[1]!='(':
                tok, exp = self.ParsePrimary(tok)
                type.SetLen(exp)
                return tok, type
        if tok[1]!='(':
            # e.g. real r
            if tok[1]!='*':
                return tok, type
            # e.g. integer *8 declaration.
            tok, exp = self.ParseExpression(tok)
            type.SetLen(tok[1], exp)
            return tok, type
        type.SetParOpen(tok[1])
        while tok[1]!=')':
            tok = self.GetNextToken()
            s = string.upper(tok[1])
            if s=='KIND' or s=='LEN':
                sKindOrLen = tok[1]
                sEqual = self.GetNextToken()[1]
                tok    = self.GetNextToken()
                if tok[1]!='*':
                    tok, exp = self.ParseExpression(tok)
                else:
                    exp =tok[1]
                    tok = self.GetNextToken()
            else:
                sKindOrLen = None
                sEqual     = None
                if tok[1]=='*':
                    exp = tok[1]
                    tok = self.GetNextToken()
                else:
                    tok, exp = self.ParseExpression(tok)
            if tok[1]==',':
                type.AddKindOrLen(sKindOrLen, sEqual, exp, tok[1])
            else:
                type.AddKindOrLen(sKindOrLen, sEqual, exp)
                
        assert tok[1]==")"
        type.SetParClose(tok[1])
        tokNext = self.GetNextToken()
        return tokNext, type
    # --------------------------------------------------------------------------
    # type-spec        is INTEGER [ kind-selector ]   or REAL [ kind-selector ]
    #                  or DOUBLE PRECISION or COMPLEX [ kind-selector ]
    #                  or CHARACTER [char-selector] or LOGICAL [ kind-selector ]
    # char-selector    is length-selector
    # length-selector  is ( [ LEN = ] type-param-value ) or * char-length [ , ]
    # type-param-value is scalar-int-expr or * or :
    def ParseTypeSpec(self, tok):
        tok, type = self.ParseBasicType(tok)
        if tok[1]=='(' or tok[1]=='*':
            tok, type = self.ParseKindCharSelector(tok, type)
        return tok, type
            
    # --------------------------------------------------------------------------

# ==============================================================================
if __name__=="__main__":
    from Test.ParseSpecificationTest import RunAllTests
    RunAllTests()
