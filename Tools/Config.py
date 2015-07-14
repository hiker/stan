#!/usr/bin/env python

import string

# This object stores all global configuration, especially about output
# formats. Supported attributes:
#
# labelalignright : if labels should be right aligned (1) or left aligned
# maxcols         : number of columns per line
# indent          : first column to use for statements (must be at least 7
#                   for (valid) fixed format, can be anything for free)
# keywordcase     : if keywords (subroutine, for, do, ...) are written in
#                   upper-case, lower-case, or capitalized. This attribute
#                   should not be used directly, instead the method
#                   sKeyword(string) should be used.
# spacebetweencommalist: if a space is put between 'a,b,c' or not
# startcolumn     : first column to use for statements (must be at least 7
#                   for (valid) fixed format, can be anything for free)
# variablecase    : if variables are written in upper-case, lower-case, or
#                   capitalized. This should never be used directly, instead
#                   the method sVariable(string) should be used.


class Config:
    # Class attribut with all general (i.e. not format specific)
    # attributes
    dDefault = { 'stylesheet' : {'labelalignright'      : 1,
                                 'indent'               : 3,
                                 'keywordcase'          : 'upper',
                                 'variablecase'         : 'lower',
                                 'contlinemarker'       : '&',
                                 'spacebetweencommalist': 1,
                                 'format'               : 'fixed',
                                 'maxcols'              : {'fixed' : 72, 'free' : 132},
                                 'startcolumn'          : {'fixed' :  7, 'free' :   1},
                                 },
                 'files'      : {'amip1sst.F': {'linelength':132},
                                 'landmask.F': {'linelength':132},
                                 'sstmskgh.F': {'linelength':132},
                                 'zevpmx.F'  : {'linelength':132}
                                 },
                 'project'    : {'paths'     : [".","whatever/directory"]
                                 },
                 }

    # Special character used to separate entries for dictionary in dict in ...
    # e.g.: "project|paths" instead of ["project"]["path"]
    sSeparatorChar = "|"
    
    # The actual configuration information (as a class variable)
    dConfig        = {}
    # --------------------------------------------------------------------------
    # Init: save the config filename and read the config file
    def __init__(self, sConfigFilename="stanrc"):
        if not Config.dConfig:
            Config.sConfigFilename=sConfigFilename
            self.GetConfig()

    # -------------------------------------------------------------------------
    def GetConfig(self):
        # Try reading the config file. If it doesn't exist (or any other
        # error occurs), get the default values
        try:
            f=open(Config.sConfigFilename,'r')
            l=f.readlines()
            f.close()
            s="\n".join(l)
            Config.dConfig=eval(s)
        except IOError:
            Config.dConfig = Config.dDefault.copy()
            self.WriteConfigFile()
            
    # -------------------------------------------------------------------------
    # Save the config dictionary
    def WriteConfigFile(self):
        try:
            f=open(Config.sConfigFilename,'w')
        except IOError:
            print "Couldn't open",Config.sConfigFilename
            return
        f.write(`Config.dConfig`)
        f.write("\n")
        f.close()
        
    # -------------------------------------------------------------------------
    # Access to the configuration data via a dictionary like interface.
    # As a shortcut, one can use "|" (see sSeparatorChar) to divide several
    # nested dictionaries, i.e. ["a|b|c"] instead of ["a"]["b"]["b"]
    def __getitem__(self, sKey):
        l = sKey.split(Config.sSeparatorChar)
        d = Config.dConfig
        for i in l:
            d=d.get(i,None)
            if not d:
                return None
        return d
    # -------------------------------------------------------------------------
    # Set configuration data via a dictionary like interface.
    # As a shortcut, one can use "|" (see sSeparatorChar) to divide several
    # nested dictionaries, i.e. ["a|b|c"]=1 instead of ["a"]["b"]["b"]=1
    def __setitem__(self, sKey, value):
        l = sKey.split(Config.sSeparatorChar)
        d = Config.dConfig
        # Follow the tree:
        for i in range(len(l)-1):
            d1=d.get(l[i],None)         # goto next dictionary
            # Create new entry for all remaining entries
            if not d1:
                for j in range(i, len(l)-1):
                    d[l[j]] = {}
                    d       = d[l[j]]
                d[l[-1]] = value
                self.WriteConfigFile()  # save the modified config file
                return
            d=d1
        d[l[-1]] = value

        self.WriteConfigFile()          # save the modified config file
          
# ==============================================================================
# A simple wrapper object which defines an attribute 'config' which stores
# all configuration information.
class HasConfig:
    def __init__(self):
        self.config = Config()
# ==============================================================================
if __name__=="__main__":
    c=Config()
