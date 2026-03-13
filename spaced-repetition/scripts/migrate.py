#!/usr/bin/env python3
"""
migrate.py — Convert existing fixed-interval SR cards to FSRS state.

Usage:
    python migrate.py <card_file> [--dry-run]

    --dry-run   Print what would be changed without modifying the file.

Strategy:
    For each card WITHOUT an FSRS line, infer initial FSRS state from the
    existing Interval/History fields:

    - Parse "Interval: Day N" to estimate how many successful reviews have occurred.
    - Estimate stability from the current interval (interval ≈ stability at 90% retention).
    - Estimate difficulty from the card's review history (lapses → higher difficulty).
    - Set next_review from the existing "Next review:" field.
    - Set last_review from the last History entry date, or from "Next review" - interval.

    Cards WITH an FSRS line are skipped (already migrated).

After migration:
    - Run `python due_cards.py <card_file>` to see your queue.
    - The first real review of each migrated card will recalibrate the state.
"""

import os
import re
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))
from fsrs import FSRSState, DEFAULT_W, initial_difficulty
from review import parse_cards, format_fsrs_line, _detect_indent


_CARD_FIELDS = re.compile(
    r'\*\*(Prompt|Answer|Priority|FSRS|History|Added|Interrogate|When to reach):\*\*',
    re.IGNORECASE
)


def _is_flashcard(card: dict) -> bool:
    """Return True if the section looks like an actual flashcard (not a header section)."""
    text = "".join(card["raw_lines"])
    return bool(_CARD_FIELDS.search(text))


# Map from "Day N" interval strings to approximate stability (days)
# We treat stability ≈ interval at 90% retention
INTERVAL_MAP = {
    1: 1.0,
    3: 3.0,
    7: 7.0,
    14: 14.0,
    30: 30.0,
    60: 60.0,
    90: 90.0,
}


def parse_existing_interval(card_lines: list[str]) -> int | None:
    """Extract interval in days from `- **Interval:** Day N` or `Day N`."""
    for line in card_lines:
        m = re.search(r'\bDay\s+(\d+)\b', line, re.IGNORECASE)
        if m:
            return int(m.group(1))
        m = re.search(r'\bInterval:\*\*\s*(\d+)', line)
        if m:
            return int(m.group(1))
    return None


def parse_existing_next_review(card_lines: list[str]) -> date | None:
    """Extract next review date from `- **Next review:** YYYY-MM-DD`."""
    for line in card_lines:
        m = re.search(r'\bNext review[:\*]+\s*(\d{4}-\d{2}-\d{2})', line)
        if m:
            try:
                return date.fromisoformat(m.group(1))
            except ValueError:
                pass
    return None


def parse_history_dates(card_lines: list[str]) -> list[date]:
    """Extract all ISO dates from the History line."""
    dates = []
    for line in card_lines:
        if "History" in line:
            found = re.findall(r'(\d{4}-\d{2}-\d{2})', line)
            for d in found:
                try:
                    dates.append(date.fromisoformat(d))
                except ValueError:
                    pass
    return sorted(dates)


def count_lapses_in_history(card_lines: list[str]) -> int:
    """Count ❌ or 'reset' or 'Again' markers in history."""
    for line in card_lines:
        if "History" in line:
            lapses = line.count("❌") + len(re.findall(r'\bAgain\b', line))
            return lapses
    return 0


def infer_fsrs_state(card: dict) -> FSRSState:
    """
    Build a best-guess FSRSState from a card's existing fixed-interval fields.
    """
    raw = card["raw_lines"]
    state = FSRSState()

    # --- Stability: approximate from current interval ---
    interval_days = parse_existing_interval(raw)
    state.stability = float(interval_days) if interval_days else 1.0
    state.stability = max(0.5, state.stability)

    # --- Next review date ---
    next_review = parse_existing_next_review(raw)
    state.next_review = next_review

    # --- Last review date ---
    history_dates = parse_history_dates(raw)
    if history_dates:
        state.last_review = history_dates[-1]
        state.reps = len(history_dates)
    elif next_review and interval_days:
        state.last_review = next_review - timedelta(days=interval_days)
        state.reps = 1

    # --- Lapses ---
    state.lapses = count_lapses_in_history(raw)

    # --- Difficulty: infer from lapses and priority ---
    # Cards with lapses are harder. P1 cards are assumed to be practiced more.
    priority = card["priority"]
    base_d = {"P1": 4.5, "P2": 5.5, "P3": 6.5}.get(priority, 5.5)
    lapse_penalty = min(state.lapses * 0.5, 2.0)
    state.difficulty = min(10.0, base_d + lapse_penalty)

    # If we have multi-review history at Day 7+, card is manageable → lower difficulty
    if state.reps >= 2 and state.stability >= 7.0:
        state.difficulty = max(1.0, state.difficulty - 0.5)

    return state


def migrate_card(card: dict, all_lines: list[str], line_offset: int = 0) -> bool:
    """
    Insert a FSRS line into a card that doesn't have one.
    Returns True if the card was modified.

    line_offset: number of lines already inserted before this card (to adjust indices).
    """
    if card["fsrs_line_idx"] is not None:
        return False  # Already has FSRS state

    state = infer_fsrs_state(card)
    fsrs_indent = _detect_indent(card["raw_lines"])
    fsrs_line = fsrs_indent + format_fsrs_line(state) + "\n"

    # Find insertion point: before History line, or after last known metadata line
    raw = card["raw_lines"]
    offset = card["start_line"] + line_offset  # adjust for prior insertions
    insert_idx = None

    for j, line in enumerate(raw):
        if re.match(r'\s*-\s+\*\*History:\*\*', line):
            insert_idx = offset + j
            break

    if insert_idx is None:
        # Insert before the first blank line or at end of card
        for j, line in enumerate(raw[1:], 1):
            if line.strip() == "":
                insert_idx = offset + j
                break
        if insert_idx is None:
            insert_idx = offset + len(raw)

    all_lines.insert(insert_idx, fsrs_line)
    return True


def main():
    args = sys.argv[1:]
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    if not args:
        print(__doc__)
        sys.exit(1)

    card_file = os.path.expanduser(args[0])
    if not os.path.exists(card_file):
        print(f"File not found: {card_file}", file=sys.stderr)
        sys.exit(1)

    with open(card_file, "r") as f:
        text = f.read()

    cards, all_lines = parse_cards(text)

    migrated = 0
    skipped = 0
    lines_inserted = 0  # track insertions to adjust offsets for subsequent cards

    print(f"Scanning {os.path.basename(card_file)}...")
    print()

    for card in cards:
        if not _is_flashcard(card):
            continue  # skip section headers and non-card sections

        if card["fsrs_line_idx"] is not None:
            print(f"  [SKIP]    {card['title']}  (already has FSRS state)")
            skipped += 1
            continue

        state = infer_fsrs_state(card)
        print(f"  [MIGRATE] {card['title']}")
        print(f"            → d={state.difficulty:.2f} s={state.stability:.1f}d "
              f"reps={state.reps} lapses={state.lapses} "
              f"next={state.next_review or 'unknown'}")

        if not dry_run:
            migrate_card(card, all_lines, line_offset=lines_inserted)
            lines_inserted += 1
        migrated += 1

    print()
    print(f"Results: {migrated} migrated, {skipped} skipped")

    if dry_run:
        print("\n[DRY RUN] No files modified. Remove --dry-run to apply.")
        return

    if migrated > 0:
        with open(card_file, "w") as f:
            f.write("".join(all_lines))
        print(f"\nUpdated: {card_file}")
        print("Run `python due_cards.py` to see your queue with FSRS scheduling.")
    else:
        print("Nothing to migrate.")


if __name__ == "__main__":
    main()
