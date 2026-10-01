---
name: repo-fence
description: "Keep this trading program inside clay10fields/database on main. Use before any GitHub read or write for the book, the recorder, or research notes. Not for other repos."
type: workflow
lifecycle: active
---

# Repo fence

The program is `clay10fields/database`, branch `main`.

## Allowed

Read and write that repo. Research notes go in `research/`. Raw files in `raw/` are append-only. Do not edit them. Do not place orders. The recorder workflow may be dispatched. It may not be pointed at another repo.

## Not allowed

Do not open, clone, or edit `crypto-research-machine`. Do not open, clone, or edit `hype-pressure-kit`. Do not create a side branch for a note. Do not leave a result only in the chat. If it is not on `main`, the next session will not see it.

## After a write

Confirm the file URL is `https://github.com/clay10fields/database/blob/main/...`. If the index at `research/README.md` should point at the new file, update that row in the same commit.
