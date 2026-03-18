---
name: spaced-repetition-teaching
description: >
  Adaptive spaced repetition engine using the FSRS-6 algorithm (Free Spaced
  Repetition Scheduler, Ye et al. 2024). Manages flashcard reviews with
  scientifically optimal intervals based on memory research. Adapts review
  methodology to learning domain: conceptual+skill (algo coding, system design),
  memorization-heavy (med school, vocab), or conceptually-heavy (physics, math).
  Triggers on: study sessions, flashcard reviews, "what's due today", "review
  cards", spaced repetition scheduling, study session management, and SR queue
  management. Developed through the Formation Fellowship technical interview
  prep program.
---

# Spaced Repetition Skill (FSRS-6)

Adaptive flashcard review system using FSRS-6 — state of the art in spaced
repetition scheduling (Ye et al., 2024).

**Algorithm ref:** [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) (MIT).
**Origin:** Developed through [Formation](https://formation.dev) Fellowship for
technical interview prep. The author is not a representative of Formation.

---

## Learning Domain Adaptation

Detect domain from card content and adapt the review cycle:

| Domain | Review Cycle | Pace | Example Domains |
|--------|-------------|------|-----------------|
| **Conceptual + Skill** (default) | Recall → Interrogate → Rewrite (timed) → Retain | Moderate depth | Algo coding, system design, interview prep |
| **Memorization-Heavy** | Recall → Retain | High volume, fast | Med school, language vocab, API refs |
| **Conceptually Heavy** | Recall → Interrogate (extended) → Retain | Fewer cards, deep | Physics, math, philosophy |

### Review phases

- **Recall** — Explain the approach without looking.
- **Interrogate** — Why this approach? Tradeoffs? What if requirements change?
  For memorization domains, lighter: associations, mnemonics. For conceptual
  domains, extended: derive from first principles, Feynman-method explanation.
- **Rewrite** — Code/apply it cold, timed. For memorization: produce from memory.
  For conceptual: re-derive or explain to a non-expert.
- **Retain** — Revisit 48+ hours later. Can't reproduce cleanly? → Rate Again.

❌ Skipping post-recall phases = 80% effort for 50% results.

### Detection heuristic

- Code/pseudocode/complexity analysis → **Conceptual + Skill**
- Definitions, terminology, fact lists → **Memorization-Heavy**
- Proofs, derivations, "why" as core prompt → **Conceptually Heavy**
- When uncertain, ask or default to **Conceptual + Skill**.

---

## Card File

Cards live in a user-specified markdown file. Ask once if not specified.

### Card format

Each card is a `### Title` section with metadata fields:

```markdown
### Binary Search on Answer Space
- **Priority:** P1
- **Prompt:** "Given items of various sizes and N recipients, find the largest
  portion so everyone gets at least one. Approach?"
- **Answer:** Binary search on [1, max(items)]. Predicate:
  sum(item // size for item in items) >= recipients. Return hi.
- **Interrogate:** When would two pointers beat this? What makes the predicate
  monotonic?
- **When to reach for it:** "Maximize/minimize a value subject to a feasibility
  check" — binary search on the answer.
- **FSRS:** d=5.50 s=8.20 reps=3 lapses=0 last=2026-03-11 next=2026-03-19
- **History:** [2026-03-04 Good, 2026-03-09 Again, 2026-03-11 Good]
```

### FSRS fields

| Field | Meaning |
|-------|---------|
| `d` | Difficulty [1–10], lower = easier |
| `s` | Stability in days (≈ days until 90% recall) |
| `reps` | Total reviews |
| `lapses` | Times forgotten (rated Again) |
| `last`/`next` | Last review / next scheduled review |

### Rating scale

| Rating | Label | When to use |
|--------|-------|-------------|
| 1 | Again | Blanked or completely wrong |
| 2 | Hard | Got there with significant difficulty or errors |
| 3 | Good | Recalled correctly with some effort |
| 4 | Easy | Instant, effortless recall (use sparingly) |

Present ratings as **Again/Hard/Good/Easy** labels, never raw numbers.

### Priority guide

- **P1:** Fundamental, comes up everywhere. Review first.
- **P2:** Common pattern, transferable. Review second.
- **P3:** Good to know, niche. Skip if time-capped.

---

## Scripts

Pure Python 3.6+, no external dependencies. All in `scripts/`.

```bash
# Check what's due
python scripts/due_cards.py ~/cards.md
python scripts/due_cards.py ~/cards.md --all             # include upcoming
python scripts/due_cards.py ~/cards.md --date 2026-03-20  # plan ahead

# Submit a review
python scripts/review.py ~/cards.md "Binary Search" 3

# Self-test the FSRS algorithm
python scripts/fsrs.py
```

---

## Handling User Requests

### "What's due today?"
Run `due_cards.py`. Present P1 cards first.

### "I reviewed [card] — rated [X]"
Run `review.py`. Show updated stability and next interval.
If rated Again, normalize — it's data, not failure.

### "Add a new card for [topic]"
Insert a new `### Title` section. Do NOT add the FSRS line — created
automatically on first review.

```markdown
### [Title]
- **Priority:** [P1/P2/P3]
- **Prompt:** "[Question]"
- **Answer:** [Key insight + approach]
- **Interrogate:** [Tradeoffs? What if requirements change?]
- **When to reach for it:** [Pattern/signal that triggers this approach]
- **Added:** [date]
- **History:** []
```

### "How is my retention?"
Parse card file. Compute: strong cards (s>30d), struggling (lapses>0),
7-day review load forecast.

---

## Algorithm Reference

See `references/fsrs-algorithm.md` for full FSRS math, formulas, and default
weights. Paper: Ye et al., "A Stochastic Shortest Path Algorithm for Optimizing
Spaced Repetition Scheduling" (2024).

Quick reference:
- **Stability (s):** interval ≈ stability at 90% retention target.
- **Difficulty (d):** Good cards converge to 3–6.
- **After Again:** Stability drops sharply (e.g., 20d → 3d). Expected.
- **After Easy:** Stability grows fast. Use sparingly.
