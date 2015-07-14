#!/usr/bin/env python

from Tools.functions        import flatten
from Stylesheets.Default    import DefaultStylesheet
from   Stylesheets.Layout2d import Layout2d, MultiLine2d
from AOR.ProgUnit           import ProgUnit
from AOR.AttributeString    import AttributeString
from AOR.SpecialStatements  import Comment, CommentLine, CompilerDirective, \
                                   PreDirective, ContMarker

class f77(DefaultStylesheet):
    
    def __init__(self):
        DefaultStylesheet.__init__(self, 'fixed')
        self['keywordcase']    = 'identical'
        self['contlinemarker'] = '>'
    # -------------------------------------------------------------------------
    # This splits a list which represents a BasicStatement into a list of
    # list (of strings), the outer list each representing a new line, the inner
    # list of strings representing the actual statement. This functions
    # basically creates new lines dictated by the original progam layout by
    # inserting the comments, directives, ... from the AttributeStrings, and
    # if necessary split lines if they are too long for the maximum line length.
    def SplitIntoLines(self, l, bIgnoreAttributes=0):
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
        lLines = []
        lCurr  = Layout2d()
        if type(l[0])==str or bIgnoreAttributes:
            lStartStatement = l[0:2]
        else:
            # The first element has attributes (i.e. there is a label and any
            # attributes before):
            for i in l[0].GetPrefixAttributes():
                lLines.append(`i`)
            lStartStatement=[" "*(self['startcolumn']-1), l[1]]
            
        lCurr.extend(l[0:2])

        # nCurrentColumn is the current column, startign with 0 for the first
        # column. It is used to indent comments in the same line as an
        # executable statement correctly.
        nCurrentColumn = len(l[0])+len(l[1])
        for i in l[2:]:
            if type(i)==str or bIgnoreAttributes:
                # Check if the current string fits into the current line.
                # Since this is a string (and not an AttributeString), it
                # is clear that this string is part of the statement, we don't
                # have to test if a comment would be after maxcols (which
                # wouldn't matter).
                # In case that it is a single string (e.g. a comment), and
                # it's the first thing, we don't break the line. This helps
                # in case of a comment that's longer than the line length.
                if nCurrentColumn+len(i)>self['maxcols'] and \
                       nCurrentColumn!=0:
                    lLines.append(lCurr)
                    lCurr = Layout2d()
                    lCurr.indent(self['startcolumn']-2)
                    lCurr.extend([self['contlinemarker'], i])
                    nCurrentColumn = self['startcolumn']-1+len(i)
                else:
                    lCurr.append(i)
                    nCurrentColumn = nCurrentColumn + len(i)
                continue
            # Now i is an Attribute string. First look for prefix attributes
            # Each of those must start on a new line, but a ContMarker is an
            # exception, since is is (for sure) the last attribute in a line,
            # AND it does not start a new line (in contrary it forces that
            # the next string belongs to the same line!!).
            s=i.GetString()
            
            # When the first prefix attribute is handled, there is some
            # data in lCurr, which needs to be appended. 
            bIsFirst = 1
            for j in i.GetPrefixAttributes():
                if j.__class__==ContMarker:
                    # Handling the special case: do not start a new line,
                    # instead append the next string, since it does belong
                    # to the same line!!
                    if bIsFirst:
                        lLines.append(lCurr)
                    lCurr= Layout2d()
                    lCurr.indent(self['startcolumn']-2)
                    lCurr.append(`j`)
                    lCurr.extend([lStartStatement[1],s])
                    nCurrentColumn = self['startcolumn']-1 +\
                                     len(lStartStatement[1])+len(s)
                    break
                else:
                    if bIsFirst:
                        lLines.append(lCurr)
                    bIsFirst = 0
                    lLines.append(`j`)
                    lCurr = Layout2d()
            else:
                # This is not executed if a ContMarker was added. This basically
                # means we have to start a new line, because of the attribute -
                # except if there was no prefix attribute (e.g .only a comment
                # at the end of a line) - in this case the string has to be
                # added to the current line.
                # Only if no ContMarker was added, we have to append the string
                # next. And, in this case, it always starts a new line!!!
                if len(i.GetPrefixAttributes())==0:
                    lCurr.append(s)
                    nCurrentColumn = nCurrentColumn+len(s)
                # The current line is empty, i.e. it only contained
                # the strings for indentation --> the line is overwritten
                # with the actual string to append
                elif len(lCurr.lElements)==2:
                    lCurr = Layout2d()
                    lCurr.extend(lStartStatement+[s])
                    nCurrentColumn = self['startcolumn']+1 + \
                                     len(lStartStatement[1])+len(s)
                # Start a new line for the actual string
                else:
                    lLines.append(lCurr)
                    lCurr = Layout2d()
                    lCurr.extend(lStartStatement+[s])
                    nCurrentColumn = self['startcolumn']+1 + \
                                     len(lStartStatement[1])+len(s)
                    
            lPostfix = i.GetPostfixAttributes()
            for j in lPostfix:
                if j.__class__==Comment:
                    lCurr.extend([' '*(j.GetLocation()[1]-nCurrentColumn-1),
                                       `j`])
                else:
                    lCurr.append([' %s'%`j`])  # Add at least one space here
        lLines.append(lCurr)
        return lLines
    # --------------------------------------------------------------------------
    def ToList(self, obj, l, bIgnoreAttributes=0):
        if not isinstance(obj, ProgUnit):
            return DefaultStylesheet.ToList(self, obj, l,
                                            bIgnoreAttributes=bIgnoreAttributes)
        
        l2d     = Layout2d()
        obj.ToList(self, l2d)
        for i in l2d:
            l.extend(self.SplitIntoLines( i.lToSimpleList(),
                                          bIgnoreAttributes ) )
        return
          
