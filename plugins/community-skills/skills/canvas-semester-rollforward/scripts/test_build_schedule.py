#!/usr/bin/env python3
"""
Tests for build_schedule.py.

Run:  python test_build_schedule.py

The regression test at the bottom is the important one: it reproduces a real
Fall 2026 T/Th term whose correct timestamps were confirmed against live Canvas
data. If a future edit breaks DST handling, that test fails loudly.
"""

import unittest
from datetime import date

from build_schedule import build, parse_days, parse_hhmm


class TestParsing(unittest.TestCase):
    def test_named_days(self):
        self.assertEqual(parse_days("Tue,Thu"), {1, 3})
        self.assertEqual(parse_days("Mon, Wed, Fri"), {0, 2, 4})

    def test_compact_days(self):
        self.assertEqual(parse_days("TR"), {1, 3})
        self.assertEqual(parse_days("MWF"), {0, 2, 4})
        self.assertEqual(parse_days("U"), {6})

    def test_compact_and_named_agree(self):
        self.assertEqual(parse_days("TR"), parse_days("Tue,Thu"))

    def test_bad_day_raises(self):
        with self.assertRaises(ValueError):
            parse_days("Funday")
        with self.assertRaises(ValueError):
            parse_days("XYZ")

    def test_hhmm(self):
        self.assertEqual(parse_hhmm("09:25"), (9, 25))
        self.assertEqual(parse_hhmm("23:59"), (23, 59))


class TestSchedule(unittest.TestCase):
    def test_only_requested_weekdays(self):
        rows = build(date(2026, 8, 25), date(2026, 9, 30), {1, 3},
                     "10:35", "10:55", "America/Chicago")
        self.assertTrue(all(r["weekday"] in ("Tue", "Thu") for r in rows))

    def test_sessions_number_from_one_and_are_contiguous(self):
        rows = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                     "10:35", "10:55", "America/Chicago")
        self.assertEqual([r["session"] for r in rows], list(range(1, len(rows) + 1)))

    def test_skip_dates_removed_and_renumbered(self):
        full = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                     "10:35", "10:55", "America/Chicago")
        trimmed = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                        "10:35", "10:55", "America/Chicago",
                        skip=["2026-11-26"])  # a Thursday in range
        self.assertEqual(len(trimmed), len(full) - 1)
        self.assertNotIn("2026-11-26", [r["local_date"] for r in trimmed])
        # renumbering stays contiguous after a removal
        self.assertEqual([r["session"] for r in trimmed],
                         list(range(1, len(trimmed) + 1)))

    def test_close_before_open_raises(self):
        with self.assertRaises(ValueError):
            build(date(2026, 8, 25), date(2026, 8, 27), {1, 3},
                  "10:55", "10:35", "America/Chicago")

    def test_inclusive_endpoints(self):
        rows = build(date(2026, 8, 25), date(2026, 8, 25), {1},
                     "09:00", "09:30", "America/Chicago")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["local_date"], "2026-08-25")


class TestDaylightSaving(unittest.TestCase):
    """DST is the whole reason this script exists."""

    def test_fall_term_crosses_dst(self):
        rows = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                     "10:35", "10:55", "America/Chicago")
        offsets = {r["offset"] for r in rows}
        self.assertEqual(offsets, {"-0500", "-0600"},
                         "A Aug-Dec US term must span both CDT and CST")

    def test_same_local_time_yields_different_utc_across_dst(self):
        rows = build(date(2026, 10, 29), date(2026, 11, 3), {1, 3},
                     "10:35", "10:55", "America/Chicago")
        before = next(r for r in rows if r["local_date"] == "2026-10-29")
        after = next(r for r in rows if r["local_date"] == "2026-11-03")
        self.assertEqual(before["open_utc"], "2026-10-29T15:35:00Z")
        self.assertEqual(after["open_utc"], "2026-11-03T16:35:00Z")

    def test_spring_term_crosses_dst_the_other_way(self):
        rows = build(date(2027, 1, 19), date(2027, 5, 6), {1, 3},
                     "14:00", "15:15", "America/Chicago")
        offsets = {r["offset"] for r in rows}
        self.assertEqual(offsets, {"-0600", "-0500"},
                         "A Jan-May US term must span both CST and CDT")

    def test_non_dst_timezone_is_stable(self):
        rows = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                     "10:35", "10:55", "America/Phoenix")
        self.assertEqual({r["offset"] for r in rows}, {"-0700"},
                         "Arizona does not observe DST")


class TestCrossSemesterMove(unittest.TestCase):
    """
    Moving a series from a fall shell into a spring section is the most error-prone
    roll-forward, because three things change at once and none of them are visible in
    the copied course:

      1. Different holidays. Fall has Thanksgiving; spring has a whole break week plus
         assorted campus holidays. Neither calendar transfers.
      2. DST moves the opposite direction, and in spring the transition frequently falls
         *inside* the break week, so the offset changes across a gap in the schedule.
      3. The session count differs, so a fall series will rarely have exactly the right
         number of items for a spring term.

    The script cannot know a holiday calendar and does not try. It requires the skip
    dates to be supplied. These tests pin the behavior that matters: given correct skips,
    the offsets and numbering come out right.
    """

    SPRING_BREAK = ["2027-03-15", "2027-03-17", "2027-03-19"]

    def test_spring_break_week_removed(self):
        rows = build(date(2027, 1, 20), date(2027, 5, 7), {0, 2, 4},
                     "08:00", "08:50", "America/Chicago", skip=self.SPRING_BREAK)
        dates = [r["local_date"] for r in rows]
        for d in self.SPRING_BREAK:
            self.assertNotIn(d, dates)

    def test_dst_transition_inside_the_break_week(self):
        """DST starts Sun Mar 14 2027 — inside spring break. The offset must change
        across the gap, with no session straddling the transition."""
        rows = build(date(2027, 1, 20), date(2027, 5, 7), {0, 2, 4},
                     "08:00", "08:50", "America/Chicago", skip=self.SPRING_BREAK)
        before = [r for r in rows if r["local_date"] < "2027-03-14"]
        after = [r for r in rows if r["local_date"] > "2027-03-14"]
        self.assertEqual({r["offset"] for r in before}, {"-0600"}, "pre-transition is CST")
        self.assertEqual({r["offset"] for r in after}, {"-0500"}, "post-transition is CDT")
        self.assertEqual(before[-1]["local_date"], "2027-03-12")
        self.assertEqual(after[0]["local_date"], "2027-03-22")

    def test_same_local_time_different_utc_across_spring_transition(self):
        rows = build(date(2027, 1, 20), date(2027, 5, 7), {0, 2, 4},
                     "08:00", "08:50", "America/Chicago", skip=self.SPRING_BREAK)
        before = next(r for r in rows if r["local_date"] == "2027-03-12")
        after = next(r for r in rows if r["local_date"] == "2027-03-22")
        self.assertEqual(before["open_utc"], "2027-03-12T14:00:00Z")
        self.assertEqual(after["open_utc"], "2027-03-22T13:00:00Z")

    def test_fall_and_spring_session_counts_differ(self):
        """A fall series will not simply drop into spring — the counts don't match, which
        is the signal to reconcile items against sessions rather than assume 1:1."""
        fall = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                     "10:35", "10:55", "America/Chicago",
                     skip=["2026-11-24", "2026-11-26"])
        spring = build(date(2027, 1, 20), date(2027, 5, 7), {0, 2, 4},
                       "08:00", "08:50", "America/Chicago", skip=self.SPRING_BREAK)
        self.assertNotEqual(len(fall), len(spring))

    def test_additional_campus_holiday_shifts_numbering(self):
        base = build(date(2027, 1, 20), date(2027, 5, 7), {0, 2, 4},
                     "08:00", "08:50", "America/Chicago", skip=self.SPRING_BREAK)
        with_holiday = build(date(2027, 1, 20), date(2027, 5, 7), {0, 2, 4},
                             "08:00", "08:50", "America/Chicago",
                             skip=self.SPRING_BREAK + ["2027-03-29"])
        self.assertEqual(len(with_holiday), len(base) - 1)
        after = next(r for r in with_holiday if r["local_date"] == "2027-03-31")
        before = next(r for r in base if r["local_date"] == "2027-03-31")
        self.assertEqual(after["session"], before["session"] - 1)


class TestRealTermRegression(unittest.TestCase):
    """
    Reproduces MAN 327 Fall 2026 (T/Th, Aug 25 - Dec 3). These expected values were
    confirmed against timestamps Canvas itself had already stored for the first
    session, then extended across the term. Treat them as ground truth.

    Note the Thanksgiving skip. A raw T/Th sweep of this range yields 30 sessions,
    but the real term has 28 because Nov 24 and Nov 26 are break days. This is the
    normal case, not an edge case: almost every term has holidays, and forgetting
    them shifts every session number after the break.
    """

    THANKSGIVING = ["2026-11-24", "2026-11-26"]

    def setUp(self):
        self.rows = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                          "10:35", "10:55", "America/Chicago",
                          skip=self.THANKSGIVING)

    def test_holidays_actually_shift_numbering(self):
        """Without the skip, Dec 1 would be session 29 rather than 27."""
        no_skip = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                        "10:35", "10:55", "America/Chicago")
        self.assertEqual(len(no_skip), 30)
        self.assertEqual(
            next(r["session"] for r in no_skip if r["local_date"] == "2026-12-01"), 29)
        self.assertEqual(
            next(r["session"] for r in self.rows if r["local_date"] == "2026-12-01"), 27)

    def test_session_count(self):
        self.assertEqual(len(self.rows), 28)

    def test_first_session_matches_canvas(self):
        r = self.rows[0]
        self.assertEqual(r["local_date"], "2026-08-25")
        self.assertEqual(r["weekday"], "Tue")
        self.assertEqual(r["open_utc"], "2026-08-25T15:35:00Z")
        self.assertEqual(r["close_utc"], "2026-08-25T15:55:00Z")

    def test_last_session_matches_canvas(self):
        r = self.rows[-1]
        self.assertEqual(r["session"], 28)
        self.assertEqual(r["local_date"], "2026-12-03")
        self.assertEqual(r["open_utc"], "2026-12-03T16:35:00Z")

    def test_dst_split_is_20_then_8(self):
        cdt = [r for r in self.rows if r["offset"] == "-0500"]
        cst = [r for r in self.rows if r["offset"] == "-0600"]
        self.assertEqual((len(cdt), len(cst)), (20, 8))

    def test_session_21_is_the_first_cst_session(self):
        self.assertEqual(self.rows[20]["local_date"], "2026-11-03")
        self.assertEqual(self.rows[20]["offset"], "-0600")
        self.assertEqual(self.rows[19]["offset"], "-0500")

    def test_attendance_window_variant(self):
        """Same term, different window (9:25-10:45) used by the attendance series."""
        rows = build(date(2026, 8, 25), date(2026, 12, 3), {1, 3},
                     "09:25", "10:45", "America/Chicago",
                     skip=self.THANKSGIVING)
        self.assertEqual(rows[0]["open_utc"], "2026-08-25T14:25:00Z")
        self.assertEqual(rows[0]["close_utc"], "2026-08-25T15:45:00Z")
        self.assertEqual(rows[20]["open_utc"], "2026-11-03T15:25:00Z")
        self.assertEqual(rows[20]["close_utc"], "2026-11-03T16:45:00Z")


if __name__ == "__main__":
    unittest.main(verbosity=2)
