# Questions for Rama — 2026-11-03

**Why we're asking:** the agent fills the ACFC metadata (IIG) from the FRD and the STTM.
Three things are not in any document, so today the agent leaves them blank or guesses:
how child pipelines run, how IDs are assigned, and when one pipeline covers many tables.
The prod facts below come from the framework's own rows
(`docs/acfc/iig_goldens/01_pair_group_index.csv`).

## 1. Child pipelines

Today the agent writes **1 grand master + 1 master + 2 children per feed**
(file → stage and stage → standard), all under the one master.

1. Does every feed get its own two children? Or do several feeds share one child?
2. Under one master, do the children run **in parallel or in sequence**? If in sequence,
   which order (by feed? stage before standard?), and **where is that order stored**?
   The schedule table has no order column. Is it `UDF1` (the dependency check) or the
   ADF / Workflow definition outside the metadata?
3. Must the stage → standard child wait for its own feed's file → stage child only, or
   for every file → stage child under the master?
4. pair_11: the agent writes 12 schedule rows and prod has 10. Both have 2 children per
   feed; the difference is **5 feeds vs 4**. Is the 5th feed in prod under a different
   master, or not deployed?
5. Is the grand master / master **new for each feed**, or an existing pipeline that new
   children attach to? If existing, how does the engineer find its PIPELINE_ID?
6. Child names: the EDO pattern
   `PL_CHLD_<Product>_<Sub-Product>_<Source>_TO_<Target>_<Load Strategy>` has no feed
   slot, so two feeds' children get the same name. What makes them unique in prod? The
   pair_11 prod rows use an older pattern (`PL_File_PYX_CM_MIDS_<feed>_ADLS_To_Delta_Incr`).

## 2. How IDs are assigned (GROUP_ID, PIPELINE_ID, OBJECT_ID)

What prod shows:
- **PIPELINE_ID = GROUP_ID + 200** on 297 of 299 rows. The exception is pair_07:
  18603 → 180603 and 18604 → 180604.
- **The stage → standard group is the next number:** pair_02 has 180251 / 180252,
  180253 / 180254 and 180255 / 180256.
- **The ID ranges overlap:** 2109459103 is pair_10's GROUP_ID and also a PIPELINE_ID in
  pair_09.
- **OBJECT_ID is used two ways:**
  - 1..n inside one group: pair_08 CAQH has 18 objects, pair_09 has 36;
  - a running number across groups, one object per group: pair_08 834prop runs 5..67,
    with 15, 16 and 20 each used twice or more.

7. Who issues GROUP_ID and PIPELINE_ID: a person, a register / sequence, or a query for
   max + n? Is "+200" a rule or a habit? Is pair_07 a typo?
8. Is the stage → standard leg always GROUP_ID + 1 of its file → stage leg?
9. Must GROUP_ID and PIPELINE_ID be unique across both ranges, or only within each table?
10. OBJECT_ID: always 1..n inside a group? Or do the 834prop rows follow a different
    convention (a running number per source)?
11. Can the agent propose IDs (marked "proposed, check before load"), or must they stay
    blank for the engineer? Today they stay blank because the agent never invents IDs.

## 3. One pipeline with N objects, or one pipeline per table (this settles pairs 08 / 09)

- **pair_02:** 3 tables → 3 groups per leg, 1 object each.
- **pair_08:** CAQH → 1 group with 18 objects (file → stage) and 1 group with 3 objects
  (stage → standard). The 834prop files have a group each.
- **pair_09:** both shapes for the same 36 PeopleSoft tables. There is one group
  (2109458903) with 36 objects, and also 36 groups with 1 object each (1094590930..., in
  steps of 30).

12. What decides between the two shapes? Is it one source file vs one file per table,
    the source system, the load strategy, or the team / date it was built?
13. pair_09: which of the two shapes is current, and is the other one retired?
14. When one group carries N tables, can each table have its own load strategy and keys
    (pair_09's STTM Summary sheet states one per table)? Or must they all match?
15. For the stage → standard table (`STGDELTA_STDDELTA_INGESTION_DET`): is OBJECT_ID per
    file or per table? Is the key (GROUP_ID, OBJECT_ID, PIPELINE_ID)?

## After the session

Write the answers into `docs/RESTART.md`. Then we can:
- set the pair_11 child count;
- decide the ID rule (blank or proposed);
- pick the multi-table shape for pairs 08 / 09.
