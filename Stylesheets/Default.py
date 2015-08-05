#!/usr/bin/env python

import string
from   types                import ListType, StringType
from   Tools.Config         import HasConfig
from   AOR.DoubleList       import DoubleList
from   Stylesheets.Layout2d import Layout2d, MultiLine2d

# This object represents a stylesheet. It is used for
# 1) storing general layout attributes (e.g. if keywords should be
#    capitalized, ...), which can (and should) be used by all stylesheets
# 2) Allow implementation of different styles by overwriting only methods
#    which needs to be changed - hopefully :)
#
# The following keywords are currently supported:
class DefaultStylesheet(HasConfig):
    dCase2Function = {'upper'          : string.upper,
                      'lower'          : string.lower,
                      'identical'      : lambda x:x,
                      'capitalized'    : string.capitalize}


    # --------------------------------------------------------------------------
    def __init__(self, sFormat='fixed'):
        HasConfig.__init__(self)
        self.dMyConfig       = self.config['stylesheet'].copy()
        # The original structure is
        # Config['startcolumn']={'fixed': ..., 'free':...}
        # Since this is somewhat complicated to handle, the structure
        # for the stylesheets is changed so that the format is not
        # used anymore.
        self['startcolumn' ] = self['startcolumn'][self["format"]]
        self['maxcols'     ] = self['maxcols'    ][self["format"]]
        self['keywordcase' ] = "upper"
        self['variablecase'] = "lower"

    # -------------------------------------------------------------------------
    def get(self, sKey, default=None):
        return self.dMyConfig.get(sKey, default)
   # -------------------------------------------------------------------------
    def __getitem__(self, sKey):
        try:
            return self.dMyConfig[string.lower(sKey)]
        except KeyError:
            return None
    # -------------------------------------------------------------------------
    def __setitem__(self, sKey, value):
        sKey=sKey.lower()
        self.dMyConfig[sKey] = value
        if sKey=="keywordcase":
            self.dMyConfig['keywordcase' ] = self.dCase2Function.get(value,
                                                                     lambda x:x)
        elif sKey=="variablecase":
            self.dMyConfig['variablecase'] = self.dCase2Function.get(value,
                                                                     lambda x:x)
    # -------------------------------------------------------------------------
    # Creates the correct capitalisation for a keyword (i.e. upper case, lower
    # case, .... Parameters:
    #
    # s -- The keyword 
    def sKeyword(self, s): return self['keywordcase'](s)
    # -------------------------------------------------------------------------
    # Creates the correct capitalisation (or whatever) for a variable name
    def sVariable(self, s): return self['variablecase'](s)
    # -------------------------------------------------------------------------
    def GetIndentation(self, statement):
        return (" "*self['indent']) * (statement.GetIndentation()-1)
    # -------------------------------------------------------------------------
    # Returns the right amount of spaces, so that a character following
    # these spaces will be on the first column defined in this stylesheet.
    def sGetStartColumnSpaces(self):
        return ' '*(self['startcolumn']-1)
    # -------------------------------------------------------------------------
    # Converts an object to a list of strings (and lists). This basically calls
    # ToList in the object, but by overwriting this method different layout
    # functions can be used.
    def ToList(self, obj, l, bIgnoreAttributes=0):
        if type(obj)==StringType:
            l.append(obj)
        elif type(obj)==ListType:
            l.append(obj)
        else:
            obj.ToList(self, l)
    # -------------------------------------------------------------------------
    # Split a line into several lines if necessary. This needs to be
    # overwritten by the stylesheets.
    def SplitIntoLines(self, l, bIgnoreAttributes=0):
        return [l]
    # -------------------------------------------------------------------------
    # Takes the result of a ToList call and returns a string representation.
    def ToString(self, obj, bIgnoreAttributes=0):
        # *sigh* It's definitively not nice to import here, but otherwise
        # we have a circular reference:
        # BasicStatement -> Default -> File -> BasicStatement :((((
        from AOR.File           import File
        from AOR.ProgUnit       import ProgUnit
        from AOR.BasicStatement import BasicStatement
        from   Tools.functions  import flatten
        # We have to handle a few special cases:
        # 1) Displaying a progam unit: a program unit is a list of
        #    statements, i.e. a list of [list representing the statement]
        #    We have to convert each [list representing the statement] to a
        #    string, and then concatenate this list of strings with newlines
        # 2) Displaying a file: a file is a list of subroutines (which is a list
        #    of list of (strings and list), see above).
        if isinstance(obj, ProgUnit) or obj.__class__==File:
            l = MultiLine2d()
            self.ToList(obj, l, bIgnoreAttributes=bIgnoreAttributes)
            return `l`
        # 3) otherwise, we have (at most) a complete statement, so the
        #    list can be flattened and all strings then concatenated.
        elif isinstance(obj, BasicStatement):
            l = Layout2d()
            #l = MultiLine2d()
            self.ToList(obj, l, bIgnoreAttributes=bIgnoreAttributes)
            l1 = self.SplitIntoLines(l.lToSimpleList(), 
                                     bIgnoreAttributes=bIgnoreAttributes)
            l=[]
            for i in l1:
                l.append("".join(i))
            return "\n".join(l)
        else:
        # 4) Simple expressions etc., which all go on a single line, no newline
            l = Layout2d()
            self.ToList(obj, l, bIgnoreAttributes=bIgnoreAttributes)
            return `l`
    # -------------------------------------------------------------------------
          
