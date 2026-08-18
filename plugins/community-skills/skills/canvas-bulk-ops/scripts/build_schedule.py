#!/usr/bin/env python3
"""
Build a term's class-session schedule and the exact UTC timestamps Canvas needs.

Why this exists: the single most common way bulk Canvas date edits go wrong is the
daylight-saving boundary. A fall term that starts in CDT and ends in CST will have
its last several weeks silently shifted by an hour if you compute one UTC offset and
reuse it. This script resolves the offset per date from the IANA database, so each
session gets the offset actually in effect on that day.

Usage
-----
  python build_schedule.py --start 2026-08-25 --end 2026-12-03 \
      --days Tue,Thu --open 10:35 --close 10:55 --tz America/Chicago

  # skip holidays / no-class dates
  python build_schedule.py ... --skip 2026-11-26,2026-11-27

  # emit JSON instead of a table
  python build_schedule.py ... --json

Output columns
--------------
  session      1-based session number (what "Class N" usually means)
  local_date   YYYY-MM-DD in the course's timezone
  weekday      three-letter day, so a wrong --days flag is obvious at a glance
  open_utc     ISO8601 Z timestamp for unlock_at
  close_utc    ISO8601 Z timestamp for due_at (and lock_at, if you lock at due)
  offset       the UTC offset actually in effect that day (sanity check)
"""

import argparse
import json
import sys
from datetime import date, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    sys.exit("This script needs Python 3.9+ for zoneinfo.")

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
UTC = ZoneInfo("UTC")


def parse_days(spec):
    """'Tue,Thu' or 'TR' or 'MW' -> {1, 3} (Monday=0, matching date.weekday())."""
    compact = {"M": 0, "T": 1, "W": 2, "R": 3, "F": 4, "S": 5, "U": 6}
    spec = spec.strip()
    if "," in spec or spec[:3].title() in DAY_NAMES:
        out = set()
        for part in spec.split(","):
            key = part.strip()[:3].title()
            if key not in DAY_NAMES:
                raise ValueError(f"Unrecognized day {part!r}")
            out.add(DAY_NAMES.index(key))
        return out
    # compact form like "TR" or "MWF"
    out = set()
    for ch in spec.upper():
        if ch not in compact:
            raise ValueError(f"Unrecognized day letter {ch!r}")
        out.add(compact[ch])
    return out


def parse_hhmm(s):
    h, m = s.strip().split(":")
    return int(h), int(m)


def build(start, end, days, open_hhmm, close_hhmm, tzname, skip=()):
    tz = ZoneInfo(tzname)
    oh, om = parse_hhmm(open_hhmm)
    ch, cm = parse_hhmm(close_hhmm)
    skip_set = set(skip)

    rows = []
    cur, n = start, 0
    while cur <= end:
        if cur.weekday() in days and cur.isoformat() not in skip_set:
            n += 1
            o = datetime(cur.year, cur.month, cur.day, oh, om, tzinfo=tz)
            c = datetime(cur.year, cur.month, cur.day, ch, cm, tzinfo=tz)
            if c <= o:
                raise ValueError(
                    f"Close time {close_hhmm} is not after open time {open_hhmm} "
                    f"on {cur.isoformat()}. If you meant an overnight window, "
                    f"set it explicitly in Canvas instead."
                )
            rows.append({
                "session": n,
                "local_date": cur.isoformat(),
                "weekday": DAY_NAMES[cur.weekday()],
                "open_local": o.strftime("%I:%M %p").lstrip("0"),
                "close_local": c.strftime("%I:%M %p").lstrip("0"),
                "open_utc": o.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "close_utc": c.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "offset": o.strftime("%z"),
            })
        cur += timedelta(days=1)
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--start", required=True, help="First possible class day, YYYY-MM-DD")
    p.add_argument("--end", required=True, help="Last possible class day, YYYY-MM-DD")
    p.add_argument("--days", required=True, help="'Tue,Thu' or compact 'TR' (R=Thursday, U=Sunday)")
    p.add_argument("--open", required=True, dest="open_", help="Local open time, HH:MM 24h")
    p.add_argument("--close", required=True, help="Local close/due time, HH:MM 24h")
    p.add_argument("--tz", default="America/Chicago", help="IANA timezone of the course")
    p.add_argument("--skip", default="", help="Comma-separated YYYY-MM-DD dates with no class")
    p.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
    a = p.parse_args()

    rows = build(
        date.fromisoformat(a.start), date.fromisoformat(a.end),
        parse_days(a.days), a.open_, a.close, a.tz,
        [s.strip() for s in a.skip.split(",") if s.strip()],
    )

    if a.json:
        print(json.dumps(rows, indent=1))
        return

    print(f"{len(rows)} sessions | {a.tz} | open {a.open_} close {a.close}")
    offsets = sorted({r["offset"] for r in rows})
    if len(offsets) > 1:
        print(f"NOTE: term crosses a DST change; offsets in play: {', '.join(offsets)}")
    print()
    print(f"{'#':>3}  {'date':<12} {'day':<4} {'open (UTC)':<22} {'close (UTC)':<22} offset")
    for r in rows:
        print(f"{r['session']:>3}  {r['local_date']:<12} {r['weekday']:<4} "
              f"{r['open_utc']:<22} {r['close_utc']:<22} {r['offset']}")


if __name__ == "__main__":
    main()
