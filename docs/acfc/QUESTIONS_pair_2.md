# pair_2 (SD) — open questions for the framework owner (Sarath)

From round 6 (acfc-results `f131dcc`, `codegen-outputs/iig_validation/round6/pair_2/`).
Each item is class A: the documents do not decide it, or two real sources disagree.
Citations: `mismatches.md:<line>` of that round; the reference IIGs are
`fixtures/reference/SFMC_IIG.xlsx` (SFMC) and
`fixtures/acfc_shapes/pair_1/golden/RFC_ACCUMULATORS_IIG.xlsx` (pair 1, PRX family);
"test cells" is the older SD sheet the home invariant scores against.

1. **SCHEMA_DRIFT_FLAG — N or Y for the SD / CAQH family?** The SD prod rows say `N`
   (mismatches.md:10 / :19 / :49), as do SFMC and pair 1. The test-cells sheet and
   the CAQH IIG reported on 2026-10-08 say `Y`. The agent writes `N` since round 7.
   Please confirm `N` is current for new file feeds.
2. **FILE_HEADER_FLAG — what decides it?** SD prod `Y` (mismatches.md:11 / :20 / :50),
   SFMC `Y`, pair 1 `N`. The FRD and the STTM state no header row. Left open.
   Is it "the file has a column-header row" (a FAQ answer), or a family default?
3. **RECYCL_RETN_DAYS for the individual-risk file — 7 or 30?** The STTM's recycle
   column header says the recycle is enabled for 7 days. The test-cells sheet says
   7. The prod row says 30 (mismatches.md:69). The agent writes 7, from the STTM.
4. **FILE_METADATA — should the IIG carry the column?** The prod table has it, with
   `NULL` on all three SD rows (mismatches.md:17 / :26 / :71), and SFMC has it blank.
   The iig_v2 template has no such column; it was transcribed from the pair-1 RFC
   package. Should the column be added for every feed?
5. **DATABRICKS_NOTEBOOK_PATH — is `/Workspace/iig/<notebook>` the convention for
   new feeds?** SD prod (mismatches.md:557 / :564) and SFMC use it. Pair 1 uses a
   vendor folder. Left open.
6. **Notebook PROCESS_NAME — what is the rule?** SD prod reads
   `Stage Load for <domain> <file name in title case>` and `Standard Load for …`
   (mismatches.md:553 / :560). SFMC reads `Stage Load for <source>`. No document
   states either.
7. **Environment values on DATABRICKS_NOTEBOOK_DETAILS.** These are the workspace
   URL, the access-token secret name, DATABRICKS_CLUSTERID (`NA` in prod) and
   CLUSTER_DETAILS_ID (an id) (mismatches.md:554–558). No document states them.
   Should they come from the environment overlay, or be assigned by the deployer?
8. **Is the test-cells sheet superseded by the prod export?** It differs from prod on
   four points:
   - SCHEMA_DRIFT_FLAG (item 1).
   - The `_MI` in the individual-risk OBJECT_NAME / SRC_FILE_NAME. Prod has it, and
     both the FRD and the STTM file-details row state it.
   - `Decimal(10,2)` vs bare `Decimal` in STGDELTA SRC_DATA_TYPE.
   - Retention days (item 3).

   If prod is current, the home invariant should be re-based on the prod rows.
