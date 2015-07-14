#!/usr/bin/env python

# This implements a string which can additionally contains  attributes
# (i.e. arbitrary objects). This is used to attach special tokens
# to other tokens, e.g. a comment is attached to the previous token, ...
# E.g. a Fortran line like  "a=b  ! assignment"  would return
# a token 'b' with the attribute Comment("! assignment") as a postfix
# attribute. Or:
# !cdir concur
# do i=1, n
# The token for 'do' would contain the prefix attribute
# CompilerDirectice("!cdir concur")

from types        import ListType

class AttributeString(str):
    def __init__(self, s):
        str.__init__(self, s)
        # If this object is initialised with an AttributeString,
        # copy the attributes as well
        if isinstance(s, AttributeString):
            self.lPrefix  = s.GetPrefixAttributes()[:]
            self.lPostfix = s.GetPostfixAttributes()[:]
        else:
            self.lPrefix  = []
            self.lPostfix = []
    # --------------------------------------------------------------------------
    # Creates a new attribute string which has the same pre- and postfix
    # attributes, but a new string.
    def sCreateCopy(self, s):
        new = AttributeString(s)
        new.SetPrefixAttributes(self.GetPrefixAttributes())
        new.SetPostfixAttributes(self.GetPostfixAttributes())
        return new
    # --------------------------------------------------------------------------
    # Splits an AttributeString into two strings, the first one containing
    # all prefix attributes, the second one all postfix ones. The parameter
    # n specified the number of character to for the first string.
    def tSplitString(self, n):
        s1 = AttributeString(self[0:n])
        s2 = AttributeString(self[n: ])
        s1.SetPrefixAttributes(self.GetPrefixAttributes())
        s2.SetPostfixAttributes(self.GetPostfixAttributes())
        return s1,s2
    # --------------------------------------------------------------------------
    def SetPrefixAttributes(self,  l) : self.lPrefix = l[:]
    # --------------------------------------------------------------------------
    def SetPostfixAttributes(self, l) : self.lPostfix = l[:]
    # --------------------------------------------------------------------------
    def AppendPrefix(self,  o):
        if type(o)==ListType:
            self.lPrefix.extend(o)
        else:
            self.lPrefix.append(o)
    # --------------------------------------------------------------------------
    def AppendPostfix(self, o):
        if type(o)==ListType:
            self.lPostfix.extend(o)
        else:
            self.lPostfix.append(o)
    # --------------------------------------------------------------------------
    def GetPrefixAttributes(self ): return self.lPrefix
    # --------------------------------------------------------------------------
    def GetPostfixAttributes(self): return self.lPostfix
    # --------------------------------------------------------------------------
    def GetString(self): return str.__str__(self)
    # --------------------------------------------------------------------------
    # We have to overwrite this method so that a new AttributeString is
    # returned!
    def upper(self):
        return self.sCreateCopy(str.__str__(self).upper())
    # --------------------------------------------------------------------------
    # We have to overwrite this method so that a new AttributeString is
    # returned!
    def lower(self):
        return self.sCreateCopy(str.__str__(self).lower())
    # --------------------------------------------------------------------------
    # We have to overwrite this method so that a new AttributeString is
    # returned!
    def capitalize(self):
        return self.sCreateCopy(str.__str__(self).capitalize())
    # --------------------------------------------------------------------------
    #def ToList(self, stylesheet, l): return l.append(str.__str__(self))
    def ToList(self, stylesheet, l): return l.append(self)
    # --------------------------------------------------------------------------
    #def __repr__(self): return str.__str__(self)
    # Debug: output an attribute string with all attributes
    def __repr__(self):
        return "%s-%s-%s"%(`self.lPrefix`,str.__str__(self),`self.lPostfix`)

