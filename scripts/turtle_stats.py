#!/usr/bin/env python3
"""Turtle League stats from the goals spreadsheet CSV.

Usage:
    python3 turtle_stats.py path/to/leaderboard.csv

Expects the CSV exported from the "Turtle League Leaderboard" Google Sheet,
with columns: Game Day, Field, Game #, Game, Team, Goal, Goalscorer, Date.
Each row is one goal; a row with Goal = 0 records a game with no goals
(so 0-0 draws still count in the standings).
"""

import csv
import sys
from collections import defaultdict

TEAM_NAMES = {
    "Blue": "Sky Monsters",
    "Orange": "Peel Madrid",
    "White": "Sweaty Yetis",
    "Green": "Mint Conditions",
}

COLORS = {
    "Sky Monsters": "\033[94m",
    "Peel Madrid": "\033[33m",
    "Sweaty Yetis": "\033[37m",
    "Mint Conditions": "\033[32m",
}
RESET = "\033[0m"


def team_name(color):
    return TEAM_NAMES.get(color.strip(), color.strip())


def colored(team, text=None):
    if not sys.stdout.isatty():
        return text or team
    return COLORS.get(team, "") + (text or team) + RESET


def load_games(path):
    """Group goal rows into games keyed by (day, game #, matchup)."""
    games = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            row = {k.strip(): (v or "").strip() for k, v in row.items() if k}
            matchup = row["Game"].replace(" vs ", " v ")
            t1, t2 = (team_name(t) for t in matchup.split(" v "))
            key = (int(row["Game Day"]), int(row["Game #"]), frozenset((t1, t2)))
            game = games.setdefault(key, {
                "day": int(row["Game Day"]),
                "game": int(row["Game #"]),
                "date": row["Date"],
                "teams": (t1, t2),
                "scorers": {t1: [], t2: []},
            })
            if row["Goal"] == "1" and row["Team"]:
                game["scorers"][team_name(row["Team"])].append(row["Goalscorer"])
    return sorted(games.values(), key=lambda g: (g["day"], g["game"]))


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__.strip())
    games = load_games(sys.argv[1])

    table = {t: {"w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0}
             for t in TEAM_NAMES.values()}
    boot = defaultdict(int)
    scorers_by_team = defaultdict(set)

    for g in games:
        t1, t2 = g["teams"]
        g1, g2 = len(g["scorers"][t1]), len(g["scorers"][t2])
        for team in (t1, t2):
            for name in g["scorers"][team]:
                boot[name] += 1
                scorers_by_team[team].add(name)
        a, b = table[t1], table[t2]
        a["gf"] += g1; a["ga"] += g2
        b["gf"] += g2; b["ga"] += g1
        if g1 > g2:
            a["w"] += 1; a["pts"] += 3; b["l"] += 1
        elif g2 > g1:
            b["w"] += 1; b["pts"] += 3; a["l"] += 1
        else:
            a["d"] += 1; a["pts"] += 1
            b["d"] += 1; b["pts"] += 1

    print(f"\n=== STANDINGS (through game day {games[-1]['day']}) ===\n")
    print(f"   {'Team':<16} {'W':>2} {'D':>2} {'L':>2} {'GF':>3} {'GA':>3} {'GD':>4} {'Pts':>4}")
    ranked = sorted(table.items(),
                    key=lambda kv: (-kv[1]["pts"], -(kv[1]["gf"] - kv[1]["ga"])))
    for i, (team, s) in enumerate(ranked, 1):
        gd = s["gf"] - s["ga"]
        print(f"{i:>2} {colored(team, f'{team:<16}')} {s['w']:>2} {s['d']:>2} {s['l']:>2}"
              f" {s['gf']:>3} {s['ga']:>3} {gd:>+4} {s['pts']:>4}")

    print("\n=== GOLDEN BOOT ===\n")
    rank, last = 0, None
    for i, (name, goals) in enumerate(
            sorted(boot.items(), key=lambda kv: (-kv[1], kv[0])), 1):
        if goals != last:
            rank, last = i, goals
        print(f"{rank:>2} {name:<16} {goals}")

    print("\n=== GOLDEN TEAM (unique scorers) ===\n")
    for team, names in sorted(scorers_by_team.items(), key=lambda kv: -len(kv[1])):
        print(f"{len(names):>2} {colored(team, f'{team:<16}')} {', '.join(sorted(names))}")

    print("\n=== RESULTS ===")
    day = None
    for g in games:
        if g["day"] != day:
            day = g["day"]
            print(f"\nGame Day {day} — {g['date']}")
        t1, t2 = g["teams"]
        g1, g2 = len(g["scorers"][t1]), len(g["scorers"][t2])
        scorers = ", ".join(g["scorers"][t1] + g["scorers"][t2]) or "no goals"
        print(f"  G{g['game']:<2} {colored(t1)} {g1} - {g2} {colored(t2)}  ({scorers})")
    print()


if __name__ == "__main__":
    main()
