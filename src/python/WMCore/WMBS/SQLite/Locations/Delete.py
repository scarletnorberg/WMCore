#!/usr/bin/env python
"""
_Delete_

SQLite implementation of Locations.Delete
"""

__all__ = []



from WMCore.WMBS.MySQL.Locations.Delete import Delete as DeleteLocationsMySQL

class Delete(DeleteLocationsMySQL):
    sql = DeleteLocationsMySQL.sql
