---
name: season-schedule
description: Add, edit, or reset the Schedule & RSVP tab content on the Turtle League site's live season page (season.html) or a past-season archive page — game days, matchups, RSVP links, scores, and playoff seeding.
---

# season-schedule

Manages the **Schedule & RSVP** tab content: game days, per-day matchups, RSVP links for
upcoming days, final scores for completed days, and the playoffs/finals bracket.

Read `scripts/BUNDLER_FORMAT.md` first for how to safely decode/edit/re-encode a bundler page
(`season.html`). Never hand-edit the raw file.

## Data shape

Schedule data lives in a `SCHEDULE` array as a class field inside the decoded page — one object
per game day:

```js
SCHEDULE = [
  {
    gameDay: 1, date: "Wed, June 10", isCompleted: true,
    slots: [
      { time: "6:30 PM", games: [
        { field: 1, team1: "Sky Monsters", team2: "Peel Madrid", score: "2 – 0" },
        { field: 2, team1: "Sweaty Yetis", team2: "Mint Conditions", score: "3 – 0" }
      ]},
      { time: "7:30 PM", games: [ /* ... */ ]}
    ]
  },
  // ...
  {
    gameDay: "Playoffs & Finals", date: "Tues, Aug 4", isPlayoff: true,
    slots: [
      { time: "6:30 PM", games: [
        { field: 1, team1: "Sweaty Yetis", team2: "Peel Madrid", seed1: "1st Seed", seed2: "4th Seed" },
        { field: 2, team1: "Sky Monsters", team2: "Mint Conditions", seed1: "2nd Seed", seed2: "3rd Seed" }
      ]},
      { time: "7:30 PM", games: [
        { field: 1, team1: "Winner Field 1", team2: "Winner Field 2" }
      ]}
    ]
  }
];
```

Key fields and rendering rules (see `renderScheduleDays()`-equivalent in the decoded page):
- `gameDay` is normally a number (rendered as "Game Day N"); the playoff entry uses a literal
  string (e.g. `"Playoffs & Finals"`) instead, shown as-is.
- `isCompleted: true` — day has been played. Once true, RSVP buttons stop rendering for that day
  and `luma`/`meetup` fields (if present) should be removed.
- `isPlayoff: true` — suppresses RSVP buttons regardless of `isCompleted`, and enables `seed1`/
  `seed2` rendering (shown as `"Team Name (1st Seed)"`).
- A **not-yet-played, non-playoff day** carries RSVP links directly on the day object:
  `luma: "https://..."` (rostered players — green "Roster RSVP" button) and
  `meetup: "https://..."` (free agents — red "Free Agent RSVP" button). Remove both once the day
  is marked completed.
- A played game has `score: "X – Y"` (en dash, spaces around it) on the game object instead of
  (or in addition to being derived from) the goal-scorer counts in `GAME_DATA` — see
  `season-stats`. Keep the two in sync: the `score` string here should equal the scorer-count
  totals there.
- `team1`/`team2` must exactly match names used in `TEAMS` and `GAME_DATA` (see `season-teams`
  and `season-stats`).

## Common tasks

**Mark a day complete / add a score** — set `isCompleted: true`, add `score: "X – Y"` to each
game, remove that day's `luma`/`meetup` fields. If you have final CSV results, prefer
`scripts/update_site.py`'s `update_schedule()` logic (matches games by team-name pair, fills in
scores, strips RSVP lines) — reuse that function rather than hand-writing the same regex logic
again for a bulk update.

**Add a new game day / set up playoffs** — append a `SCHEDULE` entry following the shape above;
for playoffs, use `isPlayoff: true` and `seed1`/`seed2` once seeding is known, and add the
winner-TBD final slot with plain team names (`"Winner Field 1"`) until the semifinal results are in.

**Start a new season (reset schedule)** — replace the entire `SCHEDULE` array with the new
season's fixtures. Each not-yet-played day needs real `luma`/`meetup` RSVP links before publishing
— don't leave placeholder URLs live.

**Archive a finished season's schedule** — once a season is over, its full `SCHEDULE` (every day
completed, playoffs resolved) becomes the "Season Recap" content on that season's Past-Seasons
archive page (e.g. `summer-2026.html`), rendered as **plain, static HTML** (no bundler, no RSVP
buttons — the season is over) rather than a live `SCHEDULE` array. Then reset `season.html`'s
`SCHEDULE` array for the next season.

## Verification

Preview locally (`python3 -m http.server`) and check the Schedule tab: completed days show final
scores and no RSVP buttons, upcoming days show working RSVP buttons and no score, and the playoff
bracket shows correct seeds with the final's teams resolved once known.
