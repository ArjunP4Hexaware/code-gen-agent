# IIG template default for ACFC

**The ACFC default stays `iig_v2`** (`config/overlays/acfc_env.yaml`
`metadata.template`). It is the PRX 8-sheet layout ACFC's framework loads, and
it writes pipeline names in the `PL_File_…` convention the prod goldens use
(`config/config.yaml` iig_v2 pipelines). `iig_v1` is the 7-tab SFMC reference
layout, and it also switches the naming convention to the EDO `WF_` / `NB_`
builders. That switch is what produced the round-7 pair_2 diff of 0.0: no
generated name matched a golden one.

When `tools/iig_diff.py` sees a 7-sheet golden against an 8-sheet agent
workbook, its `NOTE` only says so. The sheet one side lacks is reported
separately and does not affect the comparable score, and naming-convention
columns are never scored. It never recommends rerunning with
`--iig-template iig_v1`. Do not change the template to make a diff line up.
