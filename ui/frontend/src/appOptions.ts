/* post91: what the App offers (config output.app_options). Notebooks are shown
   only when "notebook" is offered; a backend that sends no list = everything on.
   To show notebooks again: config/config.yaml output.app_options: [notebook, framework]. */
export function notebooksOffered(options: string[] | null | undefined): boolean {
  return !options || options.includes("notebook");
}
