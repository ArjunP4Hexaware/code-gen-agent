/*
 * Office Script: export the AI Agent incident tracker's sheet(s) as JSON lines.
 *
 * Why: Graph is refused from the coding container (Conditional Access), so Soham runs
 * this in Excel (Automate -> New Script -> paste -> Run) on the SharePoint workbook
 * AI_Agent_Incident_tracker.xlsx and pastes the result into the chat.
 *
 * READ-ONLY on the tracker: it only (re)creates a sheet named _JSON_EXPORT.
 * Output, in _JSON_EXPORT column A, one JSON object per row:
 *   1st line  {"_sheet", "_header_row", "_columns": [...]}       per exported sheet
 *   then      {"_sheet", "_row": <Excel row number>, "<header>": <value>, ...}
 *             (empty cells left out; dates as ISO yyyy-mm-dd[Thh:mm:ssZ])
 *   last      {"_end": true, "records": <n>}
 * A line longer than one cell holds (32,767 characters) is split across rows; column B
 * says "cont" on every continuation row - join it to the row above, no separator.
 *
 * To copy: click A1 of _JSON_EXPORT, Ctrl+Shift+Down, Ctrl+C, paste into the chat.
 * Delete the _JSON_EXPORT sheet afterwards (or leave it; the next run replaces it).
 * Client text: the export is client content - it is pasted into the chat only, never
 * committed (AGENTS.md, "The incident tracker").
 */
function main(workbook: ExcelScript.Workbook) {
  const SHEETS: string[] = ["CodeGen"];   // add more sheet names to export them too
  const OUT = "_JSON_EXPORT";
  const CHUNK = 30000;                    // under Excel's 32,767-character cell limit

  const lines: string[] = [];
  let records = 0;

  for (const name of SHEETS) {
    const ws = workbook.getWorksheet(name);
    if (!ws) {
      lines.push(JSON.stringify({ _sheet: name, _error: "sheet not found" }));
      continue;
    }
    const used = ws.getUsedRange(true);   // values only
    if (!used) {
      lines.push(JSON.stringify({ _sheet: name, _error: "sheet is empty" }));
      continue;
    }
    const values = used.getValues();
    const formats = used.getNumberFormats();
    const top = used.getRowIndex();       // 0-based
    const filled = (v: string | number | boolean) => v !== "" && v !== null && v !== undefined;

    // header = the first row with 2+ filled cells
    const h = values.findIndex(row => row.filter(filled).length >= 2);
    if (h < 0) {
      lines.push(JSON.stringify({ _sheet: name, _error: "no header row found" }));
      continue;
    }
    const seen: { [k: string]: number } = {};
    const headers = values[h].map((v, i) => {
      let key = String(v).replace(/\s+/g, " ").trim() || `col_${i + 1}`;
      if (seen[key] !== undefined) {
        seen[key] += 1;
        key = `${key} (${seen[key]})`;
      } else {
        seen[key] = 1;
      }
      return key;
    });
    lines.push(JSON.stringify({ _sheet: name, _header_row: top + h + 1, _columns: headers }));

    for (let r = h + 1; r < values.length; r++) {
      const row = values[r];
      if (!row.some(filled)) continue;
      const rec: { [k: string]: string | number | boolean } = { _sheet: name, _row: top + r + 1 };
      for (let c = 0; c < headers.length; c++) {
        const v = row[c];
        if (!filled(v)) continue;
        rec[headers[c]] = typeof v === "number" && isDateFormat(formats[r][c]) ? serialToIso(v) : v;
      }
      lines.push(JSON.stringify(rec));
      records += 1;
    }
  }
  lines.push(JSON.stringify({ _end: true, records: records }));

  // split long lines into continuation rows
  const rows: string[][] = [];
  for (const line of lines) {
    for (let i = 0; i < line.length; i += CHUNK) {
      rows.push([line.slice(i, i + CHUNK), i === 0 ? "" : "cont"]);
    }
  }

  const old = workbook.getWorksheet(OUT);
  if (old) old.delete();
  const out = workbook.addWorksheet(OUT);
  const target = out.getRange(`A1:B${rows.length}`);
  target.setNumberFormat("@");            // text: Excel must not reinterpret the JSON
  target.setValues(rows);
  out.activate();
  console.log(`${records} record(s) from ${SHEETS.join(", ")} -> ${OUT} (${rows.length} row(s))`);
}

/* A number format that shows a date / time (quoted text and [..] sections ignored). */
function isDateFormat(fmt: string): boolean {
  if (!fmt) return false;
  const bare = String(fmt).replace(/"[^"]*"/g, "").replace(/\[[^\]]*\]/g, "");
  return /[dyhs]/i.test(bare) || /m{3,}/i.test(bare);
}

/* Excel serial date (1900 system) -> ISO; whole days -> yyyy-mm-dd. */
function serialToIso(serial: number): string {
  const ms = Math.round((serial - 25569) * 86400 * 1000);
  const iso = new Date(ms).toISOString();
  return Number.isInteger(serial) ? iso.slice(0, 10) : iso.replace(/\.\d{3}Z$/, "Z");
}
