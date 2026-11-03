import { useEffect, useState } from "react";
import { api, type HealthResponse, type StorageRootState } from "../api";

// Shown where the document chooser lists nothing (2026-10-07): every storage
// root the App reads, its env var, its value and a live probe — so an empty
// panel says WHICH variable is unset or WHICH folder is not shared with the
// App's service principal, instead of a bare "nothing found".
const LABELS: Record<StorageRootState, string> = {
  readable: "readable",
  empty: "empty",
  not_shared: "not shared with the App",
  unset: "not set",
  invalid: "invalid URI",
  error: "error",
  timeout: "no answer",
};

export function StorageRoots() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [failed, setFailed] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    api
      .health()
      .then((h) => live && setHealth(h))
      .catch((e: Error) => live && setFailed(e.message));
    return () => {
      live = false;
    };
  }, []);

  if (failed) return <p className="hint">Storage check unavailable: {failed}</p>;
  if (!health) return <p className="hint">Checking the storage roots…</p>;
  return (
    <div className="storage-roots" style={{ textAlign: "left", marginTop: 8 }}>
      <p className="hint">
        Storage roots this App reads (probed now, as <code>{health.principal}</code>):
      </p>
      <table className="table">
        <thead>
          <tr>
            <th>Env var</th>
            <th>Value</th>
            <th>State</th>
            <th>Detail</th>
          </tr>
        </thead>
        <tbody>
          {health.roots.map((r, i) => (
            <tr key={`${r.env}-${i}`}>
              <td>
                <code>{r.env}</code>
              </td>
              <td>{r.value ? <code>{r.value}</code> : <span className="hint">—</span>}</td>
              <td>
                <span className={r.state === "readable" ? "pill req-filled" : "pill req-missing"}>
                  {LABELS[r.state] ?? r.state}
                </span>
              </td>
              <td className="hint">{r.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
