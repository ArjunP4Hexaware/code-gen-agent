// post162: Vite's `?raw` imports (a file's text) - used by the theme tests
declare module "*?raw" {
  const content: string;
  export default content;
}
