// Playwright smoke: open a page, wait for render, screenshot, print title + console errors.
// Usage: node tools/check/smoke.cjs <url> <png>   (tools/check/ship.sh runs it)
// Deployed App: set CODEGEN_BEARER to an OAuth token (databricks auth token -p <profile>);
// it is passed as a header only, never written anywhere.
const path = require("path");
// dev_bootstrap installs Playwright under ui/frontend (Chromium in /tmp/pw)
const { chromium } = require(path.join(__dirname, "..", "..", "ui", "frontend",
                                       "node_modules", "playwright"));

const url = process.argv[2] || "http://127.0.0.1:8599/";
const png = process.argv[3] || "/tmp/smoke.png";

(async () => {
  const browser = await chromium.launch();
  const ctxOpts = { viewport: { width: 1366, height: 900 } };
  if (process.env.CODEGEN_BEARER) {
    ctxOpts.extraHTTPHeaders = { Authorization: `Bearer ${process.env.CODEGEN_BEARER}` };
  }
  const page = await (await browser.newContext(ctxOpts)).newPage();
  const errors = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(`pageerror: ${e.message}`));

  const resp = await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForSelector("h1", { timeout: 30000 });
  await page.screenshot({ path: png, fullPage: true });

  console.log(`status:  ${resp && resp.status()}`);
  console.log(`title:   ${await page.title()}`);
  console.log(`h1:      ${(await page.textContent("h1")).trim()}`);
  console.log(`errors:  ${errors.length}`);
  errors.forEach((e) => console.log(`  - ${e}`));
  console.log(`saved:   ${png}`);
  await browser.close();
  process.exit(errors.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });
