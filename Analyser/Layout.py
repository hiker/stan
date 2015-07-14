#!/usr/bin/env python

from Tools.Error         import Error
from AOR.Variable        import Variable
from AOR.AttributeString import AttributeString, Comment, CommentLine, \
                                CompilerDirective, PreDirective, ContMarker

class Layout:

    def __init__(self, sLine):
        self.nIndent  = 7             # Current indentation
        self.nCol     = self.nIndent  # Current column
        self.nLine    = 0             # Current line number
        self.nMaxCol  = 72            # Maximum colum number for non-comments
        self.lLines   = []
        self.lAllLines=[sLine]
        
    # -------------------------------------------------------------------------
    def LayoutAll(self):
        for i in self.lAllLines:
            self.BreakIntoLines(i, nIndent=7)
        return self.lLines
    
    # -------------------------------------------------------------------------
    # Breakes a (recursive) list of tokens into lines. It takes care of
    # prefixes and postfixes of strings, indentation, ....
    def BreakIntoLines(self, lInput, nIndent):
        nStartLine = lInput.GetLocation()[0]
        for i in lInput:
            #print "current token '%s' (%s), col=%d"%(i,i.__class__,self.nCol)
            self.HandlePrefix(i, nIndent)
            while self.nLine<nStartLine:
                print self.nLine,nStartLine
                self.AppendNewLine(None, nIndent)
            nLen=len(i)
            #print "nlen",nLen,self.nCol, self.nMaxCol
            if self.nCol+nLen<=self.nMaxCol:
                self.AppendToCurrentLine(i)
            else:
                if self.nCol == nIndent:
                    raise("Not yet done: token '%s' does not fit in line"%i)
                self.AppendNewLine(i, nIndent)
                self.nCol = nIndent+nLen

    # -------------------------------------------------------------------------
    def AppendToCurrentLine(self, obj):
        lFlat = self.Flatten(obj)
        for i in lFlat:
            self.lLines[-1].append(i)
            self.nCol = self.nCol + len(i)
    # -------------------------------------------------------------------------
    def AppendNewLine(self, obj=None, nIndent=0):
        try:
            loc = obj.GetLocation()
            while self.nLine<loc[0]-1:
                self.lLines.append([])
                self.nLine = self.nLine + 1
            self.lLines.append([obj])
            self.nLine = self.nLine + 1
        except:
            if obj==None:
                self.lLines.append([])
            else:
                self.lLines.append([obj])
            self.nLine = self.nLine + 1
    # -------------------------------------------------------------------------
    def GetFirstRealToken(self, l):
        if isinstance(l, str) or isinstance(l,Variable):
            return l
        return self.GetFirstRealToken(l[0])
    # -------------------------------------------------------------------------
    # Finds the first real token (as opposed to a list token) and handles
    # any prefixes (a prefix will cause a line break)
    def HandlePrefix(self, s, nIndent):
        rtok = self.GetFirstRealToken(s)
        if not isinstance(rtok, AttributeString): return
        lPre = rtok.GetPrefixAttributes()
        if not lPre: return
        for i in lPre:
            if isinstance(i, CommentLine) or \
               isinstance(i, CompilerDirective) or\
               isinstance(i, PreDirective):
                self.AppendNewLine(i, nIndent)
                self.nCol=nIndent
            elif isinstance(i, ContMarker):
                pass
            else:
                raise Error("Wrong instance '%s' found"%i)
        self.AppendNewLine(obj=None, nIndent=nIndent)
        self.nCol=nIndent
                
    # -------------------------------------------------------------------------
    def Flatten(self, lOrig):
        l=[]
        if isinstance(lOrig,Variable) or isinstance(lOrig, str):
            return [lOrig]
        for i in lOrig:
            l.append(i)
        return l
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    
# =============================================================================
if __name__=="__main__":
    from Grammar.Parser     import Parser
    from Scanner.Scanner    import ScannerFactory
    parser  = Parser(sInput='''\
! Declare a, b, and c

!      integer(kind=2), dimension(10,4) :: a(1+2**5*4),b,c

      Real,Intent(IN),dimension(NJ,3,NLEV_CORR,NLAT_COV,2)::ct_ilat,
     >                                                      ct_ilat_d
''',
                     bTestOnly=1)
    tok, l = parser.ParseSpecification(parser.GetNextToken() )
    #for i in l:
    #    print "i=",i
    la=Layout(l)
    for i in la.LayoutAll():
        print i

