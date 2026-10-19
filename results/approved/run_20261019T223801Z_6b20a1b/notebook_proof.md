# CAQH notebook proof — run_20261019T223801Z_6b20a1b

* runner: claude-code container, src-only (post75, 6b20a1b); provider live, databricks-claude-opus-5, --environment D1, notebook + framework
* Step 6 asked: which cluster or external location the ingestion framework uses to read the landing container (Raj or Sarath).
* Not asked today: this runner has no channel to reach them. Checked instead (read-only): 16 Unity Catalog external locations are visible to the runner's identity, 0 cover the landing storage account.
* Rerun on another cluster: skipped (no cluster / external location named).
* Previous attempt (run_20261019T181043Z_fe61bc4, D1-FSC-ETL-SC-S-16.4-01, dry_run=true): config cell ran yes; read cell defined yes; read row count not measured; first error = proof cell, source_files -> dbutils.fs.ls, ExecutionError (no storage credential for the landing account on that cluster).
* Notebook present in this run: pair_12 feed_1 yes (the notebook is in the work folder, not imported this time).
