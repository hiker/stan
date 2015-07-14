#! /usr/bin/env python

import os

class Cache:
    def __init__(self, nSize=10, sProject=""):
        try:
            from Tools.Database import Database
            self.DB=Database(sProject)
        except:
            self.DB=None
            
        self.nSize  = nSize
        # lCache contains pointers to the objects, and is used to implement
        # a last recently used strategy
        # dcache is used to find the information quickly.
        self.lCache = []
        self.dCache = {}
    # --------------------------------------------------------------------------
    def DeleteFile(self, oFile):
        if self.dCache.get(oFile.sGetFilename(), None) == None: return
        for i in range(len(self.lCache)):
            if self.lCache[i]==oFile:
                print "Deleting '%s' from cache"%oFile.sGetFilename()
                del self.lCache[i]
                del self.dCache[oFile.sGetFilename()]
                return
    # --------------------------------------------------------------------------
    def Store(self, oFile, bNoDBUpdate=0):
        sFilename = oFile.sGetFilename()
        nCount    = 0
        oldObj    = self.dCache.get(sFilename, None)
        if oldObj:
            for i in self.lCache:
                if i == oldObj:
                    self.lCache[nCount   ] = oFile
                    self.dCache[sFilename] = oFile
                    break
                nCount=nCount + 1
        else:
            # Otherwise put the file into the cache list
            while len(self.lCache)>=self.nSize:
                print len(self.lCache), self.nSize
                nOldLen = len(self.lCache)
                self.DeleteFile(self.lCache[-1])
                if nOldLen==len(self.lCache):
                    print "Deadloch, last entry not removed",nOldLen,len(self.lCache)
                    print "lCache:"
                    for i in self.lCache:
                        print i.sGetFilename()
                    print "dCache:"
                    for i,j in self.dCache.items():
                        print i,j.sGetFilename()
                    import sys
                    sys.exit(-1)
            self.dCache[sFilename]=oFile
            self.lCache = [oFile] + self.lCache

        # Now remove a previously existing copy from the datbase backend
        if not bNoDBUpdate and self.DB:
            self.DB.AddFile(oFile)
        
    # --------------------------------------------------------------------------
    def oGetFile(self, sIdentifier, sType):
        # First check the cache
        if sType=="file":
            oFile = self.dCache.get(sIdentifier, None)
            if oFile!=None:
                print "Returning %s from cache, moving to front of list"%sIdentifier
                # Well, some overhead here, but easy to implement :)
                self.DeleteFile(oFile)
                self.Store(oFile, bNoDBUpdate=1)
                return self.lCache[n]
        else:
            for oFile in self.lCache:
                o = oFile.GetIdentifier(sIdentifier, sType)
                if o:
                    print "Returning '%s' of type '%s' from cache, moving to front of list"%\
                          (sIdentifier, sType)
                    self.DeleteFile(oFile)
                    self.Store(oFile, bNoDBUpdate=1)
                    return o
        # Now try to get the object from the database backend
        if self.DB:
            oFile =  self.DB.oGetFile(sIdentifier, sType)
        if self.DB and oFile:
            if sType=="file":
                o = oFile
            else:
                o = oFile.GetIdentifier(sIdentifier, sType)
            print "Returning '%s' from database, storing in cache"%sIdentifier
            self.DeleteFile(oFile)
            self.Store(oFile, bNoDBUpdate=1)
            return o
        return None

# ==============================================================================

if __name__=="__main__":
    print "You can't run Cache directly"
