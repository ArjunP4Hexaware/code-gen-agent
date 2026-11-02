/* post162: the colour theme BEFORE first paint (no flash of the wrong theme).
   A plain blocking script (not a module, not deferred) loaded from the App's own
   origin, so the CSP's script-src 'self' allows it - never inline. Dark is the
   default; a saved "light" / "dark" choice (src/theme.ts, the header toggle) wins.
   Storage blocked = the default, nothing else breaks. */
(function () {
  var theme = "dark";
  try {
    var saved = window.localStorage.getItem("codegen.theme.v1");
    if (saved === "light" || saved === "dark") theme = saved;
  } catch (e) {
    /* storage unavailable: the default */
  }
  document.documentElement.setAttribute("data-theme", theme);
})();
