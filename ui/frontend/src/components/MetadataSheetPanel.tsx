import { Fragment, useEffect, useState } from "react";
import { api, type MetadataSheetResponse, type ProvenanceBadge } from "../api";

/* Display-only preview of the ACFC metadata sheet — the output shape for
   their metadata-driven framework. Every cell carries exactly one
   provenance badge; the layout itself is a config stand-in until the
   client's template arrives. Rendered on the Generate card and again on
   the dashboard after a run (where the columns tab is populated). */

const BADGE_LABELS: Record<ProvenanceBadge, string> = {
  from_sttm: "from STTM",
  from_sttm_unmapped: "from STTM (unmapped)",
  from_frd: "from FRD",
  synthetic: "SYNTHETIC",
  needs_template: "NEEDS CLIENT TEMPLATE",
};

function ProvenanceDot({
  badge,
  tooltip,
}: {
  badge: ProvenanceBadge;
  tooltip?: string;
}) {
  const title = tooltip ? `${BADGE_LABELS[badge]} — ${tooltip}` : BADGE_LABELS[badge];
  return <span className={`prov-dot prov-${badge}`} title={title} />;
}

export function MetadataSheetPanel({ refreshKey }: { refreshKey?: string | number }) {
  const [sheet, setSheet] = useState<MetadataSheetResponse | null>(null);
  const [activeTab, setActiveTab] = useState<string | null>(null);

  useEffect(() => {
    api.metadataSheet().then(setSheet).catch(() => setSheet(null));
  }, [refreshKey]);

  if (!sheet) return null;
  const tabNames = Object.keys(sheet.tabs);
  const current = activeTab && sheet.tabs[activeTab] ? activeTab : tabNames[0];
  const tab = sheet.tabs[current];
  const { coverage } = sheet;

  return (
    <div>
      <div className="panel-subhead">For ACFC's framework: metadata sheet preview</div>
      <p className="hint" style={{ marginTop: 0 }}>
        {sheet.layout_note}
      </p>
      <div className="sheet-tab-strip">
        {tabNames.map((name) => (
          <button
            key={name}
            className={`btn sheet-tab${name === current ? " active" : ""}`}
            onClick={() => setActiveTab(name)}
          >
            {name}
            <span className="hint"> {sheet.tabs[name].rows.length}</span>
          </button>
        ))}
      </div>
      {tab.rows.length === 0 ? (
        <div className="empty">{tab.state ?? "no rows"}</div>
      ) : (
        <div className="source-files-scroll">
          <table className="source-files-table">
            <thead>
              <tr>
                {tab.headers.map((h) => (
                  <th key={h}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tab.rows.map((row, i) => {
                const previous = i > 0 ? tab.rows[i - 1] : null;
                const newFeed =
                  row.feed_slug && row.feed_slug !== previous?.feed_slug;
                return (
                  <Fragment key={i}>
                    {newFeed && current === "columns" ? (
                      <tr className="sheet-feed-row">
                        <td colSpan={tab.headers.length}>
                          <code>{row.feed_slug}</code>
                        </td>
                      </tr>
                    ) : null}
                    <tr>
                      {tab.headers.map((h) => (
                        <td key={h} className={`sheet-cell-${row.badges[h].badge}`}>
                          {String(row.values[h] ?? "")}
                          <ProvenanceDot
                            badge={row.badges[h].badge}
                            tooltip={row.badges[h].tooltip}
                          />
                        </td>
                      ))}
                    </tr>
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="hint" style={{ margin: "8px 0 4px" }}>
        <strong>
          {coverage.derived} of {coverage.total}
        </strong>{" "}
        values derived from documents · {coverage.synthetic} synthesized ·{" "}
        {coverage.needs_template} await the client template.
      </p>
      <p>
        <a
          className="btn"
          href="/api/demo/metadata-sheet.xlsx"
          download
        >
          Download .xlsx
        </a>
      </p>
      <p className="hint" style={{ marginTop: 4, fontSize: 11 }}>
        Display only — the reviewed sheet is the approval artifact. On approval the
        rows land in the ingestion framework database, and the generated DDL +
        insert SQL are add-ons to ACFC's master notebook — the client's own
        notebook, never generated or edited by the agent. The agent never inserts
        unapproved rows.
      </p>
    </div>
  );
}
