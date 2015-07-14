#!/usr/bin/env python

import string
import re
import sys
from   traceback         import print_exception

from Tools.Test          import TestCase
from Scanner.Scanner     import ScannerFactory
from Grammar.Parser      import ParserClass
from AOR.Variable        import VariableData, Variable

# ==============================================================================
# sName -- Name of the testcase
#
# part -- which part (declaration part or execution part) to initialise the
#         parser with
#
# l -- List if testcases.
#
class ParseTestBaseClass(TestCase):
    def __init__(self, sName, l):
        TestCase.__init__(self, sName)
        self.lTests = l
    # --------------------------------------------------------------------
    def GetNumberOfTests(self): 
        return len(self.lTests)
    # --------------------------------------------------------------------
    def Test(self, parser, tok):
        parser.bIsExec = 0
        res = parser.ParseStatements(tok, nIndentModifier=1)
        return parser.sub
    # --------------------------------------------------------------------
    def RunTests(self):
        r = re.compile("#([0-9]*)#")
        for sInput in self.lTests:
            lInput  = []
            lOutput = []
            for i in string.split(sInput,"\n"):
                g = r.match(i)
                # Support for labels in fixed form: labels are
                # specified as #label#!
                if g:
                    s=g.group(1)
                    s=" %s%s"%(s, " "*(6-len(s)))
                    lInput.append("%s\n"%r.sub(s,i))
                    lOutput.append("%s "%r.sub(g.group(1),i))
                else:
                    lInput.append("      %s\n"%i)
                    lOutput.append("%s"%i)
            parser = ParserClass(lInputLines=lInput, bTestOnly=1)
            # The test cases need some array variables, which must be
            # declared (otherwise the parser tries to parse them as
            # function calls). Therefore five variables a(n), ..., e(n)
            # are declared.
            vdata = VariableData('n',{})
            var   = Variable('n',vdata)
            parser.sub.AddArgument('a',d={"dimension":var})
            parser.sub.AddArgument('b',d={"dimension":var})
            parser.sub.AddArgument('c',d={"dimension":var})
            parser.sub.AddArgument('d',d={"dimension":var})
            parser.sub.AddArgument('e',d={"dimension":var})
            token  = parser.GetNextToken()
            try:
                use = self.Test(parser, token)
            except:
                excp, value, tb = sys.exc_info()
                # An error occured, force a wrong assertequal to note this error
                self.AssertEqual("",string.join(lOutput,"\n"),
                                 sComment="An exception occured")
                print_exception(excp, value, tb)
            else:
                self.AssertEqual(`use`, string.join(lOutput,"\n"))
            del parser
            
# ==============================================================================
