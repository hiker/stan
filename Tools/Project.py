#! /usr/bin/env python

import os

from   Tools.Cache    import Cache

# Special work around for the scanner tests: if the scanner tests are
# run from the Scanner subdirectory, the import (in Parser) of Scanner.tools
# does not work, since Scanner is then the local file, not the subdirectory
# Since this can be ignored for the scanner tests (project is only needed
# for include file name resolution), we just 'pass' in case of an error.
try:
    from   Grammar.Parser import Parser
except ImportError:
    pass

class Project:
    dConfig = {}
    dAddFileInfo = {'amip1sst.F'       : {'linelength':132},
                    'landmask.F'       : {'linelength':132},
                    'sstmskgh.F'       : {'linelength':132},
                    'mod_calendar.F90' : {'linelength':132},
                    'cuascn.intfb.h'   : {'format':"free"},
                    'cubasen.intfb.h'  : {'format':"free"},
                    'cubasmcn.intfb.h' : {'format':"free"},
                    'cubidiag.intfb.h' : {'format':"free"},
                    'cuctracer.intfb.h': {'format':"free"},
                    'cuddrafn.intfb.h' : {'format':"free"},
                    'cudlfsn.intfb.h'  : {'format':"free"},
                    'cudtdqn.intfb.h'  : {'format':"free"},
                    'cududvn.intfb.h'  : {'format':"free"},
                    'cududvn.intfb.h'  : {'format':"free"},
                    'cuentrn.intfb.h'  : {'format':"free"},
                    'cuflxn.intfb.h'   : {'format':"free"},
                    'cuinin.intfb.h'   : {'format':"free"},
                    'sucumfn.intfb.h'  : {'format':"free"},
                    'fcttre_new.h'     : {'format':"free", 'linelength':132},
                    'zevpmx.F':          {'linelength':132} }
    def __init__(self,sProject=None):
        self.dConfig        = Project.dConfig
        self.Cache          = Cache(nSize=10, sProject=sProject)
        self.dRecursiveTest = {}
    # --------------------------------------------------------------------------
    def FindFile(self, sFilename):
        sFullName = sFilename
        if os.access(sFullName, os.R_OK):
            return sFullName
        return None
    # --------------------------------------------------------------------------
    # Try to find a (or several) files which (might) contain a certain
    # identifier. For now this subroutine assumes that the identifier
    # is related to the filename, but in the worst case we might have to
    # grep through all (not yet parsed) files to find the one.
    def lGetFilelistForIdentifier(self, sIdentifier, sType):
        if sType=="file":
            return [self.FindFile(sIdentifier)]
        
        # Look for possible Fortran files with 'similar' name
        l=[]
        for i in ["%s","%s.f","%s.F","%s.f90","%s.F90","%s.inc","%s.h",
                  "mod_%s.f","mod_%s.F","mod_%s.f90","mod_%s.F90"]:
            sFilename=i%sIdentifier
            if os.access(sFilename, os.R_OK):
                l.append(sFilename)
        if l: return l
        
        # Now try again with the filename in lower case
        sIdentifier=sIdentifier.lower()
        for i in ["%s","%s.f","%s.F","%s.f90","%s.F90","%s.inc","%s.h",
                  "mod_%s.f","mod_%s.F","mod_%s.f90","mod_%s.F90"]:
            sFilename=i%sIdentifier
            if os.access(sFilename, os.R_OK):
                l.append(sFilename)
        if l: return l
        # We should grep for the symbol in all files next
        return []
        
    # --------------------------------------------------------------------------
    def oGetObjectForIdentifier(self, sIdentifier, sType):
        obj=self.Cache.oGetFile(sIdentifier, sType)
        if obj:
            return obj
        for sFilename in self.lGetFilelistForIdentifier(sIdentifier, sType):
            if not self.dRecursiveTest.get(sFilename,None):
                self.dRecursiveTest[sFilename]=1
                objFile = Parser(sFilename=sFilename, project=self)
                # When a parsing error occurs, none is returned
                if objFile:
                    self.Cache.Store(objFile)
                del self.dRecursiveTest[sFilename]
                if sType=="file":
                    id = objFile
                else:
                    id = objFile.GetIdentifier(sIdentifier, sType)
                if id:
                    return id
        return None
            
    # --------------------------------------------------------------------------
    def dGetFileOptions(self, sFilename):
        d=self.dAddFileInfo.get(sFilename,{})
        return d
# ==============================================================================
