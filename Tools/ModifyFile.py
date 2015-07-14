#!/usr/bin/env python

# A very simple interface to modify a fortran file. Statements can be removed,
# or lines can be inserted after (or before) a certain statement, and the
# resulting file can then be written back. Except for the modifications the
# file will look identical to the original file, i.e. no layout changes or
# anything. Example:
#    modify = ModifyFile(oFile.sGetFilename())
#    modify.AddLine("IMPLICIT NONE", lastStatement
#    modify.RemoveStatement(implicitStatement)
#    modify.WriteBack(oFile.sGetFilename()+".none")

class ModifyFile:

    def __init__(self, sFilename):
        self.sFilename = sFilename
        try:
            f = open(sFilename,"r")
        except IOError:
            print "File '%s' does not exist"%self.sFilename
            return
        self.lLines = f.readlines()
        f.close()
        self.lModifications = []
        self.bIsModified    = 0
        self.nCount         = 0
    # --------------------------------------------------------------------------
    def WriteBack(self, sNewFilename):
        if self.bIsModified:
            self.Modify()
        f = open(sNewFilename,"w")
        for i in self.lLines:
            f.write(i)
        f.close()
        
    # --------------------------------------------------------------------------
    def Modify(self):
        # The removals/insertions have to be done from the end of the file to
        # the beginning, otherwise the line numbers would be all wrong
        self.lModifications.sort()
        self.lModifications.reverse()
        for (nLineFrom, nLineTo, nCount, o) in self.lModifications:
            if o[0]=="delete":
                del self.lLines[nLineFrom-1:nLineTo]
            elif o[0]=="insert":
                self.lLines.insert(nLineFrom, o[1])
        self.bIsModified = 0
    # --------------------------------------------------------------------------
    def AddLine(self, sLine, objBefore=None, objAfter=None):
        if objBefore:
            nLine = objBefore.GetLocation()[0]-1
        else:
            # Get a 'before' line number - the lines returned by getlocation
            # start at line #1, the index here in the list starts with 0
            nLine = objAfter.GetEndLocation()[0]
        # Append the instructions. To guarantee that the insertions are done
        # in the same order in which AddLine is called, a count value is added
        # to the tuple. Since the list of modifications will later be sorted,
        # this will guarantee that the statements are added in the right order.
        self.lModifications.append( (nLine, nLine,self.nCount,
                                     ("insert",sLine+"\n") ) )
        self.nCount=self.nCount + 1
        self.bIsModified = 1
    # --------------------------------------------------------------------------
    def RemoveStatement(self, objStatement):
        lLineFrom = objStatement.GetLocation()[0]
        lLineTo   = objStatement.GetEndLocation()[0]
        self.lModifications.append( (lLineFrom, lLineTo,
                                     self.nCount,("delete",) ) )
        self.nCount=self.nCount+1
        self.bIsModified = 1
# ==============================================================================

if __name__=="__main__":
    pass
    
