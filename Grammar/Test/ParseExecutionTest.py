#!/usr/bin/env python

from Tools.Test          import TestCase, TestSuite
from ParseTestBaseClass  import ParseTestBaseClass

# ===========================================================================
class ParseIfTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "If",
                                ["IF (1.eq.1) a=1",
"""IF (1.eq.1) THEN
  a = 1
ENDIF""",
"""IF (1.eq.1) THEN
  a = 1
ELSE
  b = 2
ENDIF""",
"""IF (1.eq.1) THEN
  a = 1
ELSE IF (2.NE.2) THEN
  b = 2
ENDIF""",
"""IF (1.eq.1) THEN
  a = 1
ELSE IF (2.NE.2) THEN
  b = 2
ELSE
  c = 3
ENDIF""",
"""IF (1.eq.1) THEN
  a = 1
ELSE IF (2.NE.2) THEN
  b = 2
ELSE IF (3.NE.3) THEN
  c = 3
ELSE
  d = 4
ENDIF""",
"""test: IF (1.eq.1) THEN
  a = 1
ELSE IF (2.NE.2) THEN test
  b = 2
ELSE IF (3.NE.3) THEN test
  c = 3
ELSE test
  d = 4
ENDIF test""",
""" IF (a) 10,20,30"""
] )
        
# ===========================================================================
class ParseArithIfTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Airthmetic If",
                                    ["IF (1.eq.1) 100,200,300"])

# ===========================================================================
class ParseDoTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Do",
                                    [
"""\
DO i=1, 10
  a = 1
ENDDO""",

"""\
DO i=1, 10
  DO j=1, 10
    a(i,j) = 1
  END DO
ENDDO""",

"""\
name: DO i=1, 10
  name2: DO j=1, 10
    a(i,j) = 1
  ENDDO name2
ENDDO name""",

"""\
#100# name: DO 200 i=1, 10
#110# name2:  DO 210 j=1, 10
    a(i,j) = 1
#210#  ENDDO name2
#200# ENDDO name""",

"""\
#100# DO 200 i=1, 10
#110#   DO 210 j=1, 10
    a(i,j) = 1
#210#  ENDDO
#200# ENDDO """,

"""\
#100# DO i=1, 10
#110#   DO j=1, 10
    a(i,j) = 1
#210#  ENDDO
#200# ENDDO """,

"""\
DO 100 i=1, 10
  a = 1
#100# CONTINUE""",

"""\
DO 200 i=1, 10
  DO 210 j=1, 10
    a(i,j) = 1
#210#  CONTINUE
#200# CONTINUE """,

"""\
DO 200 i=1, 10
  DO 210 j=1, 10
    a(i,j) = 1
#333#  CONTINUE    
#210#  CONTINUE
#200# CONTINUE """,

"""\
DO 200 i=1, 10
  DO 200 j=1, 10
    a(i,j) = 1
#200# CONTINUE """,

"""\
DO 200 i=1, 10
  DO 200 j=1, 10
    DO 200 k=1, 10
      a(i,j,k) = 1
#200# CONTINUE """,

"""\
DO 200 i=1, 10
  DO 200 j=1, 10
    DO 200 k=1, 10
      DO 300 l=1,5
        DO 300 m=1, 5
          a(i,j,k,l,m) = 1
#300# CONTINUE
#200# CONTINUE """,

"""\
DO 200 i=1, 10
  DO 200 j=1, 10
    DO 200 k=1, 10
      DO 300 l=1,5
        DO 300 m=1, 5
#300#     a(i,j,k,l,m) = 1
#200# b(i,j,k) = 2 """,

"""\
DO
  a = 1
ENDDO""",

"""\
DO 100
  a = 1
#100# ENDDO""",

"""\
DO
  DO
    a(i,j) = 1
  END DO
ENDDO""",

"""\
name: DO
  name2: DO
    a(i,j) = 1
  ENDDO name2
ENDDO name""",

"""\
DO WHILE (a.NE.1)
  a = 1
ENDDO""",

"""\
DO, WHILE (a.NE.1)
  a = 1
ENDDO""",

"""\
DO 100 WHILE (a.NE.1)
  a = 1
#100# ENDDO""",

"""\
DO 100, WHILE (a.NE.1)
  a = 1
#100# ENDDO""",

"""\
DO WHILE (i.LE.10)
  DO WHILE (j.LE.20)
    a(i,j) = 1
  END DO
ENDDO""",

"""\
name: DO WHILE (i.LE.5)
  name2: DO WHILE (j.LE.5)
    a(i,j) = 1
  ENDDO name2
ENDDO name""",

                                 ] )
        
# ===========================================================================
class ParseReturnTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Return",
                                    ["RETURN", "RETURN 1+2*3"]
                                    )
# ===========================================================================
class ParseStopTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Stop",
                                    ["STOP", "STOP 12345", "STOP 'abc'"]
                                    )
# ===========================================================================
class ParsePauseTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Pause",
                                    ["PAUSE", "PAUSE 12345", "PAUSE 'abc'"]
                                    )
        
# ===========================================================================
class ParseIncludeTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Include",
                                    ["INCLUDE 'header.h'"]
                                    )
        
# ===========================================================================
class ParseAllocateTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Allocate",
                                    [
            "ALLOCATE()", "ALLOCATE(a)",
            "ALLOCATE(a(1,2,3))", "ALLOCATE(a(1:2,3,4:5))",
            "ALLOCATE(a(i,j), b(c,2+3*j))",
            "ALLOCATE(a(i,j), b(c,2+3*j), STAT=ierr)",
            "ALLOCATE(a(i,j), STAT=ierr, ERRMSG=c, SOURCE=s)",
            ]
                                    )
# ===========================================================================
class ParseDeallocateTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Deallocate",
                                    [
            "DEALLOCATE()",
            "DEALLOCATE(a)", "DEALLOCATE(a, b)",
            "DEALLOCATE(a(1)%b(3), b)",
            "DEALLOCATE(a, b, STAT=ierr)",
            "DEALLOCATE(a, STAT=ierr, ERRMSG=c)",
            ]
                                    )
# ===========================================================================
class ParseNullifyTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Nullify",
                                    [ "NULLIFY(a)", "NULLIFY(a%b, a%c)" ] )
    
# ===========================================================================
class ParseCallTest(ParseTestBaseClass):
    def __init__(self):
        # JH todo: return with value
        ParseTestBaseClass.__init__(self, "Call",
                                    [
            "CALL sub", "CALL sub()", "CALL sub(1)", "CALL sub(1, a(:)+b)",
            "CALL sub(a(1:3), 987, \"b\", xyz)",
            "CALL sub(a=1)", "CALL sub(1, x=a(:)+b)",
            "CALL sub(a(1:3), 987, s=\"b\", v=xyz)",
            "CALL sub(a(1:3), 987, s=\"b\", v=xyz, *1)",
            "CALL sub(a(1:3), 987, s=\"b\", v=xyz, *1, b=*2)",
# JH: todo
#            "CALL a%b%c(a(1:3), 987, s=\"b\", v=xyz)"
#            "CALL a%b%c(a(1:3), 987, s=\"b\", v=xyz,*1,x=*2)"
            ])
# ===========================================================================
class ParsePrintTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Print",
                                    [
            "PRINT *,1", "PRINT *,\"1+2 is \",3",
            "PRINT *,(2*i,i=1,2)", "PRINT *,(2*i,i+1,i=1,5,2)",
            "PRINT *,((i+j,j=1,5),i=1,7,3)",
            "PRINT *,((i,j,j=1,3),(k,i,k=1,3),i=1,3)",
            "PRINT *,((j+1,j+2,j+i,j=1,3),i,i+1,i+2,i=1,6)",
            "PRINT *,(((i+j+k,k=1,3),j=1,9,2),i=1,2)",
            "PRINT *,1+2*3,(i,i=1,10),\"TEst\",(j,j=1,2)",
            "PRINT 20,1,2,3", "PRINT \"(10F8.2)\",(a(i),i=1,10)",
            "PRINT \"(F8.2,I4,\"//var//\",1PE12.f\",(a(i),i=1,10)",
            "PRINT *,a(nread)(1:ind-1)",
            "PRINT '(10f8.2)',d(indx+1:indx+2*nlevls-1:2)" ]
                                    )
# ===========================================================================
class ParseWriteTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Write",
                                    [
            "WRITE (*,*) 1", "WRITE(*,*) \"1+2 is \",3",
            "WRITE (*,*) (2*i,i=1,2)", "WRITE(1,2) (2*i,i+1,i=1,5,2)",
            "WRITE (*,6)((i+j,j=1,5),i=1,7,3)",
            "WRITE(UNIT=6,FMT='10f',NML=nml, ADVANCE='yes', END=12) 1,2",
            "WRITE(ASYNCHRONOUS='yes', POS=123, REC=654 , SIZE=123) 1,2",
            "WRITE (6,'('' Invalid directory given for CO2 tables '')')",
            ]
                                    )
# ===========================================================================
class ParseInquireTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Inquire",
                                    [
            "INQUIRE(IOLENGTH=iol) a(1:n), b",
            "INQUIRE(UNIT=1, NAME='test.dat')"
            ]
                                    )
# ===========================================================================
class ParseReadTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Read",
                                    [
            "READ (*,*) a",
            "READ (*,*) (a(i),i=1,2)", "READ(1,2) (a(i),b(i),i=1,5,2)",
            "READ (*,6)((a(i+j),j=1,5),i=1,7,3)",
            "READ(UNIT=6,FMT='10f',NML=nml, ADVANCE='yes', END=12) a,b",
            "READ(ASYNCHRONOUS='yes', POS=123, REC=654 , SIZE=123) a,b",
            "READ (6,FMT='('//char_fmt//')')",
            "READ '(10i4)', a", "READ 10, a", "READ *, a",
            "READ '(10i4)'", "READ 10", "READ *",
            ]
                                    )
# ===========================================================================
class ParseRewindTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Rewind",
                                    [
            "REWIND 10", "REWIND(10)",
            "REWIND(UNIT=10,IOMSG=s1,IOSTAT=s2,ERR=123)"
            ]
                                    )
# ===========================================================================
class ParseBackspaceTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Backspace",
                                    [
            "BACKSPACE 10", "BACKSPACE(10)",
            "BACKSPACE(UNIT=10,IOMSG=s1,IOSTAT=s2,ERR=123)"
            ]
                                    )
# ===========================================================================
class ParseEndfileTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Endfile",
                                    [
            "ENDFILE 10", "ENDFILE(10)",
            "ENDFILE(UNIT=10,IOMSG=s1,IOSTAT=s2,ERR=123)"
            ]
                                    )
# ===========================================================================
class ParseFormatTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Format",
                                    [
            "FORMAT(3(1X,/),1X,80('*')/1X/1X,20('*'),'  WARNING  ',20('*'))",
            # (/ is a single token for the scanner, so test this next
            "FORMAT(//,' THE FOLLOWING',I4,' ANALYSIS SUBVOLUMES WILL BE')"
            ]
                                    )
# ===========================================================================
class ParseOpenTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Open",
                                    [
            "OPEN(10)", "OPEN(UNIT=10)",
            "OPEN(10,FILE='test.dat',RECL=12,IOMSG=a)",
            # Test if open can be used as a scalar variable!
            "LOGICAL open\nopen = .TRUE.",
            ]
                                    )
        
# ===========================================================================
class ParseGotoTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Goto",
                                    [ "GOTO 100" ]
                                    )
# ===========================================================================
class ParseCompGotoTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Computed Goto",
                                    [ "GOTO (10,20) a",
                                      "GOTO () a",
                                      "GOTO (1,2,3,4,5) a+b**c",
                                      "GOTO (10,20), a",
                                      "GOTO (), a",
                                      "GOTO (1,2,3,4,5), a+b**c",
                                      ]
                                    )
        
# ===========================================================================
class ParseAssignmentTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Assignment",
                                    [ 'a=b', 'a=3+4',
                                      'a=.FALSE.', 'b=.TRUE.'])
# ===========================================================================
class ParseExitTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Exit",
                                    [ 'EXIT', 'EXIT test'])
# ===========================================================================
class ParseCycleTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Cycle",
                                    [ 'CYCLE', 'CYCLE test'])
        
# ===========================================================================
class ParseCloseTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Close",
                                    [
            "CLOSE(1)", "CLOSE(UNIT=1)",
            "CLOSE(UNIT=6,IOSTAT=io,IOMSG=iom,ERR=11, STATUS=stat)",
            ]
                                    )
# ===========================================================================
class ParseCaseTest(ParseTestBaseClass):
    def __init__(self):
        ParseTestBaseClass.__init__(self, "Case",
                                    [
"""\
SELECT CASE (i)
  CASE (1)
    j = 1
  CASE (2)
    j = 2
END SELECT""",

"""\
test:SELECT CASE (i)
  CASE (1) test
    j = 1
  CASE (2) test
    j = 2
END SELECT test""",

"""\
SELECT CASE (i)
  CASE (1)
    j = 1
  CASE (2)
    j = 2
  CASE DEFAULT
    j = 0
END SELECT""",

"""\
test:SELECT CASE (i)
  CASE (1) test
    j = 1
  CASE (2) test
    j = 2
  CASE DEFAULT
    j = 0
END SELECT test""",

"""\
SELECT CASE (i)
  CASE (1)
    j = 1
  CASE (:4)
    j = 2
  CASE (9:)
    j = 3
  CASE (11:13)
    j = 4
END SELECT""",

"""\
test:SELECT CASE (i)
  CASE (.TRUE.) test
    j = 1
  CASE ('dummy1') test
    j = 2
  CASE ('dummy2') test
    j = 3
END SELECT test""",

"""\
test:SELECT CASE (i)
  CASE (1,2,4) test
    j = 1
  CASE (1:,5:7,:-3) test
    j = 2
  CASE (1,2:4,:3,5:,9) test
    j = 3
END SELECT test""",
                                 ] )
        
# ===========================================================================
def CreateTestSuite():
    ts = TestSuite("Execution Part", bIsMain=1)
    ts.AddTest( ParseIfTest()         )
    ts.AddTest( ParseArithIfTest()    )
    ts.AddTest( ParseDoTest()         )
    ts.AddTest( ParseReturnTest()     )
    ts.AddTest( ParsePauseTest()      )
    ts.AddTest( ParseStopTest()       )
    ts.AddTest( ParseIncludeTest()    )
    ts.AddTest( ParseAllocateTest()   )
    ts.AddTest( ParseDeallocateTest() )
    ts.AddTest( ParseCallTest()       )
    ts.AddTest( ParsePrintTest()      )
    ts.AddTest( ParseWriteTest()      )
    ts.AddTest( ParseReadTest()       )
    ts.AddTest( ParseInquireTest()    )
    ts.AddTest( ParseRewindTest()     )
    ts.AddTest( ParseBackspaceTest()  )
    ts.AddTest( ParseEndfileTest()    )
    ts.AddTest( ParseNullifyTest()    )
    ts.AddTest( ParseOpenTest()       )
    ts.AddTest( ParseFormatTest()     )
    ts.AddTest( ParseGotoTest()       )
    ts.AddTest( ParseCompGotoTest()   )
    ts.AddTest( ParseAssignmentTest() )
    ts.AddTest( ParseExitTest()       )
    ts.AddTest( ParseCycleTest()      )
    ts.AddTest( ParseCloseTest()      )
    ts.AddTest( ParseCaseTest()       )
    return ts
# ===========================================================================
def RunAllTests():
    ts = CreateTestSuite()
    ts.RunAllTests()
# ===========================================================================

if __name__=="__main__":
    RunAllTests()
