---
name: spaced-repetition-teaching
description: >
  Adaptive spaced repetition engine using the FSRS-6 algorithm (Free Spaced
  Repetition Scheduler, Ye et al. 2024). Manages flashcard reviews with
  scientifically optimal intervals based on memory research. Triggers on: study
  sessions, flashcard reviews, "what's due today", "review cards", spaced
  repetition scheduling, and study session management. Developed through the
  Formation Fellowship technical interview prep program.
---

# Spaced Repetition Skill (FSRS-6)

Adaptive flashcard review system using the FSRS-6 algorithm — the state of the
art in spaced repetition scheduling, backed by 130+ years of memory research.

**Algorithm:** FSRS (Free Spaced Repetition Scheduler) by Ye et al., 2024.
Open-source reference: [open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs) (MIT).

**Origin:** Developed and refined through the [Formation](https://formation.dev)
Fellowship program for technical interview preparation — specifically DSA/algorithm
coding problems where learners need to both *understand* patterns conceptually and
*implement* them under time pressure. The author is not a representative of Formation.

---

## Learning Domain Adaptation

Different subjects demand different review emphasis. Detect the domain from the
card content and adapt the review cycle accordingly:

### Conceptual + Skill (default) — e.g., algorithm coding, system design
Cards require understanding *why* an approach works AND fluent implementation.
- **Recall** → **Interrogate** → **Rewrite** (timed coding) → **Retain**
- Emphasize the Interrogate and Rewrite phases — interviewers evaluate judgment
  and implementation speed, not just correctness.
- "Alternative phrasings" field matters — pattern recognition under varied wording
  is half the interview battle.

### Memorization-Heavy — e.g., medical school, language vocab, API references
Cards are primarily fact retrieval with less "why" reasoning.
- **Recall** → **Retain** (shorter cycle, higher volume)
- Interrogate phase is lighter (associations, mnemonics, context clues)
- Rewrite phase may not apply — replace with "produce from memory" (e.g., spell it,
  diagram it, list the steps)
- Optimize for card volume per session — more cards, faster pace.

### Conceptually Heavy — e.g., physics, mathematics, philosophy
Cards require deep reasoning and connecting ideas across domains.
- **Recall** → **Interrogate** (extended) → **Retain**
- Emphasize Interrogate: "Derive it from first principles," "How does this connect
  to [other concept]?", "What breaks if this assumption is wrong?"
- Rewrite phase becomes "re-derive" or "explain to a non-expert" (Feynman method)
- Fewer cards per session, more depth per card.

### Detection heuristic
Infer domain from card content:
- Has code/pseudocode/complexity analysis → **Conceptual + Skill**
- Has definitions, terminology, lists of facts → **Memorization-Heavy**
- Has proofs, derivations, "why" as the core prompt → **Conceptually Heavy**
- When uncertain, ask the user or default to **Conceptual + Skill**.

---

## Card File

Cards live in a user-specified markdown file. If not specified, ask once.

## Card Format

Each card is a markdown section (`### Title`) with metadata:

```markdown
### Binary Search on Answer Space
- **Priority:** P1
- **Prompt:** "Given items of various sizes and N recipients, find the largest
  portion so everyone gets at least one. Approach?"
- **Answer:** Binary search on the answer space [1, max(items)]. Feasibility
  predicate: sum(item // size for item in items) >= recipients. Return hi.
- **Interrogate:** When would two pointers beat this? What makes the predicate
  monotonic?
- **When to reach for it:** "Maximize/minimize a value subject to a feasibility
  check" — binary search on the answer.
- **FSRS:** d=5.50 s=8.20 reps=3 lapses=0 last=2026-03-11 next=2026-03-19
- **History:** [2026-03-04 Good, 2026-03-09 Again, 2026-03-11 Good]
```

**FSRS fields:**
- `d` = difficulty [1–10] (lower is easier)
- `s` = stability in days (≈ days until 90% recall probability)
- `reps` = total reviews
- `lapses` = times forgotten (rated Again)
- `last` / `next` = last review date / scheduled next review

**Rating scale:**
- 1 = Again — "Didn't know it" (blanked or completely wrong)
- 2 = Hard — "Struggled" (got there but with significant difficulty or errors)
- 3 = Good — "Got it" (recalled correctly with some effort)
- 4 = Easy — "Nailed it" (instant, effortless recall)

**Presentation rule:** When logging history or discussing ratings with the user,
use the human-readable label (Again/Hard/Good/Easy) — never the raw numeric
`G=N` notation. The numbers are internal to the FSRS engine.

---

## Review Methodology

Each review should cycle through multiple modes — not just recall:

1. **Recall** — Explain the approach without looking (mental rehearsal)
2. **Interrogate** — Why this approach? Tradeoffs? What changes if requirements change?
3. **Rewrite** — Code/apply it cold, timed. Notice hesitations.
4. **Retain** — Revisit 48+ hours later. Can't reproduce cleanly? → Rate Again (1).

❌ Skipping post-recall phases = 80% effort for 50% results.

**Priority guide:**
- P1: Fundamental, comes up everywhere. Review first.
- P2: Common pattern, transferable. Review second.
- P3: Good to know, niche. Skip if time-capped.

---

## Scripts

All scripts in `scripts/` — pure Python 3.6+, no external dependencies.

### Check what's due
```bash
python scripts/due_cards.py ~/my-cards.md
python scripts/due_cards.py ~/my-cards.md --all        # include upcoming
python scripts/due_cards.py ~/my-cards.md --date 2026-03-20  # plan ahead
```

### Submit a review
```bash
python scripts/review.py ~/my-cards.md "Binary Search" 3
# Ratings: 1="Didn't know it" 2="Struggled" 3="Got it" 4="Nailed it"
```

### Run algorithm self-test
```bash
python scripts/fsrs.py
```

---

## Handling User Requests

### "What's due today?" / "Show my queue"
Run `due_cards.py`. Present P1 cards prominently.

### "I reviewed [card] — rated [X]"
Run `review.py`. Show updated stability and next interval.
If they forgot (Again), normalize it — it's data, not failure.

### "Add a new card for [topic]"
Insert a new section in their card file. Do NOT add the FSRS line — it
gets created automatically on first review.

Template:
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

### "How is my retention?" / "Stats"
Parse card file and compute: strong cards (s>30d), struggling cards (lapses>0),
7-day review load forecast.

---

## Interpreting FSRS Numbers (Advanced)

Most users don't need this — the system handles scheduling automatically. For the curious:

- **Stability (s):** Days until ~90% recall. s=10 → review in ~10 days.
- **Difficulty (d):** 1=very easy, 10=very hard. Good cards converge to 3–6.
- **After "Didn't know it":** Stability drops sharply (e.g., 20d → 3d). Correct behavior.
- **After "Nailed it":** Stability grows fast. Use sparingly — only for instant recall.
- **Key insight:** At 90% retention target, interval ≈ stability.

## Algorithm Reference

See `references/fsrs-algorithm.md` for full FSRS math, formulas, and default
weights. Algorithm paper: Ye et al., "A Stochastic Shortest Path Algorithm for
Optimizing Spaced Repetition Scheduling" (2024).
