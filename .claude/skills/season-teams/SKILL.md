---
name: season-teams
description: Add, edit, remove, or reset the Teams roster content on the Turtle League site's live season page (season.html) or a past-season archive page — team names, colors, captains, and player lists.
---

# season-teams

Manages the **Teams** tab content: the roster cards showing each team's name, captain, color
identity, and player list.

Read `scripts/BUNDLER_FORMAT.md` first for how to safely decode/edit/re-encode a bundler page
(`season.html`). Never hand-edit the raw file.

## Data shape

Team data lives in a `TEAMS` array as a class field inside the decoded page:

```js
TEAMS = [
  {
    name: "Sky Monsters",
    captain: "Bettyjane",
    bg: "#deeaf7",           // card background color
    headerText: "#0055c8",   // team name text color
    captainColor: "#5a8fcc", // captain label color
    players: ["Alma","Christi","Cindy", /* ... */]
  },
  // one object per team
];
```

Pick `bg`/`headerText`/`captainColor` as a matched light/medium/dark trio in the team's identity
color (see the four existing Summer 2026 teams for the pattern — blue, gray/white, orange, green).

`players` is a flat array of first names (add `(FA)` suffix inline in scorer lists elsewhere for
free agents, but the roster list itself is just names as given).

## Where else a team name must stay in sync

A team's `name` string here must **exactly** match the same team's name used in:
- The `CC` (color-class) map in the Stats logic (see `season-stats` skill) — mismatched names
  render with no color.
- The `SCHEDULE` array's `team1`/`team2` fields (see `season-schedule` skill).
- The `GAME_DATA` array's `t1`/`t2`/`scorers` keys (see `season-stats` skill).

Renaming a team mid-season means updating it in all four places at once.

## Common tasks

**Add/edit/remove a team or player** — decode `season.html`, edit the `TEAMS` array entry, re-encode
and write via `pack()`. Adding a team also requires adding it to `CC` and to every relevant
`SCHEDULE`/`GAME_DATA` entry it plays in — this skill only owns `TEAMS` itself.

**Start a new season (reset rosters)** — replace the entire `TEAMS` array with the new season's
teams. Keep the same field shape. Pick new colors if team names/identities changed.

**Archive a finished season's rosters** — when moving a season from `season.html` into its
Past-Seasons archive page (e.g. `summer-2026.html`), the roster becomes static, final content:
copy the roster cards into the archive page's "Season Recap" tab as **plain HTML** (that page
isn't bundler-encoded — it's a finished record that won't recompute), not as a live `TEAMS` array.
Then reset `season.html`'s `TEAMS` array for the next season.

## Verification

Preview locally (`python3 -m http.server`) and check the Teams tab: every team renders with
correct colors, captain is highlighted, and the full player list appears with no name dropped or
duplicated.
