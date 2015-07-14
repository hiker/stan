#!/usr/bin/env python

import string
from types               import StringType
from AOR.AttributeString import AttributeString

class Layout2d:
    def __init__(self, o=None, attribute=None):
        self.Clear()
        if o!=None:
            self.append(o, attribute)
    # --------------------------------------------------------------------------
    def Clear(self):
        # lElements:    Contains the elements, i.e. strings or Layout2d objects
        # lPosX, lPosY: Contains the corresponding x and y positions (using
        #               tuples here would mean a lot of creating and destroying
        #               of tuples when moving strings up or ...
        # dAttributes:  Contains arbitrary 'attributes' for some lElements. It
        #               takes the index in lElements as a key./
        self.lElements   = []
        self.lPosX       = []
        self.lPosY       = []
        self.dAttributes = []
        
        # Geometry of the layout object: width, height, baseline
        self.nBaseline   = 0
        self.nWidth      = 0
        self.nHeight     = 1
        
    # --------------------------------------------------------------------------
    def __len__(self): return self.nWidth
    # --------------------------------------------------------------------------
    def __getitem__(self, n): return self.lElements[n]
    # --------------------------------------------------------------------------
    def __repr__(self): return self.__str__()
    # --------------------------------------------------------------------------
    def __str__(self):
        l = []
        for i in range(self.nHeight):
            l.append("")
        self.__ToStringList(l, xPos=0, yPos=0)
        return "\n".join(l)

    # --------------------------------------------------------------------------
    def __ToStringList(self, l, xPos, yPos):
        for i in range(len(self.lElements)):
            nX = self.lPosX[i]+xPos
            nY = self.lPosY[i]+yPos
            if isinstance(self.lElements[i], Layout2d):
                self.lElements[i].__ToStringList(l, nX, nY)
            else:
                s  = l[nY]
                s="%s%s%s"%(s, " "*(nX-len(s)), self.lElements[i])
                l[nY] = s
        return
    # --------------------------------------------------------------------------
    # A simple layout for 1d lines only, it will flatten the list, and add
    # appropriate spaces for indentation
    def lToSimpleList(self):
        l=[]
        self.__nToSimpleList(l, 0)
        return l
        
    # --------------------------------------------------------------------------
    def __nToSimpleList(self, l, nCurrPos):
        for i in range(len(self.lElements)):
            el = self.lElements[i]
            if isinstance(el, Layout2d):
                nCurrPos = el.__nToSimpleList(l, nCurrPos)
            else:
                if self.lPosX[i]>nCurrPos:
                    l.append(" "*(self.lPosX[i]-nCurrPos))
                    nCurrPos = self.lPosX[i]
                l.append(el)
                nCurrPos = nCurrPos+len(el)
        return nCurrPos
        
    # --------------------------------------------------------------------------
    def MoveDown(self, delta):
        for i in range(len(self.lPosY)):
            self.lPosY[i] = self.lPosY[i]+delta
        self.nBaseline = self.nBaseline + delta
        
    # --------------------------------------------------------------------------
    def MoveRight(self, delta):
        for i in range(len(self.lPosX)):
            self.lPosX[i] = self.lPosX[i]+delta
    # --------------------------------------------------------------------------
    def extend(self, l):
        for i in l:
            self.append(i)
    # --------------------------------------------------------------------------
    def indent(self,n):
        self.nWidth=self.nWidth+n
    # --------------------------------------------------------------------------
    def append(self, o, attribute=None, nIndent = 0, nIndentNext=0):
        self.lElements.append(o)
        self.lPosX.append(self.nWidth+nIndent)
        self.nWidth = self.nWidth + len(o) + nIndent+nIndentNext
        
        if attribute!=None:
            self.dAttributes[len(self.lElements)-1] = attribute
        
        if not isinstance(o, Layout2d):
            self.lPosY.append(self.nBaseline)
            return
        
        # Now it should be an Layout2d type
        # ---------------------------------
        assert isinstance(o, Layout2d)
        
        # The new element is higher than the current object --> move the
        # existing elements down to make space for the new element
        delta = o.nBaseline -self.nBaseline
        if delta>0:
            self.MoveDown(delta)
            self.lPosY.append(0)
        else:
            # Otherwise position the new elements so that the baselines are
            # at the same height
            self.lPosY.append(-delta)

        self.nHeight = self.nBaseline + \
                       max(self.nHeight-self.nBaseline, o.nHeight-o.nBaseline)
    # --------------------------------------------------------------------------
    # Split the current representation into blocks not wider then nMax.
    # nIndent can be specified to indicate the inde
    def sSplitIntoLines(self, nMax, nIndent = None, nAddIndent=2):
        l = []
        for i in range(self.nHeight):
            l.append("")
        self.__ToStringList(l, xPos=0, yPos=0)
        nMaxLineLength = max(map(lambda x: len(x), l))
        
        for i in range(len(l)):
            l[i]="%s%s"%(l[i], " "*(nMaxLineLength-len(l[i])))

        # First compute the indentation used (if not specified as parameter)
        # ------------------------------------------------------------------
        if nIndent==None:
            nIndent = 999
            # Maybe it is sufficient to only consider the baseline to
            # determine the indentation???
            for i in range(len(l)):
                j=0
                while j<len(l[i]) and l[i][j]==" ":
                    j=j+1
                if nIndent>j: nIndent=j

        # Compute the number of lines
        # ---------------------------
        nEffective = nMax - nIndent - nAddIndent
        nLines = (self.nWidth - nIndent) / nEffective
        if nLines*nEffective < self.nWidth - nIndent:
            nLines = nLines+1

        # Now compute the splitting point for each line - we don't
        # have to do the last line, since it will automatically fit
        # ---------------------------------------------------------
        nPosY = 0
        nPos  = nIndent
        self.Clear()
        for i in range(nLines-1):
            nPosMax = nPos + nEffective - 1
            # We must make sure that we have enough contents in this line so
            # that the remaining lines can still be squeezed into the remaining
            # space for the remaining lines. E.G.: consider nIndent=0,
            # s = "aabbcc", nMax=4 --> two lines must be created, and we have
            # to have at least 2 elements in the first line, otherwise (e.g.
            # only 1 element), there would be 5 elements left for the last
            # line, which cant fit in (and would force another line break)
            nPosMin = self.nWidth - (nLines-1 - i) * nEffective
            # Now find the best position to split the string
            nBest = self.FindBestSplit(l, nPosMin, nPosMax)+1
            #print nEffective, nPos, nPosMin, nPosMax, self.nWidth, nIndent, nMax, nLines, i,"-->",nBest
            if i==0:
                nIndentLines = nIndent
            else:
                nIndentLines = nIndent+nAddIndent
            for i in l:
                self.lElements.append(i[nPos:nBest])
                self.lPosX.append(nIndentLines)
                self.lPosY.append(self.nHeight-1)
                self.nHeight = self.nHeight+1
                if nBest-nPos+1 + nIndentLines>self.nWidth:
                    self.nWidth = nBest-nPos+1+nIndentLines
            self.nHeight = self.nHeight + 1
            nPos = nBest
        nIndentLines = nIndent+nAddIndent
        for i in l:
            self.lElements.append(i[nPos:])
            self.lPosX.append(nIndentLines)
            self.lPosY.append(self.nHeight-1)
            self.nHeight = self.nHeight+1
            if len(i)-nPos+1 + nIndentLines>self.nWidth:
                self.nWidth = len(i)-nPos+1+nIndentLines
            
    # -------------------------------------------------------------------------
    def FindBestSplit(self, l, nPosMin, nPosMax):
        nBest      = nPosMax
        nBestScore = 0
        for i in range(nPosMax-1, nPosMin, -1):
            nScore = 0
            for sLine in l:
                if sLine[i]==" ":
                    nScore = nScore + 2
                elif sLine[i]==",":
                    nScore = nScore + 1
            # Shortcut if a column with only spaces
            if nScore==2*len(l): return i
            if nScore > nBestScore:
                nBestScore = nScore
                nBest = i
        return nBest
# ==============================================================================
# Special class to display an exp function
class Exp2d(Layout2d):
    def __init__(self, o=None):
        Layout2d.__init__(self)
        if o:
            self.append(o)
            self.exp()
    # --------------------------------------------------------------------------
    def power(self, obj):
        self.append("^")
        self.MoveDown(obj.nHeight)
        self.lElements.append(obj)
        self.lPosX.append(self.nWidth)
        self.lPosY.append(0)
        self.nWidth    = self.nWidth  + obj.nWidth
        self.nHeight   = self.nHeight + obj.nHeight
            
    # --------------------------------------------------------------------------
    def exp(self):
        self.MoveRight(2)
        self.lElements = ["e^"        ] + self.lElements
        self.lPosX     = [0           ] + self.lPosX
        self.lPosY     = [self.nHeight] + self.lPosY
        self.nWidth    = self.nWidth  + 3
        self.nHeight   = self.nHeight + 1
        self.nBaseline = self.nHeight - 1
            
# ==============================================================================
class Division2d(Layout2d):
    def __init__(self, o=None):
        Layout2d.__init__(self, o=o)
    # --------------------------------------------------------------------------
    # Adds a division
    def over(self, x):
        nNewWidth    = max(len(x), self.nWidth)+2
        
        # Center old elements
        # -------------------
        delta = (nNewWidth-self.nWidth)/2
        self.MoveRight(delta)

        self.nWidth = nNewWidth
        self.lElements.append("-"*self.nWidth)
        self.lPosX.append(0)
        self.lPosY.append(self.nHeight)
        
        self.lElements.append(x)
        self.lPosX.append((nNewWidth-len(x))/2)
        self.lPosY.append(self.nHeight+1)

        self.nBaseline = self.nHeight
        if isinstance(x, Layout2d):
            self.nHeight = self.nHeight + 1 + x.nHeight
        else:
            self.nHeight = self.nHeight + 2
    
# ==============================================================================
# A layout object that can display a square root
class Sqrt2d(Layout2d):
    def __init__(self, o=None):
        Layout2d.__init__(self)
        if o:
            self.append(o)
            self.sqrt()
    # --------------------------------------------------------------------------
    # Adds a sqrt:
    #  +---+    or   +---+
    # \| a           | a |
    #              \ | -
    #               \| b
    def sqrt(self):
        sLine = "+%s+"%("-"*(self.nWidth+2))
        if self.nHeight==1:
            l     = [sLine]+["\|"]
            lPosX = [1,     0]
            lPosY = [0,     1]
            dx    = 3
        else:
            l     = [sLine]+["|"]*(self.nHeight-2)+["\ |","\|"]
            lPosX = [2]    +[2  ]*(self.nHeight-2)+[0    ,1   ]
            lPosY = range(self.nHeight+1)
            dx    = 4

        self.MoveDown(1)
        self.MoveRight(dx)
        self.lElements = l     + self.lElements
        self.lPosX     = lPosX + self.lPosX
        self.lPosY     = lPosY + self.lPosY
        if self.nHeight>1:
            self.lElements.append("|")
            self.lPosX.append(self.nWidth+5)
            self.lPosY.append(1)
        self.nHeight   = self.nHeight   + 1
        self.nWidth    = self.nWidth    + dx + 2

# ==============================================================================
# A layout object that can display an abs-value: |x|
class Abs2d(Layout2d):
    def __init__(self, o=None):
        Layout2d.__init__(self)
        if o:
            self.append(o)
            self.sqrt()
    # --------------------------------------------------------------------------
    # Adds a sqrt:
    # | a |
    def abs(self):
        self.MoveRight(1)
        for i in range(self.nHeight):
            self.lElements.insert(0, "|")
            self.lPosX.insert(0, 0)
            self.lPosY.insert(0, i)
            self.lElements.append("|")
            self.lPosX.append(self.nWidth+1)
            self.lPosY.append(i)
        self.nWidth    = self.nWidth + 2
        return

# ==============================================================================
# A special layout2d class, where each entry is on a new line
class MultiLine2d(Layout2d):
    def __init__(self):
        Layout2d.__init__(self)
        self.nHeight = 0
    # --------------------------------------------------------------------------
    def append(self, o, attribute=None, nIndent = 0, nIndentNext = 0):
        # Add one empty line at top for real multi-line objects
        if isinstance(o, Layout2d) and o.nHeight>1:
            o.MoveDown(1)
            o.nHeight = o.nHeight + 1
        self.nWidth = max(self.nWidth, len(o))
        self.lElements.append(o)
        self.lPosX.append(0)
        self.lPosY.append(self.nHeight)
        if type(o) is StringType or type(o) is AttributeString:
            self.nHeight = self.nHeight + 1
        else:
            self.nHeight = self.nHeight + o.nHeight
            # Leave one empty line at the bottom
            # for real multi-line objects:
            if o.nHeight>1:
                self.nHeight = self.nHeight + 1
    
        
# ==============================================================================

if __name__=="__main__":
    l = Division2d("x")
    l.over("y")
    l.append(" + b")
    p = Exp2d()
    p.append(l)
    p.power(l)
    print p
    import sys
    sys.exit()
    l.over("z")
    print l
    print "+"*30
    ls = Sqrt2d("a")
    lexp = Exp2d(ls)
    print lexp
    print "+"*30
    l.append(" + ")
    l.append(lexp)
    l2 = Sqrt2d()
    l2.append("a + ")
    l2.append(l)
    print l2
    print "+"*30
    l2.sqrt()
    print l2
    print "+"*30
    l3=Layout2d("x + ")
    l3.append(l2)
    print l3
    print "+"*30
