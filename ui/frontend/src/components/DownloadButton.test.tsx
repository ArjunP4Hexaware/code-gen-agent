import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { downloadHref } from "../api";
import { CodeView } from "./CodeView";
import { DownloadButton } from "./DownloadButton";

describe("DownloadButton", () => {
  it("is a small GitHub-style link that downloads, with a label", () => {
    const html = renderToStaticMarkup(
      <DownloadButton href="/x.ipynb" label="Download .ipynb" title="Download x.ipynb" />,
    );
    expect(html).toMatch(/^<a class="gh-btn" href="\/x.ipynb" download="" /);
    expect(html).toContain("<span>Download .ipynb</span>");
    expect(html).not.toContain("primary");
  });

  it("has an icon-only variant that still names itself", () => {
    const html = renderToStaticMarkup(<DownloadButton href="/a.py" title="Download a.py" />);
    expect(html).toContain('class="gh-btn gh-btn-icon"');
    expect(html).toContain('aria-label="Download a.py"');
    expect(html).not.toContain("<span>");
  });
});

describe("the file view", () => {
  it("offers the open file's own download in its path bar", () => {
    const href = downloadHref("cv_feed", "pipeline/reader.py");
    expect(href).toBe("/api/feeds/cv_feed/download?path=pipeline%2Freader.py");
    const html = renderToStaticMarkup(
      <CodeView path="pipeline/reader.py" content="x = 1" downloadHref={href} />,
    );
    expect(html).toContain(`href="${href.replace(/&/g, "&amp;")}"`);
    expect(html).toContain('aria-label="Download reader.py"');
  });

  it("has no download button when no href is given", () => {
    const html = renderToStaticMarkup(<CodeView path="a.py" content="x = 1" />);
    expect(html).not.toContain("gh-btn");
  });
});
