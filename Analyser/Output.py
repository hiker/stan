#! /usr/bin/env python

import string
from   UserList            import UserList
from   AOR.Subroutine      import Subroutine
from   AOR.Function        import Function
from   AOR.Program         import Program
from   AOR.AttributeString import Comment
from   Tools.Config        import Config

# This is the base class for all output functions
class Output(Config):
    # Constructor. Parameter:
    #
    # f -- file object to output
    def __init__(self, f, nMaxCols=72, sFormat='fixed'):
        dClass2Func = { Comment   : self.CommentLine,
                        Subroutine: self.Subroutine,
                        #Function  : self.Function,
                        #Program   : self.Program,
                        #CommaList : self.CommaList,
                    }
                    
        Config.__init__(self, sFormat=sFormat)
        self.lOutput  = []
        self.nMaxCols = nMaxCols

        if self['keywordcase']=='upper':
            self.keyword = string.upper
        elif self['keywordcase']=='lower':
            self.keyword = string.lower
        else:
            self.keyword = string.capitalize
        # Init output device - currently nothing since stdout is used
        for i in f:
            self.DoOutput(i)

    # -------------------------------------------------------------------------
    def OutputAll(self):
        for i in self.lOutput:
            print i
    # -------------------------------------------------------------------------
    def Write(self, *a):
        s = string.join(a,'')
        print '-->',s
        self.lOutput.append(s)
    # -------------------------------------------------------------------------
    def DoOutput(self, obj):
        # Set the indentation.
        self.nIndent  = self['indent']
        try:
            f = self.dClass2Func[obj]
            apply(f, obj)
        except KeyError:
            pass
    # -------------------------------------------------------------------------
    def CommentLine(self, comment):
        s=`comment`
        self.Write(self.NewStatementNewLine(sCommentChar=s[0]),
                   s[1:])
    # -------------------------------------------------------------------------
    def Subroutine(self, sub):
        l        = []
        lsPrefix = sub.GetPrefix()
        if lsPrefix:
            l=lsPrefix
        l.extend([self.keyword('subroutine'),sub.GetName()])
        
        cl = self.GetArgument()
        if cl:
            l.extend(self.CommaList(cl))
            
    # -------------------------------------------------------------------------
    # Returns a list of elements of a comma-list, e.g. 'a, b, c' is returned
    # as ['a,', 'b,', 'c,'] or ['a, ', 'b, ', 'c, '] depending on the choosen
    # 'spacebetweencommalist' configuration
    def CommaList(self, cl):
        l = []
        if self['spacebetweencommalist']:
            sComma=', '
        else:
            sComma=','
        for i in cl:
            if type(i) == type(''):
                l.append('%s%s'%(i, sComma))
            else:
                s=apply(self.dClass2Func[i.__class__], i)
                l.append('%s%s'%(s, sComma))
        if l:
            # We have to remove the last comma from the last entry in the list
            l[-1] = l[-1][:-len(sComma)]
        return l
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
# =============================================================================
class OutputFixed(Output):

    # Constructor. Parameter:
    #
    # f -- file object
    def __init__(self, f):
        Output.__init__(self, f, sFormat='fixed')
    # -------------------------------------------------------------------------
    # Describes the beginning of a new line and a new statement. It will
    # place a comment line correcty (i.e. first column for fixed), and
    # labels as well. Enough spaces are added so that the actual statement
    # is indented correctly. Parameter:
    #
    # nIndent -- Column in which the output should start (without considering
    #            labels)
    #
    # sCommentChar -- If defined, a comment line is created and this character
    #                 should be used as a comment character
    #
    # sLabel -- If defined: the label to insert at the beginning
    def NewStatementNewLine(self, nIndent=7, sCommentChar=None, sLabel=None):
        if sCommentChar: return sCommentChar
        if sLabel:
            if self['labelalignright']:
                return '%5s %s'%(sLabel,' '*(nIndent-7))
            else:
                return '%-5s %s'%(sLabel, ' '*(nIndent-7))
        return ' '*(nIndent-1)
                    
# =============================================================================
class OutputFree(Output):
    # Constructor. Parameter:
    #
    # f -- file object
    def __init__(self, f):
        Output.__init__(self, f, sFormat='free')
    # -------------------------------------------------------------------------
    # Describes the beginning of a new line and a new statement. It will
    # place a comment line correcty (i.e. first column for fixed), and
    # labels as well. Enough spaces are added so that the actual statement
    # is indented correctly. Parameter:
    #
    # nIndent -- Column in which the output should start (without considering
    #            labels)
    #
    # sCommentChar -- If defined, a comment line is created and this character
    #                 should be used as a comment character
    #
    # sLabel -- If defined: the label to insert at the beginning
    def NewStatementNewLine(self, nIndent=1, sCommentChar=None, sLabel=None):
        # Convert all comment characters to '!'
        if sCommentChar: return '!'
        if sLabel:
            return '%s %s'%(sLabel, ' '*(nIndent-len(sLabel)-1))
        return ' '*(nIndent-1)
# =============================================================================
def usage():
    print 'Usage: Parser.py [-P] [-I] <list of files>'
    print
    print '-P: Profile'
    print '-I: Generate interface'
# -----------------------------------------------------------------------------

if __name__=='__main__':

    from Grammar.Parser import Parser
    import sys
    #parser  = Parser(sFilename=sys.argv[1])
    #objFile = parser.GetFileObject()
    
    from AOR.AttributeString import Comment
    import getopt
    #o = OutputFree([])
    #o['labelalignright']=0
    #c = Comment('C test1', (1, 1))
    #o.CommentLine(c)
    #o.OutputAll()
    #import sys
    #sys.exit()
    bDoProfile = 0
    bDoPrint   = 0
    bDoTest    = 0
    bInterface = 0
    # P : Profile
    # O : Output tokens
    lOpt, lArgs = getopt.getopt(sys.argv[1:],'POTI')
    for i in lOpt:
        if i[0]=='-P':
            bDoProfile=1
        elif i[0]=='-O':
            bDoPrint=1
        elif i[0]=='-T':
            bDoTest=1
        elif i[0]=='-I':
            bInterface=1
            
    if len(lArgs)<1:
        usage()

    if not bDoProfile:
        for i in lArgs:
            objFile = Parser(sFilename=i)
            if bDoPrint:
                print `objFile`
            if bInterface:
                from Analyser.Interface import GenerateInterface
                for i in objFile.GetAllSubroutines():
                    print GenerateInterface(i)
    else:
        import profile
        profile.run(
'''for i in lArgs:
    objFile = Parse(sFilename=i)
''')
