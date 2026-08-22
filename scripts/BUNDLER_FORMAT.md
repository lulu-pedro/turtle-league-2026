# The bundler page format

`season.html` (and, historically, `leaderboard.html`/`schedule.html`/`teams.html`) are not plain
HTML files. The entire page — markup, inline styles, and a small React-like logic class with
`{{ }}` bindings, `sc-for`, `sc-if` — is JSON-encoded as one long string inside a
`<script type="__bundler/template">` tag (recognizable by the string starting with
`"<!DOCTYPE ...`). A tiny bootstrap script in `<head>` decodes and hydrates it into the visible
page at runtime.

**Never hand-edit that JSON string in a text editor.** A single stray character (an unescaped
quote, a wrong `/`) silently corrupts the page. Always go through: decode → edit the plain
JS/HTML → re-encode → verify the re-encoding reproduces the original byte-for-byte → only then
write the file.

`scripts/update_site.py` already implements this safely and is the canonical, reusable
implementation — import its helpers rather than reimplementing them:

```python
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
from update_site import unpack, pack

path = Path("season.html")
raw, span, decoded, ascii_mode = unpack(path)   # decoded: full plain-text HTML+JS string

# ... edit `decoded` with string ops / regex ...

pack(path, raw, span, decoded, ascii_mode)      # re-encodes, sanity-checks, writes
```

`unpack()` raises instead of proceeding if it can't reproduce the original template
byte-for-byte — that's a safety net, not a bug to work around. If you hit it, stop and
investigate rather than forcing the write.

After any edit: run `git diff --stat` to confirm only the intended region changed, and preview
with `python3 -m http.server` from the repo root before committing.

## Where things live inside the decoded template

The decoded string is standard HTML with a `<script>` block near the end containing a class with:
- Data arrays as class fields (`TEAMS`, `SCHEDULE`, `GAME_DATA` — see the `season-teams`,
  `season-schedule`, `season-stats` skills for each one's exact shape).
- A `renderVals()` method that computes everything the template's `{{ }}`/`sc-for`/`sc-if`
  bindings read — if you add a field to a data array, check whether `renderVals()` (or a
  helper it calls) needs to expose a derived value for it too.
- State (e.g. `menuOpen` for the mobile nav, and — once tabs exist on `season.html` — `activeTab`)
  read via `this.state` and changed via `this.setState(...)`, following the same pattern already
  used for the mobile hamburger toggle (`toggleMenu` / `navClass` in `renderVals()`).

## Team display constants

Team display colors are keyed by team name in a `CC` (color-class) map, e.g.:
```js
CC = { "Peel Madrid": 'tc-orange', "Sky Monsters": 'tc-blue', "Sweaty Yetis": 'tc-white', "Mint Conditions": 'tc-green' };
```
This map (or its Fall-season equivalent) must stay in sync with whatever team names
`TEAMS`/`SCHEDULE`/`GAME_DATA` use — a mismatched name silently renders with no team color.
