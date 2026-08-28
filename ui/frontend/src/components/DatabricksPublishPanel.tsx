import { useEffect, useState } from "react";
import { api, type DatabricksPublishResult, type DatabricksPublishTarget } from "../api";

// The human-gated outbound half of the volumes seam: the reviewer picks the
// target catalog.schema.volume, confirms per feed, and the feed's report +
// notebook (+ framework artefacts) land under <volume>/<feed_slug>/ in Unity
// Catalog. The picker is free-form on purpose — but the BACKEND refuses any
// target outside the code-enforced writable prefix, and this panel says so
// on its face rather than pretending the choice is unlimited.
export function DatabricksPublishPanel({ feedSlugs }: { feedSlugs: string[] }) {
  const [target, setTarget] = useState<DatabricksPublishTarget | null>(null);
  const [catalog, setCatalog] = useState("");
  const [schema, setSchema] = useState("");
  const [volume, setVolume] = useState("");
  const [feed, setFeed] = useState(feedSlugs[0] ?? "");
  const [confirming, setConfirming] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [result, setResult] = useState<DatabricksPublishResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .databricksPublishTarget()
      .then((t) => {
        setTarget(t);
        setCatalog(t.catalog ?? "");
        setSchema(t.schema ?? "");
        setVolume(t.volume ?? "");
      })
      .catch(() => setTarget(null));
  }, []);

  useEffect(() => {
    if (!feedSlugs.includes(feed)) setFeed(feedSlugs[0] ?? "");
  }, [feedSlugs, feed]);

  if (target === null) return null;

  const fullName = `${catalog}.${schema}.${volume}`;
  const insidePolicy = `${catalog}.${schema}.`.startsWith(target.writable_prefix);
  const ready = target.available && catalog && schema && volume && feed;

  const publish = async () => {
    setPublishing(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.databricksPublish({
        feed_slug: feed,
        catalog,
        schema_name: schema,
        volume,
      });
      setResult(res);
      setConfirming(false);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
      setConfirming(false);
    } finally {
      setPublishing(false);
    }
  };

  return (
    <div className="panel" style={{ marginTop: 18 }}>
      <div className="panel-head">
        <h2>Publish to Unity Catalog volume</h2>
        <span className="hint">
          the human gate for Databricks: reviewed artifacts land under{" "}
          <code>/Volumes/…/&lt;feed&gt;/</code> — never a side effect of generating
        </span>
      </div>
      <div className="panel-body">
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "flex-end" }}>
          {(
            [
              ["Catalog", catalog, setCatalog],
              ["Schema", schema, setSchema],
              ["Volume", volume, setVolume],
            ] as const
          ).map(([label, value, set]) => (
            <label key={label} style={{ display: "grid", gap: 4, fontSize: 12 }}>
              <span className="hint">{label}</span>
              <input
                className="input"
                value={value}
                onChange={(e) => set(e.target.value.trim())}
                style={{ width: 170 }}
              />
            </label>
          ))}
          <label style={{ display: "grid", gap: 4, fontSize: 12 }}>
            <span className="hint">Feed</span>
            <select className="input" value={feed} onChange={(e) => setFeed(e.target.value)}>
              {feedSlugs.map((slug) => (
                <option key={slug} value={slug}>
                  {slug}
                </option>
              ))}
            </select>
          </label>
          <button
            className="btn primary"
            disabled={!ready || publishing}
            onClick={() => setConfirming(true)}
          >
            {publishing ? "Publishing…" : "Publish…"}
          </button>
        </div>

        {!target.available ? (
          <div className="hint" style={{ marginTop: 8 }}>
            Publishing is unavailable here: {target.reason}
          </div>
        ) : !insidePolicy ? (
          <div className="hint" style={{ marginTop: 8, color: "var(--amber, #b45309)" }}>
            <code>{fullName}</code> is outside the writable policy — the backend only
            writes under <code>{target.writable_prefix}*</code> and will refuse this
            target. Publishing never touches client schemas.
          </div>
        ) : (
          <div className="hint" style={{ marginTop: 8 }}>
            Target: <code>/Volumes/{`${catalog}/${schema}/${volume}`}/{feed || "<feed>"}/</code>
            {" · "}policy: writes only under <code>{target.writable_prefix}*</code>, enforced
            in code.
          </div>
        )}

        {error ? (
          <div className="error-banner" style={{ marginTop: 10 }}>
            {error}
          </div>
        ) : null}

        {result ? (
          <div className="hint" style={{ marginTop: 10 }}>
            Published {result.artifacts.length} artifact(s) to{" "}
            <code>{result.volume}</code>
            {result.volume_created ? " (volume created)" : ""}:{" "}
            {result.artifacts.map((a) => a.name).join(", ")}
          </div>
        ) : null}

        {confirming ? (
          <div className="modal-overlay" role="dialog" aria-modal="true">
            <div className="modal">
              <h2>Publish to the workspace?</h2>
              <p>
                Writes <code>{feed}</code>&apos;s report, notebook and framework artefacts to{" "}
                <code>
                  /Volumes/{catalog}/{schema}/{volume}/{feed}/
                </code>{" "}
                in Unity Catalog. Publishing is the review gate — do this only after
                looking at the feed&apos;s verdict. Files already there are not
                overwritten.
              </p>
              <div className="decision-row" style={{ marginTop: 14 }}>
                <button className="btn primary" onClick={publish} disabled={publishing}>
                  {publishing ? "Publishing…" : "Confirm — publish"}
                </button>
                <button className="btn" onClick={() => setConfirming(false)} disabled={publishing}>
                  Cancel
                </button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
