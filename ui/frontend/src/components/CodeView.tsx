import Prism from "prismjs";
import "prismjs/components/prism-json";
import "prismjs/components/prism-markdown";
import "prismjs/components/prism-python";
import "prismjs/components/prism-sql";
import "prismjs/components/prism-toml";
import { useMemo } from "react";

const LANG_BY_EXT: Record<string, string> = {
  py: "python",
  sql: "sql",
  json: "json",
  toml: "toml",
  md: "markdown",
};

export function CodeView({ path, content }: { path: string; content: string }) {
  const html = useMemo(() => {
    const ext = path.split(".").pop() ?? "";
    const lang = LANG_BY_EXT[ext];
    const grammar = lang ? Prism.languages[lang] : undefined;
    if (!grammar) {
      return null;
    }
    return Prism.highlight(content, grammar, lang);
  }, [path, content]);

  return (
    <div className="code-pane">
      <div className="path-bar">{path}</div>
      {html !== null ? (
        <pre dangerouslySetInnerHTML={{ __html: html }} />
      ) : (
        <pre>{content}</pre>
      )}
    </div>
  );
}
