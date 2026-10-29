import { useState } from "react";
import { groupFlags } from "../flagGroups";

// post137: the feed's flags in sections (flagGroups.ts), each one collapsible,
// the ones a reviewer acts on open first. Every flag is still shown whole.
export function FlagSections({ flags }: { flags: string[] }) {
  const sections = groupFlags(flags);
  const [open, setOpen] = useState<Set<string>>(
    () => new Set(sections.filter((s) => s.open).map((s) => s.id)));
  const setAll = (value: boolean) =>
    setOpen(value ? new Set(sections.map((s) => s.id)) : new Set());

  const renderFlag = (f: string) => {
    // The HITL centerpiece: candidates awaiting a human decision
    // get called out distinctly from housekeeping flags.
    // post148: each flag is an issue card (orange bar; red for a human decision)
    const hitl = f.includes("pending engineer approval");
    return (
      <li key={f} className={`issue${hitl ? " bad flag-hitl" : ""}`}>
        {hitl ? <span className="hitl-tag">PENDING ENGINEER APPROVAL</span> : null}
        {f}
      </li>
    );
  };

  return (
    <>
      {sections.length > 1 ? (
        <div className="flag-section-tools">
          <button onClick={() => setAll(true)}>Expand all</button>
          <button onClick={() => setAll(false)}>Collapse all</button>
        </div>
      ) : null}
      {sections.map((s) => (
        <details
          key={s.id}
          className="flag-section"
          data-section={s.id}
          open={open.has(s.id)}
          onToggle={(e) => {
            const isOpen = (e.currentTarget as HTMLDetailsElement).open;
            setOpen((prev) => {
              if (prev.has(s.id) === isOpen) return prev;
              const next = new Set(prev);
              if (isOpen) next.add(s.id);
              else next.delete(s.id);
              return next;
            });
          }}
        >
          <summary>
            <span className="flag-section-title">{s.title}</span>
            <span className="flag-section-count">
              {s.flags.length} {s.id === "iig_blank" ? "sheet" : "flag"}
              {s.flags.length === 1 ? "" : "s"}
            </span>
            {s.hint ? <span className="flag-section-hint">{s.hint}</span> : null}
          </summary>
          <ul className="flag-issues">{s.flags.map(renderFlag)}</ul>
        </details>
      ))}
    </>
  );
}
