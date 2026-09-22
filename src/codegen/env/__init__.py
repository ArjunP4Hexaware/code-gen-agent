"""Environment reconciliation (M10): what exists in the TARGET environment,
and what the deployment artefacts do about it.

``model``    pure data — imported by the emitters and the report.
``expect``   what the artefacts expect to find (tables + config rows).
``probe``    the classifier: absent | identical | different | unreadable.
``clients``  the two read-only transports (Unity Catalog through the SQL
             seam, the SQL Server metadata DB through JDBC) — an EDGE.

Both probe targets exist ONLY inside the operator's own workspace. Nothing in
this package can be exercised from a developer machine: outside a Databricks
runtime every object reads ``unreadable`` and no credential is resolved.
"""
