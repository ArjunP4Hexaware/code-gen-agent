---
name: ship-staging
description: Merge feature/multi-table into main (identical-tree merge, fast-forward) and deploy the data engineers' App codegen-agent-staging, then prove it. Only on Soham's explicit word.
disable-model-invocation: true
---

# /ship-staging

Only when Soham has said to merge / deploy staging IN THIS conversation turn or the one
before - his word does not carry over to a later version.

1. The dev App must already run this exact commit, health + smoke green (`/ship-dev`).
2. `tools/check/ship.sh staging --approved` - it refuses a HEAD that is not
   `origin/feature/multi-table`, an App that is busy (someone mid-run) or a merge whose
   tree differs from feature's; it builds `git commit-tree <feature>^{tree} -p
   origin/main -p <feature>`, pushes it as a fast-forward, deploys, restores the last
   good commit on a failed deploy, checks health + smoke.
3. Report: main's new short sha, the version, health / smoke. Never change staging's
   grants or run on it without Soham's word.

The rules behind each step: `docs/PROCEDURES.md` ("Pushing", "Deploying", "The App").
