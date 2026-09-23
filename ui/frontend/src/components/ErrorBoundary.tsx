import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
  /** What the boundary guards, for the message ("the document chooser"). */
  label?: string;
}

interface State {
  error: Error | null;
  stack: string | null;
}

/**
 * A render error inside the children degrades to THIS card — message,
 * component stack, Try again / Reload — instead of blanking the page.
 * One sits around the routes in App.tsx (the shell chrome stays), one
 * around the document chooser / pairing panel (a bad status payload costs
 * one card, not the page).
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null, stack: null };

  static getDerivedStateFromError(error: Error): Partial<State> {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.setState({ stack: info.componentStack ?? null });
    console.error("[ui] render failed", this.props.label ?? "", error, info.componentStack);
  }

  render(): ReactNode {
    const { error, stack } = this.state;
    if (!error) return this.props.children;
    const what = this.props.label ? `${this.props.label} could not be shown` : "This part of the page could not be shown";
    return (
      <div className="flag-hitl error-boundary" role="alert" style={{ padding: "10px 12px", margin: "8px 0" }}>
        <strong>{what}.</strong>{" "}
        <span className="hint">{error.name}: {error.message}</span>
        {stack ? (
          <pre className="hint" style={{ whiteSpace: "pre-wrap", fontSize: 11, marginTop: 6 }}>
            {stack.trim()}
          </pre>
        ) : null}
        <div style={{ marginTop: 8, display: "flex", gap: 6 }}>
          <button className="btn" onClick={() => this.setState({ error: null, stack: null })}>
            Try again
          </button>
          <button className="btn" onClick={() => window.location.reload()}>
            Reload
          </button>
        </div>
      </div>
    );
  }
}
