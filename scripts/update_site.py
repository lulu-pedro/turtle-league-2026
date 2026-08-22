#!/usr/bin/env python3
"""Update the Turtle League site from the goals spreadsheet CSV.

Usage:
    python3 scripts/update_site.py path/to/leaderboard.csv

Takes the cumulative CSV exported from the "Turtle League Leaderboard"
Google Sheet and updates:

  - leaderboard.html: regenerates the GAME_DATA array (standings, golden
    boot, golden team, and match history all derive from it in the page).
  - schedule.html: marks every game day present in the CSV as completed,
    fills in final scores, and removes the RSVP links for those days.

Both pages store their content as a JSON-encoded template string. This
script decodes that string, edits the readable text, re-encodes it, and
verifies before writing that its encoder reproduces the original string
byte-for-byte (so the only changes are the intended ones). Review with
`git diff` / a local server, then commit.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from turtle_stats import load_games

REPO = Path(__file__).resolve().parent.parent


# ---------- template packing ----------

def find_template(raw):
    """Return (start, end) offsets of the JSON template string in the HTML."""
    pos = 0
    for line in raw.split("\n"):
        body = line.strip()
        if body.startswith("<script") and '"<!DOCTYPE' in body:
            body = body[body.index(">") + 1:]
        if body.startswith('"<!DOCTYPE'):
            if body.endswith("</script>"):
                body = body[: -len("</script>")]
            start = raw.index(body, pos)
            return start, start + len(body)
        pos += len(line) + 1
    raise ValueError("bundler template string not found")


def encode(decoded, ascii_mode):
    # </ must stay escaped or the browser would end the <script> tag early
    return json.dumps(decoded, ensure_ascii=ascii_mode).replace("</", "<\\u002F")


def unpack(path):
    """Read an HTML file; return (raw, span, decoded template, ascii_mode)."""
    raw = path.read_text()
    start, end = find_template(raw)
    original = raw[start:end]
    decoded = json.loads(original)
    for ascii_mode in (True, False):
        if encode(decoded, ascii_mode) == original:
            return raw, (start, end), decoded, ascii_mode
    raise ValueError(
        f"{path.name}: cannot re-encode the template byte-identically; "
        "refusing to edit (the page may have been changed by another tool)"
    )


def pack(path, raw, span, decoded, ascii_mode):
    start, end = span
    new_raw = raw[:start] + encode(decoded, ascii_mode) + raw[end:]
    json.loads(new_raw[slice(*find_template(new_raw))])  # sanity: still parses
    path.write_text(new_raw)


# ---------- leaderboard.html ----------

def js_str(s):
    return json.dumps(s, ensure_ascii=False)


def update_leaderboard(decoded, games):
    entries = []
    for g in games:
        t1, t2 = g["teams"]
        s1 = ",".join(js_str(n) for n in g["scorers"][t1])
        s2 = ",".join(js_str(n) for n in g["scorers"][t2])
        entries.append(
            f'    {{ day: {g["day"]}, game: {g["game"]}, '
            f't1: {js_str(t1)}, t2: {js_str(t2)}, '
            f'scorers: {{ {js_str(t1)}: [{s1}], {js_str(t2)}: [{s2}] }} }},'
        )
    block = "GAME_DATA = [\n" + "\n".join(entries) + "\n  ];"
    new, n = re.subn(r"GAME_DATA = \[\n.*?\n  \];", block, decoded, flags=re.S)
    if n != 1:
        raise ValueError(f"expected exactly one GAME_DATA block, found {n}")
    return new


# ---------- schedule.html ----------

def update_schedule(decoded, games):
    by_day = {}
    for g in games:
        by_day.setdefault(g["day"], []).append(g)

    game_re = re.compile(
        r'(\{ field: \d+, team1: "([^"]+)", team2: "([^"]+)")(?:, score: "[^"]*")?( \})'
    )
    day_re = re.compile(r"(gameDay: (\d+), date: \"[^\"]+\",)( isCompleted: true,)?")

    out, day_games = [], None
    for line in decoded.split("\n"):
        m = day_re.search(line)
        if m:
            day = int(m.group(2))
            pending = by_day.pop(day, None)
            day_games = list(pending) if pending else None
            if day_games is not None and not m.group(3):
                line = line.replace(m.group(1), m.group(1) + " isCompleted: true,")
        if day_games is not None:
            if re.match(r"\s*(luma|meetup): ", line):
                continue
            gm = game_re.search(line)
            if gm:
                t1, t2 = gm.group(2), gm.group(3)
                match = next((g for g in day_games
                              if frozenset(g["teams"]) == frozenset((t1, t2))), None)
                if match is None:
                    raise ValueError(f"no CSV result for {t1} v {t2} on day scheduled line: {line.strip()}")
                day_games.remove(match)
                score = f'{len(match["scorers"][t1])} – {len(match["scorers"][t2])}'
                line = game_re.sub(rf'\g<1>, score: "{score}"\g<4>', line)
        out.append(line)

    if by_day:
        raise ValueError(f"CSV has game days not found in schedule.html: {sorted(by_day)}")
    return "\n".join(out)


# ---------- main ----------

def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip())
    games = load_games(sys.argv[1])
    days = sorted({g["day"] for g in games})
    print(f"CSV: {len(games)} games across game days {days}")

    lb_path = REPO / "leaderboard.html"
    raw, span, decoded, ascii_mode = unpack(lb_path)
    pack(lb_path, raw, span, update_leaderboard(decoded, games), ascii_mode)
    print(f"updated {lb_path.name}: GAME_DATA regenerated ({len(games)} games)")

    sc_path = REPO / "schedule.html"
    raw, span, decoded, ascii_mode = unpack(sc_path)
    pack(sc_path, raw, span, update_schedule(decoded, games), ascii_mode)
    print(f"updated {sc_path.name}: days {days} completed with scores")

    print("\nDone. Review with `git diff --stat` and a local preview, then commit.")


if __name__ == "__main__":
    main()
