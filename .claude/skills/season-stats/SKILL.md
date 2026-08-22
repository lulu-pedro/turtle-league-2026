---
name: season-stats
description: Add goal-scorer results, and understand/update standings, Golden Boot, and Golden Team computations, on the Turtle League site's live season page (season.html). Also used to derive final award figures when a season ends.
---

# season-stats

Manages the **Stats** tab: standings, Golden Boot (top scorer), Golden Team (most distinct
scorers), and match history — all computed client-side from one source array, `GAME_DATA`.

Read `scripts/BUNDLER_FORMAT.md` first for how to safely decode/edit/re-encode a bundler page
(`season.html`). Never hand-edit the raw file.

## Data shape

```js
GAME_DATA = [
  { day: 1, game: 1, t1: "Sky Monsters", t2: "Peel Madrid",
    scorers: { "Sky Monsters": ["Alma","Em G"], "Peel Madrid": [] } },
  // one entry per game played — day 1 has two games (game: 1, game: 2), etc.
];
```

- `scorers` lists **one entry per goal**, by scorer name, keyed by team name — not a goal count.
  A 0-0 draw still needs an entry with both arrays empty (don't omit the game).
  A free agent scorer is written as `"Name (FA)"` inline in the array — no separate field.
- `t1`/`t2` must exactly match team names used in `TEAMS` and `SCHEDULE` (see `season-teams` and
  `season-schedule`), and must have a matching entry in the `CC` color map:
  ```js
  CC = { "Peel Madrid": 'tc-orange', "Sky Monsters": 'tc-blue', "Sweaty Yetis": 'tc-white', "Mint Conditions": 'tc-green' };
  ```

## How everything is derived (don't hand-maintain these — they're computed)

`parseGames()` turns each `GAME_DATA` entry into `{ day, game, teams: [t1,t2], goals: {t1: n, t2: n}, scorers }`,
where goal counts are simply `scorers[team].length`. From that:
- `getStandings(games)` — W/D/L/points/goal-difference table, 3 points a win, 1 each for a draw,
  sorted by points then goal difference.
- `getGoldenBoot(games)` — tallies goals per scorer name across all games, sorted descending.
- `getGoldenTeam(games)` — counts **distinct** scorers per team (a `Set`, not a sum), sorted
  descending — this is "most different players who scored," not most goals.
- Match history is the same games, newest-first, with a per-game scorer list and a
  point-swing string (`"Team +3"` or `"+1 each"` for a draw).

If you're adding a new derived stat, add a method following this pattern and expose it from
`renderVals()` — don't compute it inline in the template.

## Common tasks

**Add a game's results** — append a `GAME_DATA` entry (or two, if two games were played in one
slot) once you know the scorers. Keep `schedule.html`'s `score:` field for that same matchup in
sync (see `season-schedule`) — they're two independent sources of the same number and nothing
enforces agreement automatically.

**Bulk-import from the season spreadsheet CSV** — `scripts/turtle_stats.py`'s `load_games()`
parses the "Turtle League Leaderboard" Google Sheet CSV export into the same shape this skill
uses; `scripts/update_site.py` already wires that into a full `GAME_DATA` regeneration
(`update_leaderboard()`). Prefer running that script over hand-entering many games — hand-entry
is for one-off corrections or small updates.

**Derive final awards when a season ends** — the Winners page's Golden Boot/Silver Boot and
Golden Team figures are just the top one/two entries of `getGoldenBoot()`/`getGoldenTeam()` run
against the season's final, complete `GAME_DATA`. Decode the page, temporarily run
`parseGames()`/`getGoldenBoot()`/`getGoldenTeam()`/`getStandings()` logic (e.g. via `node`, or by
porting the same reducer to a quick Python script) against the final `GAME_DATA` to get the
numbers, rather than eyeballing the raw scorer arrays by hand.

**Start a new season (reset stats)** — replace `GAME_DATA` with an empty array and update `CC` to
the new season's team names/colors (coordinate with `season-teams`).

**Archive a finished season's stats** — the final standings table (and the awards derived above)
becomes **static, hand-written HTML** on that season's Past-Seasons archive page (e.g.
`summer-2026.html`, "Winners & Stats" tab) — paste in the computed final numbers once, since a
finished season's standings never change again. Don't try to keep a live `GAME_DATA` array on an
archive page.

## Verification

Preview locally (`python3 -m http.server`) and check the Stats tab: standings order and points
look right for a couple of known results, Golden Boot/Golden Team top entries match what you'd
expect from the games you just added, and match history shows the new game(s) with correct
scorers and point-swing text.
