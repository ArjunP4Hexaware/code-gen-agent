# Office Scripts for Soham's SharePoint workbooks

Graph is refused from the coding container (ACFC Conditional Access - never route around
it), so the agent writes an **Office Script** and Soham runs it in Excel (Automate -> New
Script -> paste over the sample -> Run). The scripts live here so a container reset never
loses them.

| Script | Workbook / sheet | What it does |
|---|---|---|
| `export_incident_tracker.ts` | `AI_Agent_Incident_tracker.xlsx`, sheet `CodeGen` | READ-ONLY export: one JSON line per incident into a `_JSON_EXPORT` sheet (column B `cont` = join to the row above). Soham pastes column A into the chat; it is client text - read, never committed. |

An update script (rows changed by Incident No) is written per change, from the latest
export: a `DRY_RUN` switch first (the console lists what it would do), idempotent (an
"Update <date>:" line already there is not added again), Comments never touched. It
quotes client text (incident values), so it is given in the chat and kept in /tmp only -
**never committed** (2026-11-19's: `/tmp/t/osc/update_incident_tracker_2026-11-19.ts`).

## The failure that keeps happening: Office Scripts is not plain TypeScript

**It compiles here and fails in Excel.** Excel's Office Scripts compiler is stricter than
`tsc`, and the error is NOT a paste problem (2026-11-19: "Only arrow functions may be used
in array method callbacks", line 35 / line 55 - a named function passed to `filter` /
`some`). Rules it enforces that `tsc --strict` does not:

- **An array method's callback is an arrow function written in place.**
  `row.filter(isFilled)` fails; `row.filter(v => isFilled(v))` works. Same for `map`,
  `some`, `every`, `find`, `findIndex`, `forEach`, `reduce`, `sort`.
- **No `function (x) {...}` expressions as callbacks** - arrows only.
- **No `any`** (explicit or implied) - give every parameter a type.

**Before handing a script over, run both checks:**

```bash
python3 tools/tracker/check_office_script.py tools/tracker/<script>.ts   # the rules above
# + tsc --strict against a minimal ExcelScript declaration, and a run on a fake workbook
#   (the recipe of 2026-11-19: /tmp/t/osc/excel.d.ts + run.js - rebuild them if gone)
```

`check_office_script.py` is a regex heuristic; when Excel reports a new rule, add it there
and here.
