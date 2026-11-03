// GitHub-style secondary download button (small, gray, bordered) — for file
// views, where a full-size primary button would shout. Icon: Octicons
// "download-16" (MIT).
function DownloadIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 16 16" width="16" height="16" fill="currentColor">
      <path d="M2.75 14A1.75 1.75 0 0 1 1 12.25v-2.5a.75.75 0 0 1 1.5 0v2.5c0 .138.112.25.25.25h10.5a.25.25 0 0 0 .25-.25v-2.5a.75.75 0 0 1 1.5 0v2.5A1.75 1.75 0 0 1 13.25 14Z" />
      <path d="M7.25 7.689V2a.75.75 0 0 1 1.5 0v5.689l1.97-1.969a.749.749 0 1 1 1.06 1.06l-3.25 3.25a.749.749 0 0 1-1.06 0L4.22 6.78a.749.749 0 1 1 1.06-1.06l1.97 1.969Z" />
    </svg>
  );
}

/** ``label`` omitted = the icon-only variant (``title`` is then its name). */
export function DownloadButton({
  href,
  label,
  title,
}: {
  href: string;
  label?: string;
  title: string;
}) {
  return (
    <a
      className={`gh-btn${label ? "" : " gh-btn-icon"}`}
      href={href}
      download
      title={title}
      aria-label={title}
    >
      <DownloadIcon />
      {label ? <span>{label}</span> : null}
    </a>
  );
}
