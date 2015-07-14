#!/usr/bin/env python

import string
from   Tools.Test          import TestCase, TestSuite, Verbosity
# Work around for the naming problem: depending on how this module is
# used, we have to either use Scanner.Scanner or just Scanner (this is
# caused by having the same name for the directory and the actual file,
# depending on the current directory, Scanner.Scanner is either the file
# in the Scanner subdirectory (if the cwd is not Scanner) or a Scanner object
# in the Scanner file (if the cwd is Scanner)).
try:
    from   Scanner.Scanner import ScannerFactory
    from   Scanner.Token   import Token, Token2Name
except ImportError:
    from   Scanner         import ScannerFactory
    from   Token           import Token, Token2Name
    
from   AOR.AttributeString import AttributeString

# ===========================================================================
# The list of tests consists of a string containing the input for the
# scanner (it may contain \n for new lines), and a list of tokens which
# should be returned by the scanner. The tokens are in the form
# (tokenname, string) - see Token (and Token2Name) for all tokennames.
# Certain tokens (compiler- and preprocessor directives, comments, and
# continuation marker) are actually stored as postfix or prefix attributes
# of a 'real' token (a 'real' token is everything else). Currently,
# all such attribute tokens are stored as prefix attributes of the next
# real token, except for the last tokens of a file, which get stored
# as a postfix token of the last real token.
# Attributes are stored in the string part of a token, instead of
# a normal string an object of type AttributeString is created,
# which is a string plus a list of prefix- and postfix-attributes.
# For testing purposes, the attribute strings are written as
# [prefix]string[postfix].

class FixedScannerTest(TestCase):
    def __init__(self, sTitle="Fixed Format Scanner", sFormat="fixed"):
        TestCase.__init__(self,sTitle) 
        self.sFormat = sFormat
        self.lTests  = [
("      %b",                  [ ('tok_SPECIAL','%'),
                                ('tok_IDENTIFIER',"b"),
                                ('tok_SEPARATOR',""),
                                None] ),
("      b=*2)",               [ ('tok_IDENTIFIER','b'),
                                ('tok_SPECIAL',"="),
                                ('tok_OPERATOR',"*"),
                                ('tok_NUMBER',"2"),
                                ('tok_SPECIAL',")"),
                                ('tok_SEPARATOR',""),
                                None] ),
("      2_1",                [  ('tok_NUMBER','2'),
                                ('tok_SPECIAL',"_"),
                                ('tok_NUMBER',"1"),
                                ('tok_SEPARATOR',""),
                                 None] ),
("      2_KIND",            [  ('tok_NUMBER','2'),
                                ('tok_SPECIAL',"_"),
                                ('tok_IDENTIFIER',"KIND"),
                                ('tok_SEPARATOR',""),
                                None] ),
("      a;b\n      c;d",      [ ('tok_IDENTIFIER','a'),
                                ('tok_SEPARATOR', ';'),
                                ('tok_IDENTIFIER','b'),
                                ('tok_SEPARATOR', '' ),
                                ('tok_IDENTIFIER','c'),
                                ('tok_SEPARATOR', ';'),
                                ('tok_IDENTIFIER','d'),
                                ('tok_SEPARATOR', '' ) ] ),
("      integer :: a",        [ ('tok_IDENTIFIER',"integer"),
                                ('tok_SPECIAL',   ":"),
                                ('tok_SPECIAL',   ":"),
                                ('tok_IDENTIFIER',"a")        ]),
("      common //a",          [ ('tok_IDENTIFIER',"common"),
                                ('tok_OPERATOR',  "//"),
                                ('tok_IDENTIFIER',"a")        ]),
("      a.eq.12.and.b.eq.13", [ ('tok_IDENTIFIER',"a"),
                                ('tok_OPERATOR',".eq."),
                                ('tok_NUMBER',"12"),
                                ('tok_OPERATOR',".and."),
                                ('tok_IDENTIFIER',"b"),
                                ('tok_OPERATOR',".eq."),
                                ('tok_NUMBER',"13")      ]  ),
("      a.eq.0. .and.b.eq.13.",[ ('tok_IDENTIFIER',"a"),
                                ('tok_OPERATOR',".eq."),
                                ('tok_NUMBER',"0."),
                                ('tok_OPERATOR',".and."),
                                ('tok_IDENTIFIER',"b"),
                                ('tok_OPERATOR',".eq."),
                                ('tok_NUMBER',"13.")      ]  ),
("      0. and. b",           [ ('tok_NUMBER','0'),
                                ('tok_OPERATOR','. and.'),
                                ('tok_IDENTIFIER','b')] ),
("      a**12",               [ ('tok_IDENTIFIER',"a"),
                                ('tok_OPERATOR',"**"),
                                ('tok_NUMBER',"12")]  ),
("      i,i=1,3",
                              [ ('tok_IDENTIFIER',"i"),
                                ('tok_SPECIAL',","),
                                ('tok_IDENTIFIER',"i"),
                                ('tok_SPECIAL',"="),
                                ('tok_NUMBER',"1"),
                                ('tok_SPECIAL',","),
                                ('tok_NUMBER',"3") ]  ),
("      a=\"TeSt\"",          [ ('tok_IDENTIFIER',"a"),
                                ('tok_SPECIAL',"="),
                                ('tok_QUOTE','"TeSt"')]  ),
("      a==b",                [ ('tok_IDENTIFIER',"a"),
                                ('tok_OPERATOR',"=="),
                                ('tok_IDENTIFIER',"b")] ),
("* Comment\n      a",        [ ('tok_COMMENTLINE',"* Comment"), ('tok_SEPARATOR',''),
                                ('tok_IDENTIFIER',"a") ] ),
("! Comment\n! Com2\n      a",[ ('tok_COMMENTLINE',"! Comment"), ('tok_SEPARATOR',''),
                                ('tok_COMMENTLINE',"! Com2")   , ('tok_SEPARATOR',''),
                                ('tok_IDENTIFIER',"a") ] ),
("C Comment\n      a",        [ ('tok_COMMENTLINE',"C Comment"), ('tok_SEPARATOR',''),
                                ('tok_IDENTIFIER',"a") ] ),
("12345 id",                  [ ('tok_LABEL',"12345"),
                                ('tok_IDENTIFIER','id') ] ),
("1     id ",                 [ ('tok_LABEL',"1"),
                                ('tok_IDENTIFIER','id') ] ),
("12345 BEGIN2345678901234567890123456789012345678901234567890123456789012COMMENT",
                              [ ('tok_LABEL',"12345"),
                                ('tok_IDENTIFIER','BEGIN2345678901234567890123456789012345678901234567890123456789012[COMMENT]') ] ),
("     &cont",                [ ('tok_IDENTIFIER','[&]cont') ] ),
("     & cont",               [ ('tok_IDENTIFIER','[&]cont') ] ),
("      s1; s2",              [ ('tok_IDENTIFIER','s1'),
                                ('tok_SEPARATOR',';'),
                                ('tok_IDENTIFIER','s2'),
                                ('tok_SEPARATOR','') ]),
("""\
      s1
     & s2""",                 [ ('tok_IDENTIFIER','s1'),
                                ('tok_IDENTIFIER','[&]s2'),
                                ('tok_SEPARATOR','') ]),
("""\
      s1     !comment
     & s2""",                 [ ('tok_IDENTIFIER','s1[!comment]'),
                                ('tok_IDENTIFIER','[&]s2'),
                                ('tok_SEPARATOR','') ]),
("""\
      s1     !comment
!CommentLine      
     & s2""",                 [ ('tok_IDENTIFIER','s1[!comment]'),
                                ('tok_IDENTIFIER','[!CommentLine, &]s2'),
                                ('tok_SEPARATOR','') ]),
("""\
      s1     !comment

!CommentLine      
     & s2""",                 [ ('tok_IDENTIFIER','s1[!comment]'),
                                ('tok_IDENTIFIER','[, !CommentLine, &]s2'),
                                ('tok_SEPARATOR','') ]),
("""\
      's1
     &  still string'""",      [ ('tok_QUOTE_START','\'s1'),
                                 ('tok_QUOTE_END','[&]  still string\'')]),
('''\
      "s1
     &  still string"''',      [ ('tok_QUOTE_START','"s1'),
                                 ('tok_QUOTE_END','[&]  still string"')]),
("""\
      's1''
     &  still string'""",      [ ('tok_QUOTE_START',"'s1''"),
                                 ('tok_QUOTE_END','[&]  still string\'')]),
('''\
      "s1""
     &  still string"''',      [ ('tok_QUOTE_START','"s1""'),
                                 ('tok_QUOTE_END','[&]  still string"')]),
("""\
      's1
     & more string
     & still string'""",      [ ('tok_QUOTE_START','\'s1'),
                                ('tok_QUOTE_MIDDLE','[&] more string'),
                                ('tok_QUOTE_END','[&] still string\'')]),
('''\
      "s1
     & more string
     & still string"''',      [ ('tok_QUOTE_START','"s1'),
                                 ('tok_QUOTE_MIDDLE','[&] more string'),
                                 ('tok_QUOTE_END','[&] still string"')]),
("""\
      's1
     & more string''
     & still string'""",      [ ('tok_QUOTE_START',"'s1"),
                                ('tok_QUOTE_MIDDLE',"[&] more string''"),
                                ('tok_QUOTE_END','[&] still string\'')]),
('''\
      "s1
     & more string""
     & still string")''',      [ ('tok_QUOTE_START','"s1'),
                                 ('tok_QUOTE_MIDDLE','[&] more string""'),
                                 ('tok_QUOTE_END','[&] still string"'),
                                 ('tok_SPECIAL',')')]),
('''\
      s="test
     & still string"
      id            ''',       [ ('tok_IDENTIFIER','s'),
                                 ('tok_SPECIAL','='),
                                 ('tok_QUOTE_START','"test'),
                                 ('tok_QUOTE_END','[&] still string"'),
                                 ('tok_SEPARATOR',''),
                                 ('tok_IDENTIFIER','id')]),
('''\
      s="test
     & more string""
     & still string"
      id''',                   [ ('tok_IDENTIFIER','s'),
                                 ('tok_SPECIAL','='),
                                 ('tok_QUOTE_START','"test'),
                                 ('tok_QUOTE_MIDDLE','[&] more string""'),
                                 ('tok_QUOTE_END','[&] still string"'),
                                 ('tok_SEPARATOR',''),
                                 ('tok_IDENTIFIER','id')]),
('''\
!cdir nodep''',                [ ('tok_DIRECTIVE','!cdir nodep')   ]),
('''\
*cdir nodep''',                [ ('tok_DIRECTIVE','*cdir nodep')   ]),

('''\
      end
c comment''',                  [ ('tok_IDENTIFIER','end'),         ('tok_SEPARATOR',''),
                                  ('tok_COMMENTLINE','c comment'), ('tok_SEPARATOR','')
                                 ]),
                    ]
    # --------------------------------------------------------------------
    def GetNumberOfTests(self):
        # 2 Tests for getlinenumber, 2 for getcolumnnumber
        return len(self.lTests)+4
    # --------------------------------------------------------------------
    def RunTests(self):
        # First: test for getlinenumber:
        # ------------------------------
        scanner = ScannerFactory(format=self.sFormat,
                                 lines=["      a\n","       b\n"])
        scanner.GetNextToken()
        self.AssertEqual(scanner.GetLinenumber(),1,"GetLinenumber error 1")
        self.AssertEqual(scanner.GetColumnnumber(),7, "GetColumnnumber error 1")
        scanner.GetNextToken()   # Get the end of statement token
        scanner.GetNextToken()
        self.AssertEqual(scanner.GetLinenumber(),2,"GetLinenumber error 2")
        self.AssertEqual(scanner.GetColumnnumber(),8, "GetColumnnumber error 2")

        for input, lToken in self.lTests:
            scanner = ScannerFactory(format=self.sFormat,
                                     lines=string.split(input,"\n"))
            l       = []
            for t in lToken:
                tok=scanner.GetNextToken()
                if tok:
                    s=tok[1]
                    if isinstance(s,AttributeString):
                        sPre = string.join(map(lambda x:`x`,
                                               s.GetPrefixAttributes()),", ")
                        if sPre: sPre="[%s]"%sPre
                        sPost = string.join(map(lambda x:`x`,
                                                s.GetPostfixAttributes()),", ")
                        if sPost: sPost="[%s]"%sPost
                        s="%s%s%s"%(sPre,s,sPost)
                    l.append( (Token2Name(tok[0]), s) )
                else:
                    l.append(tok)
            self.AssertEqual(l, lToken)
            del scanner
# ===========================================================================
# The list of tests consists of a string containing the input for the
# scanner (it may contain \n for new lines), and a list of tokens which
# should be returned by the scanner. The tokens are in the form
# (tokenname, string) - see Token (and Token2Name) for all tokennames.
# Certain tokens (compiler- and preprocessor directives, comments, and
# continuation marker) are actually stored as postfix or prefix attributes
# of a 'real' token (a 'real' token is everything else). Currently,
# all such attribute tokens are stored as prefix attributes of the next
# real token, except for the last tokens of a file, which get stored
# as a postfix token of the last real token.
# Attributes are stored in the string part of a token, instead of
# a normal string an object of type AttributeString is created,
# which is a string plus a list of prefix- and postfix-attributes.
# For testing purposes, the attribute strings are written as
# [prefix]string[postfix].

class FreeScannerTest(FixedScannerTest):
    def __init__(self):
        FixedScannerTest.__init__(self, sTitle="Free Format Scanner",
                                   sFormat="free")
        self.lTests = [
("%b",                        [ ('tok_SPECIAL','%'),
                                ('tok_IDENTIFIER',"b"),
                                ('tok_SEPARATOR',""),
                                None] ),
("""\
abc &
 def""",                     [ ("tok_IDENTIFIER","abc[&]"),
                               ("tok_IDENTIFIER","def"),
                               ("tok_SEPARATOR","") ] ),
("""\
abc &
& def""",                     [ ("tok_IDENTIFIER","abc[&]"),
                                ("tok_IDENTIFIER","[&]def"),
                                ("tok_SEPARATOR","") ] ),

("(/1.2,3./)",                [ ("tok_SPECIAL","(/"),
                                ("tok_NUMBER","1.2"),
                                ("tok_SPECIAL",","),
                                ("tok_NUMBER","3."),
                                ("tok_SPECIAL","/)"),
                                ("tok_SEPARATOR","") ] ),

("""\
 (/3.,&
 &1.2/)""",                   [ ("tok_SPECIAL","(/"),
                                ("tok_NUMBER","3."),
                                ("tok_SPECIAL",",[&]"),
                                ("tok_NUMBER","[&]1.2"),
                                ("tok_SPECIAL","/)"),
                                ("tok_SEPARATOR","") ] ),
                                
("=>",                        [ ("tok_SPECIAL","=>"),
                                ("tok_SEPARATOR","") ] ),
                                
("""\
 a="ab&
   &  ef&
   &  gh",5
 """,                        [ ("tok_IDENTIFIER","a"),
                                ("tok_SPECIAL","="),
                                ("tok_QUOTE_START",'"ab[&]'),
                                ("tok_QUOTE_MIDDLE",'[&]  ef[&]'),
                                ("tok_QUOTE_END",'[&]  gh"'),
                                ("tok_SPECIAL",','),
                                ("tok_NUMBER",'5'),
                                ("tok_SEPARATOR","") ] ),
("""\
 a='ab&
   &  ef&
   &  gh',5
 """,                        [ ("tok_IDENTIFIER","a"),
                                ("tok_SPECIAL","="),
                                ("tok_QUOTE_START","'ab[&]"),
                                ("tok_QUOTE_MIDDLE",'[&]  ef[&]'),
                                ("tok_QUOTE_END","[&]  gh'"),
                                ("tok_SPECIAL",','),
                                ("tok_NUMBER",'5'),
                                ("tok_SEPARATOR","") ] ),

("a=\"\"",                    [ ("tok_IDENTIFIER","a"),
                                ("tok_SPECIAL","="),
                                ("tok_QUOTE",'""'),
                                ("tok_SEPARATOR","") ] ),
("""\
 a &  !comment
&  ef&
!more comments   
&  gh
 """,                        [ ("tok_IDENTIFIER","a[&, !comment]"),
                               ("tok_IDENTIFIER","[&]ef[&]"),
                               ("tok_IDENTIFIER","[!more comments, &]gh"),
                               ("tok_SEPARATOR","") ] ),

]
# ===========================================================================
def RunAllTests():
    ts = TestSuite("Scanner", bIsMain=1)
    ts.AddTest(FixedScannerTest())
    #ts.SetVerbose(Verbosity.verbALL)
    #ts.SetVerbose(Verbosity.verbNAME)
    ts.AddTest(FreeScannerTest())
    ts.RunAllTests()
# ===========================================================================

if __name__=="__main__":
    RunAllTests()
