import { describe, expect, it } from "vitest";
import { notebooksOffered } from "./appOptions";

describe("notebooksOffered (post91)", () => {
  it("is on only when the App offers notebook, or says nothing", () => {
    expect(notebooksOffered(["notebook", "framework"])).toBe(true);
    expect(notebooksOffered(["framework"])).toBe(false);
    expect(notebooksOffered(undefined)).toBe(true);     // an older backend: as before
  });
});
