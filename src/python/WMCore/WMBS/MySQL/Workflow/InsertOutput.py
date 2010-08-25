#!/usr/bin/env python
"""
_InsertOutput_

MySQL implementation of Workflow.InsertOutput
"""

__all__ = []



from WMCore.Database.DBFormatter import DBFormatter

class InsertOutput(DBFormatter):
    sql = """INSERT INTO wmbs_workflow_output (workflow_id, output_identifier,
                                               output_fileset, output_parent)
               SELECT :workflow AS workflow_id, :output AS output_identifier,
                 :fileset AS output_fileset, :parent AS output_parent
                 FROM DUAL WHERE NOT EXISTS
               (SELECT workflow_id FROM wmbs_workflow_output
                 WHERE :workflow = workflow_id AND :output = output_identifier)
          """

    def execute(self, workflowID, outputIdentifier, filesetID, outputParent,
                conn = None, transaction = False):
        binds = {"workflow": workflowID,
                 "output": outputIdentifier,
                 "fileset": filesetID,
                 "parent": outputParent}
        self.dbi.processData(self.sql, binds, conn = conn,
                             transaction = transaction)
        return
