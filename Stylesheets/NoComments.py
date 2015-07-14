#!/usr/bin/env python

from Stylesheets.Default import DefaultStylesheet
from AOR.ProgUnit        import ProgUnit
from AOR.AttributeString import AttributeString, Comment, CommentLine, \
                                CompilerDirective, PreDirective, ContMarker

class NoComments(DefaultStylesheet):
    
    def __init__(self):
        DefaultStylesheet.__init__(self, 'fixed')
        self['keywordcase']    = 'identical'
        self['contlinemarker'] = '>'
    # -------------------------------------------------------------------------
    # This splits a list which represents a BasicStatement into a list of
    # list (of strings), the outer list each representing a new line, the inner
    # list of strings representing the actual statement. This functions
    # basically creates new lines dictated by the original progam layout by
    # inserting the comments, directives, ... from the AttributeStrings.
    def SplitIntoLines(self, l, lAttributesToPrint=[CompilerDirective, PreDirective]):
        #print "l is",l
        # The single line l (i.e. a list consisting of strings) is split into a
        # list of lines (each line again a list of strings). As a first step
        # any necessary line breaks in the original program (like comment line,
        # compiler directives, ...) are used to split each line.
        
        # The first element of l is the label (if exist) plus the spaces to
        # start at the (potential indentation marker) column, the second
        # element the correct number of spaces for indentation (see
        # BasicStatement). This is the prefix which has to be prepended to each
        # 'real' (not comment, directive, ...) statement. This second element
        # is always a real string (since this is constructed in BasicElement
        # based on the indentation function of the current stylesheet), but the
        # first element (either an empty string or a label string) might
        # contain attributes.
        d = {}
        for i in lAttributesToPrint:
            d[i]=1
        if type(l[0])==str:
            lLines = [ [l[0], l[1]] ]
            lStartStatement = l[0:2]
        else:
            # The first element has attributes (i.e. there is a label and any
            # attributes before):
            lLines = []
            for i in l[0].GetPrefixAttributes():
                if d.get(i.__class__,None): 
                    lLines.append("%s"%i)
            lLines.append(["%s"%l[0], l[1]]) # convert the AttributeString l[0] into a string
            lStartStatement=[" "*(self['startcolumn']-1), l[1]]
            
        # nCurrentColumn is the current column, startign with 0 for the first
        # column. It is used to indent comments in the same line as an
        # executable statement correctly.
        nCurrentColumn = len(l[0])+len(l[1])
        for i in l[2:]:
            if type(i)==str:
                # Check if the current string fits into the current line.
                # Since this is a string (and not an AttributeString), it
                # is clear that this string is part of the statement, we don't
                # have to test if a comment would be after maxcols (which
                # wouldn't matter).
                if nCurrentColumn+len(i)>self['maxcols']:
                    lLines.append([' '*(self['startcolumn']-2),
                                   self['contlinemarker']     , l[1],'  ', i])
                    nCurrentColumn = self['startcolumn']-1+len(l[1])+2+len(i)
                else:
                    lLines[-1].append(i)
                    nCurrentColumn = nCurrentColumn + len(i)
                continue
            
            # Now i is an Attribute string. First look for prefix attributes
            # Each of those must start on a new line, but a ContMarker is an
            # exception, since is is (for sure) the last attribute in a line,
            # AND it does not start a new line (in contrary it forces that
            # the next string belongs to the same line!!).
            bStartNewLine = 0
            for j in i.GetPrefixAttributes():
                if d.get(j.__class__,None):
                    if len(lLines[-1])==2:
                        lLines[-1]=["%s"%j]
                    else:
                        lLines.append(["%s"%j])
                    bStartNewLine = 1

            s = i.GetString()
            if bStartNewLine:
                lLines.append(lStartStatement+[s])
                nCurrentColumn = self['startcolumn']+1 + \
                                 len(lStartStatement[1])+len(s)
            else:
                lLines[-1].append(s)
                # This is not executed if a ContMarker was added. This basically
            lPostfix = i.GetPostfixAttributes()
            for j in lPostfix:
                if d.get(j.__class__,None):
                    lLines.append([`j`])

        return lLines
    # --------------------------------------------------------------------------
    def ToList(self, obj):
        if not isinstance(obj, ProgUnit):
            return DefaultStylesheet.ToList(self, obj)
        lOutput = []
        for i in obj:                   # loop over all statements
            l=self._flatten(DefaultStylesheet.ToList(self,i))
            lOutput.extend(self.SplitIntoLines(l))
        return lOutput
          
