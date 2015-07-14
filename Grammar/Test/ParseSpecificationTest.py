#!/usr/bin/env python

from Tools.Test          import TestCase, TestSuite
from ParseTestBaseClass  import ParseTestBaseClass
from AOR.ProgUnit import ProgUnit

# ==============================================================================
class TestSpecificationBase(ParseTestBaseClass):
    def __init__(self, sName, l):
        ParseTestBaseClass.__init__(self, sName, l)
    # --------------------------------------------------------------------------
    def Test(self, parser, tok):
        parser.bIsExec = 0
        res = parser.ParseStatements(tok)
        return parser.sub 

# ==============================================================================
class ParseUseTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Use", 
                                       ["USE a"              , "USE :: a",
                                        "USE, INTRINSIC :: a",
                                        "USE, NON_INTRINSIC :: a",
                                        "USE a, b=>c, d=>e"  ,
                                        "USE :: a, b=>c, d=>e",
                                        "USE, INTRINSIC :: a, b=>c, d=>e",
                                        "USE a, ONLY : b, c, d",
                                        "USE :: a, ONLY : b, c, d",
                                        "USE, INTRINSIC :: a, ONLY : b, c, d"
                                        ] )
# ==============================================================================
class ParseBasicDeclarationTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Basic Declaration",
                                       [
            "DOUBLE PRECISION a, b", "INTEGER :: c",
            "LOGICAL, TARGET, POINTER, PARAMETER, EXTERNAL :: a",
            "REAL, INTRINSIC, OPTIONAL, SAVE :: b",
            "REAL, INTENT(IN) :: a(1,2:3)",
            "REAL, INTENT(OUT) :: a(1,2:3)",
            "REAL, INTENT(INOUT), TARGET :: a(1,2:3)",
            "REAL(3) b", "REAL(KIND=3) :: c",
            "REAL, DIMENSION(1,2) :: a, b(3,4)",
            "INTEGER*8 a,b", "CHARACTER*8 slflg",
            "CHARACTER dimnam*80","CHARACTER file_spectral*(*)",
            "CHARACTER slv_nam(nvar_slv)*80",
            "REAL cldlev /0.050,0.430,0.430,0.790,0.790,0.955/",
            "LOGICAL, SAVE :: first /.TRUE./",
            "INTEGER :: a=1, b=2, c /3/, d=4,e /5/",
            "INTEGER ::aaa(2,2) /3*1,2/",
            "INTEGER, PARAMETER :: u = iachar('a') - iachar('A')",
            "CHARACTER*(*), INTENT(OUT) :: sname",
            "CHARACTER(4,5) a", "CHARACTER(KIND=4,5) b",
            "CHARACTER(4, LEN=5) c",
            "CHARACTER(KIND=4, LEN=5) d",
            "CHARACTER(LEN=*) c",
            "TYPE(POINT) :: p",
            "REAL,PARAMETER,DIMENSION(7)::prf_strpht=(/23.,23.,23.,23.,23./)",
            "CHARACTER*(500), SAVE :: assc_file=''"
            ])
    
# ==============================================================================
class ParseDimensionTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Dimension",
                                       [
            "DIMENSION a(1,2)",
            "DIMENSION :: a(1,2)",
            "DIMENSION a(1+2*3**4), b(2:3,4:*), c(xx:yy)"
            ])
        
# ==============================================================================
class ParseParameterTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Parameter",
                                  ["PARAMETER(a=1)","PARAMETER(a=1, b=2+3*4)",
                                   "PARAMETER(a=1, b=2, c=3, d=4)"])
        
# ==============================================================================
class ParseCommonTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Common",
                                       [
            "COMMON a",            "COMMON a,b(1,2),c",
            "COMMON // a",         "COMMON // a,b(1,2),c",
            "COMMON /test/ a",     "COMMON /test/ a,b(1,2),c",
            "COMMON a, //b",       "COMMON a,b(1,2),c, //c,d(1,2),e",
            "COMMON a, /c1/b",     "COMMON a,b(1,2),c, /c1/c,d(1,2),e",
            "COMMON //a, //b",     "COMMON // a,b(1,2),c, //c,d(1,2),e",
            "COMMON //a, /c1/b",   "COMMON // a,b(1,2),c, /c1/c,d(1,2),e",
            "COMMON /c1/a, //b",   "COMMON /c1/ a,b(1,2),c, //c,d(1,2),e",
            "COMMON /c1/a, /c2/b", "COMMON /c1/ a,b(1,2),c, /c2/c,d(1,2),e",
            "COMMON a //b",        "COMMON a,b(1,2),c //c,d(1,2),e",
            "COMMON a /c1/b",      "COMMON a,b(1,2),c /c1/c,d(1,2),e",
            "COMMON //a //b",      "COMMON //a,b(1,2),c //c,d(1,2),e",
            "COMMON //a /c1/b",    "COMMON //a,b(1,2),c /c1/c,d(1,2),e",
            "COMMON /c1/a //b",    "COMMON /c1/a,b(1,2),c //c,d(1,2),e",
            "COMMON /c/e(1),f(1)",
            # Couldn't find any specification of 'global common', so currently
            # only the constructs which are used in mpif.h are tested here.
            "GLOBAL COMMON /c1/a //b",
            "GLOBAL COMMON /c1/a,b(1,2),c //c,d(1,2),e",
                                        ])
# ==============================================================================
class ParseNamelistTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Common",
                                       [
            "NAMELIST /a/",            "NAMELIST /a/b,c,d",
            "NAMELIST /a/,/b/c",       "NAMELIST /a/b, /c/d,e",
            "NAMELIST /a/ /b/c",       "NAMELIST /a/b  /c/d,e"
                                        ])
        
# ==============================================================================
class ParseSaveTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Save",
                                  ['SAVE a', '    SAVE :: a',
                                   'SAVE a,b,c', 'SAVE :: a,b,c',
                                   'SAVE a,/c1/,/c2/,b',
                                   'SAVE :: a,/c1/,b,/c2/',
                                   ])
        
# ==============================================================================
class ParseImplicitTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Implicit",
                                  [
            'IMPLICIT NONE',
            'IMPLICIT INTEGER (a)',
            'IMPLICIT INTEGER (a-b)',
            'IMPLICIT INTEGER (a-b)(c-d)',
            'IMPLICIT INTEGER (a**2-c*3-b)(c-d)',
            'IMPLICIT REAL (a,b,c)',
            'IMPLICIT DOUBLE PRECISION (a,b-f,y)',
            'IMPLICIT INTEGER(KIND=3) (a-f,h-l,y-z)',
            'IMPLICIT INTEGER(KIND=3+a-2*5) (a-f,h-l,y-z)',
            # Test if implicit can be used as a scalar variable
            'implicit = 1',
            ])
        
# ==============================================================================
class ParseIntrinsicTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Intrinsic",
                                  [ 'INTRINSIC abs',     'INTRINSIC :: abs',
                                    'INTRINSIC abs, sin','INTRINSIC :: abs, sin'
                                    ])
        
# ==============================================================================
class ParsePointerTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Pointer",
                                  ['POINTER a', 'POINTER a,b(:,:),c,d(:)',
                                   'POINTER :: a',
                                   'POINTER :: a, b(:),c,d(:,:,:,:)'
                                   ])
# ==============================================================================
class ParseCrayPointerTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Cray Pointer",
                                  ['POINTER (a,b)',
                                   'POINTER (a,b), (c,d), (e,f)'
                                   ])
        
# ==============================================================================
class ParseEquivalenceTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Equivalence",
                                  ['EQUIVALENCE (a,b)',
                                   'EQUIVALENCE (a,b,c)',
                                   'EQUIVALENCE (a,b,c,d,e)',
                                   'EQUIVALENCE (a(1),b(2),c,d(3,4))',
                                   'EQUIVALENCE (a,b),(c,d),(e,f),(g,h)',
                                   'EQUIVALENCE (a,b,c(3)), (d(3),e(4))'
                                   ])
# ==============================================================================
class ParseDataTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Data",
                                  ['DATA a /0/',
                                   'DATA (a(i), i=1, 4) / 4*0/',
                                   'DATA a /1,2*2.0,3/, b /4*1,3*2,2*3,1*4/',
                                   'DATA a /1,2*2.0,3/ b /4*1,3*2,2*3,1*4/',
                                   'DATA a/1/ b/2/, c/3/, d/4/ e/-5/',
                                   'DATA (a(i), i=1, 4) / 4*0/',
                                   'DATA (a(i), i=1, 4,2),b,(b(i),i=1,3)/ 4*0/',
                                   ])
        
# ==============================================================================
class ParseExternalTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "External",
                                  ['EXTERNAL a', 'EXTERNAL a,b,c,d',
                                   'EXTERNAL :: a', 'EXTERNAL :: a,b,c,d'
                                   ])
        
# ==============================================================================
class ParseAccessTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Access (private/public)",
                                  ["PRIVATE", "PUBLIC",
                                   "PRIVATE a,b", "PUBLIC a,b",
                                   "PRIVATE :: a, b", "PUBLIC :: a, b"
                                   ])
        
# ==============================================================================
class ParseModuleProcedureTest(TestSpecificationBase):
    def __init__(self):
        TestSpecificationBase.__init__(self, "Module Procedure",
                                  ["MODULE PROCEDURE a",
                                   "PROCEDURE a,b,c"
                                   ])
        
# ==============================================================================
def CreateTestSuite():
    ts = TestSuite("Specification", bIsMain=1)
    ts.AddTest(ParseUseTest())
    ts.AddTest(ParseBasicDeclarationTest())
    ts.AddTest(ParseDimensionTest())
    ts.AddTest(ParseParameterTest())
    ts.AddTest(ParseCommonTest())
    ts.AddTest(ParseNamelistTest())
    ts.AddTest(ParseSaveTest())
    ts.AddTest(ParseImplicitTest())
    ts.AddTest(ParseIntrinsicTest())
    ts.AddTest(ParsePointerTest())
    ts.AddTest(ParseCrayPointerTest())
    ts.AddTest(ParseEquivalenceTest())
    ts.AddTest(ParseDataTest())
    ts.AddTest(ParseExternalTest())
    ts.AddTest(ParseAccessTest())
    ts.AddTest(ParseModuleProcedureTest())
    return ts
# ==============================================================================
def RunAllTests():
    ts = CreateTestSuite()
    ts.RunAllTests()
# ==============================================================================

if __name__=="__main__":
    RunAllTests()
