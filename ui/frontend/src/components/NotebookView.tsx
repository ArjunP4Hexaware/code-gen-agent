import Prism from "prismjs";
import "prismjs/components/prism-python";
import { useMemo } from "react";
import { renderMarkdown } from "../markdown";

interface NotebookCell {
  cell_type: string;
  id?: string;
  source: string | string[];
}

const cellText = (s: string | string[]) => (Array.isArray(s) ? s.join("") : s);

function CodeCell({ source }: { source: string }) {
  const html = useMemo(
    () => Prism.highlight(source, Prism.languages.python, "python"),
    [source],
  );
  return (
    <div className="nb-cell nb-code">
      <pre dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}

/** Renders a generated .ipynb: markdown cells as prose, code cells highlighted. */
export function NotebookView({ content }: { content: string }) {
  const cells = useMemo<NotebookCell[] | null>(() => {
    try {
      const nb = JSON.parse(content);
      return Array.isArray(nb.cells) ? nb.cells : null;
    } catch {
      return null;
    }
  }, [content]);

  if (!cells) return <div className="empty">Could not parse the notebook.</div>;
  return (
    <div className="notebook">
      {cells.map((c, i) =>
        c.cell_type === "markdown" ? (
          <div
            key={c.id ?? i}
            className="nb-cell nb-md report-md"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(cellText(c.source)) }}
          />
        ) : (
          <CodeCell key={c.id ?? i} source={cellText(c.source)} />
        ),
      )}
    </div>
  );
}
