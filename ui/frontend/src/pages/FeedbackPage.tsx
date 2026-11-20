// post215: Feedback on the App - send a bug report or a suggestion, with up to 5
// screenshots (chosen, dropped or pasted), and see what you sent and its status. The
// feedback admins (the state root's feedback_admins.txt) also see everyone's and set the
// status. Ported from the STTM agent's App; nothing sent here reaches a model or a run.
import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  type FeedbackItem,
  type FeedbackKind,
  type FeedbackList,
  type FeedbackStatus,
} from "../api";
import { ErrorCard } from "../components/ErrorCard";
import { Icon } from "../components/Icons";

export const MAX_IMAGES = 5;
export const MAX_BYTES = 5 * 1024 * 1024;
const TYPES = ["image/png", "image/jpeg", "image/gif", "image/webp"];
export const STATUS_WORDS: Record<FeedbackStatus, string> = {
  new: "New",
  in_progress: "In progress",
  done: "Done",
  declined: "Declined",
};
export const KIND_WORDS: Record<FeedbackKind, string> = { bug: "Bug report", suggestion: "Suggestion" };

interface Shot {
  file: File;
  url: string;
}

/** "demo_20261120_100000" -> the run's start time, in the reader's locale. */
export function runWhen(run: string): string {
  const m = /^demo_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})$/.exec(run);
  if (!m) return run;
  const d = new Date(Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]));
  return `Run started ${d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}`;
}

function stamp(iso: string): string {
  const d = new Date(iso);
  return isNaN(d.getTime()) ? "" : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

const readDataUrl = (file: File) =>
  new Promise<string>((ok, fail) => {
    const reader = new FileReader();
    reader.onload = () => ok(String(reader.result));
    reader.onerror = () => fail(new Error("A screenshot could not be read."));
    reader.readAsDataURL(file);
  });

function errorWords(err: unknown): string {
  return err instanceof Error ? err.message : String(err);
}

export function FeedbackPage() {
  const [kind, setKind] = useState<FeedbackKind>("bug");
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [run, setRun] = useState("");
  const [runs, setRuns] = useState<string[]>([]);
  const [shots, setShots] = useState<Shot[]>([]);
  const [message, setMessage] = useState<{ text: string; bad: boolean } | null>(null);
  const [sending, setSending] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [all, setAll] = useState(false);
  const [list, setList] = useState<FeedbackList | null>(null);
  const [listError, setListError] = useState<unknown>(null);
  const shotsRef = useRef<Shot[]>([]);
  shotsRef.current = shots;

  const load = useCallback(async (everyone: boolean) => {
    try {
      setList(await api.feedbackList(everyone));
      setListError(null);
    } catch (err) {
      setListError(err);
    }
  }, []);

  useEffect(() => {
    void load(all);
  }, [all, load]);

  useEffect(() => {
    api.feedbackRuns().then((r) => setRuns(r.runs)).catch(() => setRuns([]));
    return () => shotsRef.current.forEach((s) => URL.revokeObjectURL(s.url));
  }, []);

  const addFiles = (files: File[]) => {
    setMessage(null);
    const next = [...shots];
    for (const file of files) {
      if (!TYPES.includes(file.type)) {
        setMessage({ text: `${file.name || "That file"} is not a PNG, JPEG, GIF or WebP image.`, bad: true });
        continue;
      }
      if (file.size > MAX_BYTES) {
        setMessage({ text: `${file.name || "That screenshot"} is over 5 MB.`, bad: true });
        continue;
      }
      if (next.length >= MAX_IMAGES) {
        setMessage({ text: `At most ${MAX_IMAGES} screenshots.`, bad: true });
        break;
      }
      next.push({ file, url: URL.createObjectURL(file) });
    }
    setShots(next);
  };

  const removeShot = (index: number) => {
    URL.revokeObjectURL(shots[index].url);
    setShots(shots.filter((_s, i) => i !== index));
  };

  const send = async () => {
    if (!title.trim() || !text.trim()) {
      setMessage({ text: "Add a title and some details first.", bad: true });
      return;
    }
    setSending(true);
    setMessage({ text: "Sending…", bad: false });
    try {
      const images = await Promise.all(shots.map(async (s) => ({ data: await readDataUrl(s.file) })));
      await api.sendFeedback({ kind, title: title.trim(), text: text.trim(), run: run || null, images });
      shots.forEach((s) => URL.revokeObjectURL(s.url));
      setShots([]);
      setTitle("");
      setText("");
      setRun("");
      setMessage({ text: "Thanks - your feedback was sent.", bad: false });
      void load(all);
    } catch (err) {
      setMessage({ text: errorWords(err), bad: true });
    } finally {
      setSending(false);
    }
  };

  const changeStatus = async (item: FeedbackItem, status: FeedbackStatus) => {
    try {
      const saved = await api.setFeedbackStatus(item.sub_id, status);
      setList((current) =>
        current && { ...current, items: current.items.map((i) => (i.sub_id === saved.sub_id ? saved : i)) });
    } catch (err) {
      setMessage({ text: errorWords(err), bad: true });
    }
  };

  return (
    <div className="landing">
      <div className="landing-head">
        <h1 className="landing-title">Feedback on the agent</h1>
        <p className="landing-lead">
          Tell us what went wrong or what would make the agent better. Add screenshots if they
          help. Feedback goes to the people who run the agent; the agent itself never reads it.
        </p>
      </div>

      <section
        className="card fb-form"
        aria-label="Send feedback"
        onPaste={(e) => {
          const files = Array.from(e.clipboardData?.files ?? []).filter((f) => f.type.startsWith("image/"));
          if (files.length) {
            e.preventDefault();
            addFiles(files);
          }
        }}
      >
        <div className="fb-field">
          <span className="fb-label" id="fb-kind-label">Type</span>
          <div className="fb-seg" role="group" aria-labelledby="fb-kind-label">
            {(Object.keys(KIND_WORDS) as FeedbackKind[]).map((k) => (
              <button
                key={k}
                type="button"
                className="btn"
                aria-pressed={kind === k}
                onClick={() => setKind(k)}
              >
                {KIND_WORDS[k]}
              </button>
            ))}
          </div>
        </div>
        <label className="fb-field">
          <span className="fb-label">Title</span>
          <input
            className="fb-input"
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="One line, e.g. The IIG left a column blank"
            autoComplete="off"
          />
        </label>
        <label className="fb-field">
          <span className="fb-label">Details</span>
          <textarea
            className="fb-input fb-textarea"
            maxLength={10000}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="What happened, what you expected, or what you'd like the agent to do"
          />
        </label>
        <label className="fb-field">
          <span className="fb-label">
            Related run <span className="fb-opt">(optional)</span>
          </span>
          <select className="fb-input" value={run} onChange={(e) => setRun(e.target.value)}>
            <option value="">None</option>
            {runs.map((r) => (
              <option key={r} value={r}>
                {runWhen(r)}
              </option>
            ))}
          </select>
        </label>
        <div className="fb-field">
          <span className="fb-label">
            Screenshots <span className="fb-opt">(optional, up to 5 images, 5 MB each)</span>
          </span>
          <label
            className={`dropzone fb-drop${dragOver ? " over" : ""}`}
            onDragEnter={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={(e) => { e.preventDefault(); setDragOver(false); }}
            onDrop={(e) => {
              e.preventDefault();
              setDragOver(false);
              addFiles(Array.from(e.dataTransfer.files));
            }}
          >
            <span className="dropzone-icon"><Icon name="upload" size={28} /></span>
            <span className="dropzone-main">
              Drag screenshots here, paste one (Ctrl+V), or <u>browse</u>
            </span>
            <span className="dropzone-sub">PNG, JPEG, GIF or WebP</span>
            <input
              type="file"
              className="visually-hidden"
              multiple
              accept="image/png,image/jpeg,image/gif,image/webp"
              onChange={(e) => {
                const files = Array.from(e.target.files ?? []);
                e.target.value = "";
                addFiles(files);
              }}
            />
          </label>
          {shots.length ? (
            <ul className="fb-thumbs">
              {shots.map((s, i) => (
                <li key={s.url} className="fb-thumb">
                  <img src={s.url} alt={`Screenshot ${i + 1}`} />
                  <button
                    type="button"
                    className="fb-thumb-remove"
                    aria-label={`Remove screenshot ${i + 1}`}
                    onClick={() => removeShot(i)}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
        <p className="fb-warn">
          Don't include member data or other PHI in screenshots or text - crop or blur it first.
        </p>
        <div className="decision-row">
          <button type="button" className="btn primary" disabled={sending} onClick={() => void send()}>
            Send feedback
          </button>
          <span className={`fb-msg${message?.bad ? " bad" : ""}`} role="status" aria-live="polite">
            {message?.text ?? ""}
          </span>
        </div>
      </section>

      <section className="card" aria-label="Sent feedback">
        <div className="card-head">
          <h2>{all ? "Everyone's feedback" : "Your feedback"}</h2>
          {list?.is_admin ? (
            <div className="fb-seg" role="group" aria-label="Whose feedback">
              <button type="button" className="btn" aria-pressed={!all} onClick={() => setAll(false)}>
                Mine
              </button>
              <button type="button" className="btn" aria-pressed={all} onClick={() => setAll(true)}>
                Everyone's
              </button>
            </div>
          ) : null}
        </div>
        {listError ? (
          <ErrorCard error={listError} title="The feedback could not be loaded." />
        ) : list === null ? (
          <div className="loading-card" aria-busy="true" aria-label="loading">
            <span className="spinner" />
            <span>Loading your feedback…</span>
          </div>
        ) : list.items.length === 0 ? (
          <p className="card-sub">No feedback sent yet.</p>
        ) : (
          <ul className="fb-items">
            {list.items.map((item) => (
              <li key={item.sub_id} className="fb-item">
                <div className="fb-top">
                  <span className="pill info">{KIND_WORDS[item.kind] ?? item.kind}</span>
                  <span className="fb-item-title">{item.title}</span>
                  <span className={`pill fb-status fb-st-${item.status}`}>
                    {STATUS_WORDS[item.status] ?? item.status}
                  </span>
                </div>
                <div className="fb-meta">
                  {[stamp(item.created_at), all ? item.user : null, item.run ? runWhen(item.run) : null]
                    .filter(Boolean)
                    .join(" · ")}
                </div>
                <div className="fb-body">{item.text}</div>
                {item.images.length ? (
                  <ul className="fb-thumbs">
                    {item.images.map((name, i) => {
                      const src = `/api/feedback/${encodeURIComponent(item.sub_id)}/images/${encodeURIComponent(name)}`;
                      return (
                        <li key={name} className="fb-thumb">
                          <a href={src} target="_blank" rel="noopener noreferrer" title="Open full size">
                            <img src={src} alt={`Screenshot ${i + 1}`} loading="lazy" />
                          </a>
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
                {list.is_admin ? (
                  <label className="fb-status-set">
                    Status
                    <select
                      className="fb-input"
                      value={item.status}
                      onChange={(e) => void changeStatus(item, e.target.value as FeedbackStatus)}
                    >
                      {(Object.keys(STATUS_WORDS) as FeedbackStatus[]).map((s) => (
                        <option key={s} value={s}>
                          {STATUS_WORDS[s]}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
