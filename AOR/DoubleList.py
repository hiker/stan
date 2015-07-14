#!/usr/bin/env python

from AOR.AttributeString import AttributeString

# This object stores a 'double list', i.e. a list of objects, but
# with a string between each object. Example: "a,b,c" - the objects
# a, b, and c are the main objects of the list, while the two commas
# are stored as well. 2nd example "a+b-c".
# This object assumes that either:
# - the first list has one more entries than the second list. This can be
#   done by either:
#   1) Adding first a single element: dl.append('a')
#      and then adding the string separator followed by a second object,e.g.:
#      dl.append('+','b'), dl.append('-','c')    or
#   2) Adding first two elements: dl.append('a','+'), dl.append('b','-')
#      and then adding at last a single element: dl.append('c')
# - or both lists have the same number of elements, in which case the last
#   string element will be added to the end, e.g.:
#   'a,b,c,'
# The object will discover how it is used and handle appending the elements
# correctly.

from types import StringType, ListType

class DoubleList:

    # Constructor. 
    def __init__(self, l1=None, l2=None):
        if l1:
            if type(l1) is ListType:
                self.l1 = l1
            else:
                self.l1 = [l1]
        else:
            self.l1 = []
        if l2:
            if type(l2) is ListType:
                self.l2 = l2
            else:
                self.l2 = [l2]
        else:
            self.l2 = []
    # --------------------------------------------------------------------------
    # This must distinguish the two above described cases
    def append(self, e1, e2=None):
        if not e2:
            # This simplifies creating statements manually, since the
            # , does not have to be added, (e.g. addVar(a), addVar(b)
            # --> the , between say call(a,b) will be added automatically)
            if len(self.l1)-1==len(self.l2):
                self.l1.append(e1)
                self.l2.append(",")
            else:
                self.l1.append(e1)
            return
        if len(self.l1)==len(self.l2):
            self.l1.append(e1)
            self.l2.append(e2)
        else:
            self.l2.append(e1)
            self.l1.append(e2)
    # --------------------------------------------------------------------------
    # Returns the 'main' list: l1
    def GetMainList(self): return self.l1
    # --------------------------------------------------------------------------
    def lGetSecondaryList(self): return self.l2
    # --------------------------------------------------------------------------
    # Returns the number of elements in the main list, i.e. l1
    def __len__(self): return len(self.l1)
    # --------------------------------------------------------------------------
    def __getitem__(self, n): return self.l1[n]
    # --------------------------------------------------------------------------
    def lGetAsSimpleList(self):
        l = []
        n = len(self.l1)
        if n==0: return []
        # Handle everything except the last element
        for i in range(n-1):
            l.append(self.l1[i])
            l.append(self.l2[i])
            
        # Add the last element
        l.append(self.l1[n-1])
        # Add the corresponding element from the 2nd list if it exists
        if len(self.l2)==n:
            l.append(self.l2[n-1])
        return l
    # --------------------------------------------------------------------------
    def ToList(self, stylesheet, l, bAddSpace=None):
        n = len(self.l1)
        if n==0:
            return
        if self.l1[0]:
            stylesheet.ToList(self.l1[0], l)

        #if type(lTemp) is StringType:
        #    l=[lTemp]
        #else:
        #    l = lTemp
        #print "doublelist",self.l1,self.l2
        if bAddSpace:
            nIndent = 1
        else:
            nIndent = 0
        for i in range(1,len(self.l1)):
            l.append(self.l2[i-1])
            if self.l1[i]:
                l.indent(nIndent)
                stylesheet.ToList(self.l1[i], l)
        if len(self.l1)==len(self.l2):
            l.indent(nIndent)
            stylesheet.ToList(self.l2[-1], l)
    # --------------------------------------------------------------------------
    def __repr__(self):
        return "%sx%s"%(`self.l1`, `self.l2`)
    
# ==============================================================================

if __name__=="__main__":
    from AOR.Test.ListTest import RunAllTests
    RunAllTests()
        
