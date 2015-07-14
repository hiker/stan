#! /usr/bin/env python

import MySQLdb
import cPickle
import string

class Database:

    DBconnect = None
    def __init__(self, sProject, sDatabase="stan", sUser="joh"):
        if not Database.DBconnect:
            try:
                Database.DBconnect = MySQLdb.connect(db=sDatabase, user=sUser)
                self.cursor        = Database.DBconnect.cursor()
            except:
                Database.DBconnect = None
        self.sProject = sProject
    # --------------------------------------------------------------------------
    # Simple mysql interface
    def __getitem__(self, sKey):
        if not Database.DBconnect: return []
        self.cursor.execute(sKey)
        return self.cursor.fetchall()
    # --------------------------------------------------------------------------
    def RemoveFile(self, oFile):
        d={}
        for unit in oFile:
            sType = unit.sGetType()
            sName = unit.sGetName()
            lIds  = self["SELECT fileid FROM entity WHERE name='%s' AND type='%s'" % 
                         (sName, sType)]
            for j in lIds:
                d[j]= (sType, sName)
        if len(d)>1:
            print "Identical program units:"
            print d
            print "Will all be removed"
            
        for id, (sType, sName) in d.items():
            self["DELETE FROM entity WHERE name='%s' AND type='%s'" %
                 (sName, sType)]
            print "Removing entity sName=%s, sType=%s, fileid=%s"%(sName, sType,id)
        for id in d.keys():
            self["DELETE FROM file WHERE fileid=%d"%id]
            print "Removing fileid=%d"%id
            
        self["DELETE FROM file WHERE path='%s'"%oFile.sGetFilename()]
    # --------------------------------------------------------------------------
    def AddFile(self, oFile):
        if not Database.DBconnect: return
        # For now: no versioning, remove old file
        self.RemoveFile(oFile)
        # Now insert the file first to get the fileid:
        s = string.replace(cPickle.dumps(oFile), '\\', "\\\\")
        s = string.replace(s,                    "'",  "\\'" )
        try:
            self["INSERT INTO file (path, object, date, status, version) VALUES ('%s','%s',Null,'ok','0.0')"%
                 (oFile.sGetFilename(), s)]
        except:
            print "Error when trying to write object to database", oFile.sGetFilename()
            print "INSERT INTO file (path, object, date, status, version) VALUES ('%s','%s',Null,'ok','0.0')"% (oFile.sGetFilename(), s)
            #print "s=",s
            fid = -1
        else:
            fid=self.cursor.insert_id()
        
        # Now add all program units:
        for unit in oFile:
            sType = unit.sGetType()
            sName = unit.sGetName()
            if sType!="incompleteprogunit":
                self["INSERT INTO entity (name, type, fileid) VALUES('%s','%s',%d)"%
                     (sName, sType, fid)]
    # --------------------------------------------------------------------------
    def oGetFile(self, sIdentifier, sType):
        if sType=="file":
            r=self["SELECT object,date FROM file WHERE path='%s'"% sIdentifier]
        else:
            r=self["SELECT object,date FROM file, entity WHERE name='%s' AND type='%s' AND file.fileid=entity.fileid"% (sIdentifier, sType)]

        if not r:
            return None

        # Ignore the date for now
        if len(r)!=1:
            print "Warning, r=",r
        print "Returning database file for",sIdentifier, sType
        objFile=cPickle.loads(r[0][0])
        if sType=="file": return objFile
        return objFile

    # --------------------------------------------------------------------------
    
# ==============================================================================
class HasDatabase:
    def __init__(self, sProject):
        self.DB = Database(sProject)
# ==============================================================================
        
        
