# ACFC-side overlay fields (field names and meanings only)

Two kinds of out-of-tree files carry the values that must never enter git.
Both live under `codegen-state/` (gitignored) on the machine that runs the
agent; the repo tracks only the schema, the loader, synthetic examples and the
tests.

| File | Moved by | Synthetic example | Read by |
| --- | --- | --- | --- |
| `codegen-state/overlays/<profile>.yaml` | `CODEGEN_STATE_OVERLAYS_DIR` | `config/overlays/example.yaml` | `codegen.config.load_config` |
| `codegen-state/environments/<name>.yaml` | `CODEGEN_ENVIRONMENTS_DIR` | `config/environments/example.yaml` | `codegen.environments` |

## 1. `codegen-state/overlays/<profile>.yaml`

`<profile>` is the conventions profile after the tracked overlays
(`conventions.profile`; `acfc_prx` for ACFC). `load_config` applies it right
after `config/overlays/acfc_env.yaml` and before `--config` overlays /
`CODEGEN_CONFIG_OVERLAYS`; it is named on the `config overlays (in order)` line.
Mappings deep-merge onto the tracked values; a list replaces. Any config key may
be set; the ones below are the golden-alignment fields (2026-10-15). All sit
under `metadata.templates.iig_v2.`

| Field | Meaning |
| --- | --- |
| `corpus_cells.DATABRICKS_NOTEBOOK_DETAILS.DATABRICKS_NOTEBOOK_NAME.values.<kind>` | The notebook NAME of one leg, per notebook kind (the feed family). Kinds: `stg_to_std`; for the file-to-stage leg `delimited`, `delimited_tpl`, `fixed_width`, `fixed_width_tpl`, `pipe_segmented`, `pipe_segmented_tpl` (`_tpl` = a TPL subdomain, `tpl_subdomains`). The version suffix is part of the value. |
| `corpus_cells.DATABRICKS_NOTEBOOK_DETAILS.DATABRICKS_NOTEBOOK_PATH.values.<kind>` | The notebook PATH of that leg (a comma list for a two-notebook form). |
| `notebook_path_prefix` | The workspace root every notebook path segment starts with; a segment without it gets it prepended (cited in the cell NOTE). Blank = paths as written. |
| `corpus_tokens.<name>` | The `{name}` tokens the notebook values use (`workspace_folder`, `handler_prefix`, `pipe_handler_prefix`). |
| `email_status_default` | The `EMAIL_TEMPLATE_CONFIG` statuses written when the run gives no `run.email_statuses` answer (a subset of `template_rows.EMAIL_TEMPLATE_CONFIG`, in that order). Blank = every template row. |
| `feed_overrides.<feed_id>.email_statuses` | That feed's status set; wins over the default and the run's answer for that feed. |
| `feed_overrides.<feed_id>.src_file_name` | That feed's ADLS `SRC_FILE_NAME` style (below); wins over `family_conventions.src_file_name`. |
| `family_conventions.src_file_name` | The profile's `SRC_FILE_NAME` style: `pattern` (the file pattern as stated), `prefix_star` (the suffix wildcard: name prefix + `*`), `prefix_middle` (leading and middle wildcards: `*` + the name core + `*` + the extension — the leading date-token segments and everything from the first wildcard on dropped). |

`<feed_id>` is the run's feed id (`normalize_feed_name` of the FRD feed name; the
report file name). Unknown keys fail the config load (the loader is loud).

## 2. `codegen-state/environments/<name>.yaml`

One environment profile; resolution and the required keys:
`codegen.environments` (module docstring) and `environment_schema` in
`config/overlays/acfc_env.yaml`.

| Field | Meaning |
| --- | --- |
| `containers.landing` / `.stage` / `.standard` | The ADLS containers per layer — REQUIRED. |
| `storage_account` | The ADLS storage account — REQUIRED. |
| `catalog_map.<logical catalog>` | The STTM's logical catalog → this environment's catalog. |
| `default_catalog.stage` / `.standard` | The catalog for a band whose Catalog is blank. |
| `connection_ids.src_adls` / `.metadata` / `.target` | The framework's connection ids. |
| `values.<name>` | Any other environment-scoped value. |

A required key left blank or as a `<<ENV:...>>` placeholder is a `QUESTION
run.environment.<key>` (exit 3, NEEDS_ANSWERS); its cells are written open.
