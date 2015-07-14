#!/usr/bin/env python

import string
import sys
from   traceback           import print_exception
from   Tools.Test          import TestCase, TestSuite, Verbosity
from   AOR.AttributeString import AttributeString
from   AOR.Variable        import VariableData, Variable
from   Tools.VarUsage      import VarUsage
from   Grammar.Parser      import ParserClass

class VarUsageTest(TestCase):
    def __init__(self, sTitle="VarUsage Test", sFormat="fixed"):
        TestCase.__init__(self,sTitle) 
        self.lTests  = [
("      a='xxx'"                  , "write: a"                         ),
("      a(i)=b(i)"                , "read: b,i; write: a"              ),
("      a(i)=b(i)*c(k)"           , "read: b,c,i,k; write: a"          ),
("      a(i+j)=b(i+c(i)*d(i))"    , "read: b,c,d,i,j; write: a"        ),
("      a(i)%p=b(i)"              , "read: b,i; write: a"              ),
("      a(i)=(1,b)"               , "read: b,i; write: a"              ),
("      a=(/(i+k, i=1,3)/)"       , "read: i,k; write: a,i"            ),
("      a(i:)=b(i:n:2)"           , "read: b,i,n; write: a"            ),
("      print *,(a(i),i=1,n)"     , "read: a,i,n; write: i"            ),
("      a=b(i)(1:n)"              , "read: b,i,n; write: a"            ),
("      if(a(i).eq.j) 1,2,3"      , "read: a,i,j"                      ),
("      call sub(n,a(:), b(i:n))" , "read: i,n; unknown: a,b,n"        ),
("      a(i)=g(b(k),c)"           , "read: i,k; write: a; unknown: b,c"),
("      close(unit=1,status=stat)", "unknown: stat"                    ),
("      read(asynchronous='yes', pos=p, rec=r) a,(b(i),i=1,n)"
                                  , "read: i,n; write: a,b,i; unknown: p,r"),
("      write(asynchronous='yes', pos=p, rec=r) a,(b(i),i=1,n)"
                                  , "read: a,b,i,n; write: i; unknown: p,r"),
("""
      do i=1, a(j)+k*b, c
      enddo
"""                               , "read: a,b,c,j,k; write: i"        ),
("""
      do while(a(i).le.b(i))
      enddo
"""                               , "read: a,b,i"                      ),
("""
      do while(a(i).le.b(i))
         a(i)=a(i)+2
      enddo
"""                               , "read: a,b,i; write: a"            ),
("""
      if(a(i).eq.b(i+j)) then
      endif
"""                               , "read: a,b,i,j"                    ),
("""
      if(a(i).eq.b(i+j)) then
         c(j)=b(i+j)
      else
         d(j)=g(e(i))
      endif
"""                               , "read: a,b,i,j; write: c,d; unknown: e"),
        
                                ]
    # --------------------------------------------------------------------------
    def GetNumberOfTests(self):
        # 2 Tests for getlinenumber, 2 for getcolumnnumber
        return len(self.lTests)
    # --------------------------------------------------------------------------
    def RunTests(self):
        for sTest, sResult in self.lTests:
            sLines = string.split(sTest,"\n")
            parser = ParserClass(lInputLines=sLines, bTestOnly=1)
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
            parser.bIsExec = 0
            try:
                parser.ParseStatements(parser.GetNextToken(), nIndentModifier=1)
            except:
                excp, value, tb = sys.exc_info()
                # An error occured, force a wrong assertequal to note this error
                self.AssertEqual("",sResult, sComment="An exception occured")
                print_exception(excp, value, tb)
            v      = VarUsage()
            for obj in parser.sub:
                obj.GetVarUsage(v)
            s=v.GetTestOutput()
            self.AssertEqual("%s: %s"%(sTest,`s`), "%s: %s"%(sTest,`sResult`))
            
           
# ==============================================================================
def RunAllTests():
    ts = TestSuite("Tools", bIsMain=1)
    ts.AddTest(VarUsageTest())
    ts.RunAllTests()
# ==============================================================================
def CreateTestSuite():
    ts = TestSuite("VarUsage", bIsMain=1)
    ts.AddTest(VarUsageTest())
    return ts
# ==============================================================================

if __name__=="__main__":
    RunAllTests()
