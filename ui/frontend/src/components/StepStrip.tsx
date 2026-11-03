/* post143: the step strip of a guided page — where the person is in a run.
   Steps before `active` are done (a tick), `active` is the current one; an
   `active` past the last step marks every step done. */
export function StepStrip({ steps, active }: { steps: string[]; active: number }) {
  return (
    <ol className="steps" aria-label="Steps">
      {steps.map((s, i) => (
        <li
          key={s}
          className={i === active ? "on" : i < active ? "done" : ""}
          aria-current={i === active ? "step" : undefined}
        >
          <span className="step-n" aria-hidden="true">{i < active ? "✓" : i + 1}</span>
          {s}
        </li>
      ))}
    </ol>
  );
}
