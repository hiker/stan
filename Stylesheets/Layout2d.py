#!/usr/bin/env python

from types               import StringType
from AOR.AttributeString import AttributeString

class Layout2d:
    def __init__(self, o=None, attribute=None):
        # lElements: Contains the elements, i.e. strings or Layout2d objects
        # lPosX, lPosY: Contains the corresponding x and y positions (using tuples
        #               here would mean a lot of creating and destroying of tuples
        #               when moving strings up or ...
        # dAttributes: Contains arbitrary 'attributes' for some lElements. It's
        #              takes the index in lElements as a key./
        self.lElements   = []
        self.lPosX       = []
        self.lPosY       = []
        self.dAttributes = []
        
        # Geometry of the layout object: width, height, baseline
        self.nBaseline   = 0
        self.nWidth      = 0
        self.nHeight     = 1
        if o!=None:
            self.append(o, attribute)
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
        self.__ToString(l, xPos=0, yPos=0)
        return "\n".join(l)

    # --------------------------------------------------------------------------
    def __ToString(self, l, xPos, yPos):
        for i in range(len(self.lElements)):
            nX = self.lPosX[i]+xPos
            nY = self.lPosY[i]+yPos
            if isinstance(self.lElements[i], Layout2d):
                self.lElements[i].__ToString(l, nX, nY)
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
        #print "adding",o,self.nWidth, o, nIndent, nIndentNext, self.lElements, self.lPosX
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
            # Leave one empty line at the bottom and top
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
