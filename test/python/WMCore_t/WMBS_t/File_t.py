#!/usr/bin/env python
"""
_File_t_

Unit tests for the WMBS File class.
"""

__revision__ = "$Id: File_t.py,v 1.11 2009/01/08 22:00:21 sfoulkes Exp $"
__version__ = "$Revision: 1.11 $"

import unittest
import logging
import os
import commands
import threading
import random
from sets import Set

from WMCore.Database.DBCore import DBInterface
from WMCore.Database.DBFactory import DBFactory
from WMCore.DAOFactory import DAOFactory
from WMCore.WMBS.File import File
from WMCore.WMFactory import WMFactory
from WMQuality.TestInit import TestInit
from WMCore.DataStructs.Run import Run

class File_t(unittest.TestCase):
    _setup = False
    _teardown = False
    
    def setUp(self):
        """
        _setUp_

        Setup the database and logging connection.  Try to create all of the
        WMBS tables.  Also add some dummy locations.
        """
        if self._setup:
            return

        self.testInit = TestInit(__file__, os.getenv("DIALECT"))
        self.testInit.setLogging()
        self.testInit.setDatabaseConnection()
        self.testInit.setSchema(customModules = ["WMCore.WMBS"],
                                useDefault = False)

        myThread = threading.currentThread()
        daofactory = DAOFactory(package = "WMCore.WMBS",
                                logger = myThread.logger,
                                dbinterface = myThread.dbi)

        locationAction = daofactory(classname = "Locations.New")
        locationAction.execute(sename = "se1.cern.ch")
        locationAction.execute(sename = "se1.fnal.gov")        
        
        self._setup = True
        return
          
    def tearDown(self):        
        """
        _tearDown_
        
        Drop all the WMBS tables.
        """
        myThread = threading.currentThread()
        
        if self._teardown:
            return

        if myThread.transaction == None:
            myThread.transaction = Transaction(self.dbi)
        
        myThread.transaction.begin()

        factory = WMFactory("WMBS", "WMCore.WMBS")        
        destroy = factory.loadObject(myThread.dialect + ".Destroy")
        destroyworked = destroy.execute(conn = myThread.transaction.conn)

        if not destroyworked:
            raise Exception("Could not complete WMBS tear down.")
        
        myThread.transaction.commit()    
        self._teardown = True
            
    def testCreateDeleteExists(self):
        """
        _testCreateDeleteExists_

        Test the create(), delete() and exists() methods of the file class
        by creating and deleting a file.  The exists() method will be
        called before and after creation and after deletion.
        """
        testFile = File(lfn = "/this/is/a/lfn", size = 1024, events = 10, cksum=1111)

        assert testFile.exists() == False, \
               "ERROR: File exists before it was created"

	testFile.addRun(Run(1, *[45]))
        testFile.create()

        assert testFile.exists() > 0, \
               "ERROR: File does not exist after it was created"

        testFile.delete()

        assert testFile.exists() == False, \
               "ERROR: File exists after it has been deleted"
        return

    def testCreateTransaction(self):
        """
        _testCreateTransaction_

        Begin a transaction and then create a file in the database.  Afterwards,
        rollback the transaction.  Use the File class's exists() method to
        to verify that the file doesn't exist before it was created, exists
        after it was created and doesn't exist after the transaction was rolled
        back.
        """
        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testFile = File(lfn = "/this/is/a/lfn", size = 1024, events = 10, cksum=1111)

        assert testFile.exists() == False, \
               "ERROR: File exists before it was created"

	testFile.addRun(Run(1, *[45]))
        testFile.create()

        assert testFile.exists() > 0, \
               "ERROR: File does not exist after it was created"

        myThread.transaction.rollback()

        assert testFile.exists() == False, \
               "ERROR: File exists after transaction was rolled back."
        return    

    def testDeleteTransaction(self):
        """
        _testDeleteTransaction_

        Create a file and commit it to the database.  Start a new transaction
        and delete the file.  Rollback the transaction after the file has been
        deleted.  Use the file class's exists() method to verify that the file
        does not exist after it has been deleted but does exist after the
        transaction is rolled back.
        """
        testFile = File(lfn = "/this/is/a/lfn", size = 1024, events = 10,
                        cksum=1111)

        assert testFile.exists() == False, \
               "ERROR: File exists before it was created"

	testFile.addRun(Run(1, *[45]))
        testFile.create()

        assert testFile.exists() > 0, \
               "ERROR: File does not exist after it was created"

        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testFile.delete()

        assert testFile.exists() == False, \
               "ERROR: File exists after it has been deleted"

        myThread.transaction.rollback()

        assert testFile.exists() > 0, \
               "ERROR: File does not exist after transaction was rolled back."
        return

    def testGetInfo(self):
        """
        _testGetInfo_

        Test the getInfo() method of the File class to make sure that it
        returns the correct information.
        """
        testFileParent = File(lfn = "/this/is/a/parent/lfn", size = 1024,
                              events = 20, cksum=1111)
	testFileParent.addRun(Run(1, *[45]))
        testFileParent.create()

        testFile = File(lfn = "/this/is/a/lfn", size = 1024, events = 10, cksum=222)
	testFile.addRun(Run(1, *[45]))
	testFile.addRun(Run(2, *[46, 47]))
	testFile.addRun(Run(2, *[48]))
        testFile.create()
        testFile.setLocation(se = "se1.fnal.gov", immediateSave = False)
        testFile.setLocation(se = "se1.cern.ch", immediateSave = False)
        testFile.addParent("/this/is/a/parent/lfn")

        info = testFile.getInfo()
        assert info[0] == testFile["lfn"], \
               "ERROR: File returned wrong LFN"
        
        assert info[1] == testFile["id"], \
               "ERROR: File returned wrong ID"
        
        assert info[2] == testFile["size"], \
               "ERROR: File returned wrong size"
        
        assert info[3] == testFile["events"], \
               "ERROR: File returned wrong events"
        
        assert info[4] == testFile["cksum"], \
               "ERROR: File returned wrong cksum"
	assert len(info[5]) == 3, \
		"ERROR: File returned wrong runs"

        assert len(info[6]) == 2, \
               "ERROR: File returned wrong locations"

        for testLocation in info[6]:
            assert testLocation in ["se1.fnal.gov", "se1.cern.ch"], \
                   "ERROR: File returned wrong locations"

        assert len(info[7]) == 1, \
               "ERROR: File returned wrong parents"

        assert info[7][0] == testFileParent, \
               "ERROR: File returned wrong parents"

        testFile.delete()
        testFileParent.delete()
        return
        
    def testGetParentLFNs(self):
        """
        _testGetParentLFNs_

        Create three files and set them to be parents of a fourth file.  Check
        to make sure that getParentLFNs() on the child file returns the correct
        LFNs.
        """
        testFileParentA = File(lfn = "/this/is/a/parent/lfnA", size = 1024,
                               events = 20, cksum = 1)
	testFileParentA.addRun(Run(1, *[45]))
        testFileParentB = File(lfn = "/this/is/a/parent/lfnB", size = 1024,
                               events = 20, cksum = 2)
        testFileParentB.addRun(Run(1, *[45]))
        testFileParentC = File(lfn = "/this/is/a/parent/lfnC", size = 1024,
                               events = 20, cksum = 3)
        testFileParentC.addRun(Run( 1, *[45]))

        testFileParentA.create()
        testFileParentB.create()
        testFileParentC.create()

        testFile = File(lfn = "/this/is/a/lfn", size = 1024,
                               events = 10, cksum = 1)
        testFile.addRun(Run( 1, *[45]))
        testFile.create()

        testFile.addParent(testFileParentA["lfn"])
        testFile.addParent(testFileParentB["lfn"])
        testFile.addParent(testFileParentC["lfn"])

        parentLFNs = testFile.getParentLFNs()
        
        assert len(parentLFNs) == 3, \
               "ERROR: Child does not have the right amount of parents"

        goldenLFNs = ["/this/is/a/parent/lfnA",
                      "/this/is/a/parent/lfnB",
                      "/this/is/a/parent/lfnC"]
        for parentLFN in parentLFNs:
            assert parentLFN in goldenLFNs, \
                   "ERROR: Unknown parent lfn"
            goldenLFNs.remove(parentLFN)
                   
        testFile.delete()
        testFileParentA.delete()
        testFileParentB.delete()
        testFileParentC.delete()
        return
    
    def testLoad(self):
        """
        _testLoad_

        Create a file, add two parents and two locations and save the file
        to the database.  Load the file using the ID and using the LFN and
        compare the loaded file to the original to make sure everything loaded
        correctly.
        """
        testFileParentA = File(lfn = "/this/is/a/parent/lfnA", size = 1024,
                              events = 20, cksum = 1)
        testFileParentA.addRun(Run( 1, *[45]))
        testFileParentB = File(lfn = "/this/is/a/parent/lfnB", size = 1024,
                              events = 20, cksum = 1)
        testFileParentB.addRun(Run( 1, *[45]))
        testFileParentA.create()
        testFileParentB.create()

        testFileA = File(lfn = "/this/is/a/lfn", size = 1024, events = 10,
                        cksum = 1)
        testFileA.addRun(Run( 1, *[45]))
        testFileA.create()
        testFileA.setLocation(se = "se1.fnal.gov", immediateSave = False)
        testFileA.setLocation(se = "se1.cern.ch", immediateSave = False)
        testFileA.addParent("/this/is/a/parent/lfnA")
        testFileA.addParent("/this/is/a/parent/lfnB")
        testFileA.updateLocations()
                                                        
        testFileB = File(lfn = testFileA["lfn"])
        testFileB.load(parentage = 1)
        testFileC = File(id = testFileA["id"])
        testFileC.load(parentage = 1)

        assert testFileA == testFileB, \
               "ERROR: File load by LFN didn't work"

        assert testFileA == testFileC, \
               "ERROR: File load by ID didn't work"

        testFileA.delete()
        testFileParentA.delete()
        testFileParentB.delete()
        return

    def testAddChild(self):
        """
        _testAddChild_

        Add a child to some parent files and make sure that all the parentage
        information is loaded/stored correctly from the database.
        """
        testFileParentA = File(lfn = "/this/is/a/parent/lfnA", size = 1024,
                              events = 20, cksum = 1)
        testFileParentA.addRun(Run( 1, *[45]))
        testFileParentB = File(lfn = "/this/is/a/parent/lfnB", size = 1024,
                              events = 20, cksum = 1)
        testFileParentB.addRun(Run( 1, *[45]))
        testFileParentA.create()
        testFileParentB.create()

        testFileA = File(lfn = "/this/is/a/lfn", size = 1024, events = 10,
                         cksum = 1)
        testFileA.addRun(Run( 1, *[45]))
        testFileA.create()

        testFileParentA.addChild("/this/is/a/lfn")
        testFileParentB.addChild("/this/is/a/lfn")

        testFileB = File(id = testFileA["id"])
        testFileB.load(parentage = 1)

        goldenFiles = [testFileParentA, testFileParentB]
        for parentFile in testFileB["parents"]:
            assert parentFile in goldenFiles, \
                   "ERROR: Unknown parent file"
            goldenFiles.remove(parentFile)

        assert len(goldenFiles) == 0, \
              "ERROR: Some parents are missing"
        return

    def testAddChildTransaction(self):
        """
        _testAddChildTransaction_

        Add a child to some parent files and make sure that all the parentage
        information is loaded/stored correctly from the database.  Rollback the
        addition of one of the childs and then verify that it does in fact only
        have one parent.
        """
        testFileParentA = File(lfn = "/this/is/a/parent/lfnA", size = 1024,
                              events = 20, cksum = 1)
        testFileParentA.addRun(Run( 1, *[45]))
        testFileParentB = File(lfn = "/this/is/a/parent/lfnB", size = 1024,
                              events = 20, cksum = 1)
        testFileParentB.addRun(Run( 1, *[45]))
        testFileParentA.create()
        testFileParentB.create()

        testFileA = File(lfn = "/this/is/a/lfn", size = 1024, events = 10,
                         cksum = 1)
        testFileA.addRun(Run( 1, *[45]))
        testFileA.create()

        testFileParentA.addChild("/this/is/a/lfn")

        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testFileParentB.addChild("/this/is/a/lfn")

        testFileB = File(id = testFileA["id"])
        testFileB.load(parentage = 1)

        goldenFiles = [testFileParentA, testFileParentB]
        for parentFile in testFileB["parents"]:
            assert parentFile in goldenFiles, \
                   "ERROR: Unknown parent file"
            goldenFiles.remove(parentFile)

        assert len(goldenFiles) == 0, \
              "ERROR: Some parents are missing"

        myThread.transaction.rollback()
        testFileB.load(parentage = 1)

        goldenFiles = [testFileParentA]
        for parentFile in testFileB["parents"]:
            assert parentFile in goldenFiles, \
                   "ERROR: Unknown parent file"
            goldenFiles.remove(parentFile)

        assert len(goldenFiles) == 0, \
              "ERROR: Some parents are missing"
        
        return
    
    def testSetLocation(self):
        """
        _testSetLocation_

        Create a file and add a couple locations.  Load the file from the
        database to make sure that the locations were set correctly.
        """
        testFileA = File(lfn = "/this/is/a/lfn", size = 1024, events = 10,
                        cksum = 1)
        testFileA.addRun(Run( 1, *[45]))
        testFileA.create()
        testFileA.setLocation(["se1.fnal.gov", "se1.cern.ch"])
        testFileA.setLocation(["bunkse1.fnal.gov", "bunkse1.cern.ch"],
                              immediateSave = False)

        testFileB = File(id = testFileA["id"])
        testFileB.load()

        goldenLocations = ["se1.fnal.gov", "se1.cern.ch"]

        for location in testFileB["locations"]:
            assert location in goldenLocations, \
                   "ERROR: Unknown file location"
            goldenLocations.remove(location)

        assert len(goldenLocations) == 0, \
              "ERROR: Some locations are missing"    
        return

    def testSetLocationTransaction(self):
        """
        _testSetLocationTransaction_

        """
        testFileA = File(lfn = "/this/is/a/lfn", size = 1024, events = 10,
                        cksum = 1)
        testFileA.addRun(Run( 1, *[45]))
        testFileA.create()
        testFileA.setLocation(["se1.fnal.gov"])

        myThread = threading.currentThread()
        myThread.transaction.begin()
        
        testFileA.setLocation(["se1.cern.ch"])
        testFileA.setLocation(["bunkse1.fnal.gov", "bunkse1.cern.ch"],
                              immediateSave = False)

        testFileB = File(id = testFileA["id"])
        testFileB.load()

        goldenLocations = ["se1.fnal.gov", "se1.cern.ch"]

        for location in testFileB["locations"]:
            assert location in goldenLocations, \
                   "ERROR: Unknown file location"
            goldenLocations.remove(location)

        assert len(goldenLocations) == 0, \
              "ERROR: Some locations are missing"

        myThread.transaction.rollback()
        testFileB.load()

        goldenLocations = ["se1.fnal.gov"]

        for location in testFileB["locations"]:
            assert location in goldenLocations, \
                   "ERROR: Unknown file location"
            goldenLocations.remove(location)

        assert len(goldenLocations) == 0, \
              "ERROR: Some locations are missing"
        return    

    def testLocationsConstructor(self):
        """
        _testLocationsConstructor_

        Test to make sure that locations passed into the File() constructor
        are loaded from and save to the database correctly.  Also test to make
        sure that the class behaves well when the location is passed in as a
        single string instead of a set.
        """
        testFileA = File(lfn = "/this/is/a/lfn", size = 1024, events = 10,
                        cksum = 1, locations = Set(["se1.fnal.gov"]))
        testFileA.addRun(Run( 1, *[45]))
        testFileA.create()

        testFileB = File(lfn = "/this/is/a/lfn2", size = 1024, events = 10,
                        cksum = 1, locations = "se1.fnal.gov")
        testFileB.addRun(Run( 1, *[45]))
        testFileB.create()        

        testFileC = File(id = testFileA["id"])
        testFileC.load()

        goldenLocations = ["se1.fnal.gov"]
        for location in testFileC["locations"]:
            assert location in goldenLocations, \
                   "ERROR: Unknown file location"
            goldenLocations.remove(location)
            
        assert len(goldenLocations) == 0, \
              "ERROR: Some locations are missing"

        testFileC = File(id = testFileB["id"])
        testFileC.load()

        goldenLocations = ["se1.fnal.gov"]
        for location in testFileC["locations"]:
            assert location in goldenLocations, \
                   "ERROR: Unknown file location"
            goldenLocations.remove(location)
            
        assert len(goldenLocations) == 0, \
              "ERROR: Some locations are missing"        
        return

if __name__ == "__main__":
    unittest.main() 
