# Mixed-Interval Stacking for adaptive_composer.py

## Context

The composer currently builds scales from pure interval stacking (fifths → circle of fifths, major thirds → augmented/diminished symmetry, whole tones). Pure stacking has three clean options and then goes stale. The interesting territory is **mixing intervals** — alternating or sequencing different ratios so the scale doesn't close symmetrically and doesn't collapse into a known mode.

This brief covers the mixed approaches worth implementing, in rough order of payoff.

---

## 1. Fifth Up / Fourth Down (the spiral)

**Rule:** ascend a perfect fifth (7 semitones), descend a perfect fourth (5 semitones), repeat.

```
start = 0
pattern = [+7, -5]  # fifth up, fourth down
```

- Net motion per cycle: +2 semitones. The scale never closes — it drifts upward forever, a **spiral**, not a circle.
- After 6 cycles you land on the tritone (6 semitones) relative to the start. After 12, you've covered all 12 pitches but the *order* of arrival is completely different from the circle of fifths.
- **Why it matters for the composer:** the existing circle-of-fifths motion in `adaptive_composer.py` is periodic. This gives you a non-periodic, drifting harmonic center — useful for sections that should feel like they're slowly escaping a key without ever landing on a resolution.
- **Implementation note:** because it never repeats, you need a transposition budget or a "wrap at octave" option. Without wrapping, MIDI note numbers climb indefinitely. With wrapping (mod 12), you get a 12-note scale whose *sequence* is the spiral order: 0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5.

## 2. Major Third Up / Tritone Down (Messiaen Mode 3)

**Rule:** ascend a major third (4 semitones), descend a tritone (6 semitones), repeat.

```
pattern = [+4, -6]
```

- Net motion per cycle: -2 semitones (drifts down).
- This is **Messiaen's third mode of limited transposition**. It has exactly 8 distinct transpositions before it repeats — fewer than any other mode. That's the "suspended outside any key" quality.
- Pitch classes generated (from C): C, E, B-flat, D-sharp, G-sharp, C-sharp, F-sharp, A, then back to C. Eight notes.
- **For the composer:** pair this with the existing mode system. When the user selects "mode 3" or a "Messiaen" flag, generate from this pattern instead of the diatonic modes. The 8-note limit means chord vocabulary is small but extremely colorful — lots of major sevenths, minor ninths, tritones.

## 3. Major Third Up / Minor Third Down (octatonic)

**Rule:** ascend a major third, descend a minor third, repeat.

```
pattern = [+4, -3]
```

- Net: +1 semitone per cycle. Drifts up by a semitone each pair.
- This is the **octatonic scale** (8 notes, alternating whole/half). It's the scale Stravinsky's *Rite of Spring* is built on.
- Distinct from pure minor-third stacking (diminished seventh, 4 notes) because the alternation breaks the symmetry — you get 8 notes, not 4.
- **Composer use:** great for "unsettled" or "ritual" sections. The existing drum pattern templates (afro, latin) pair naturally with octatonic harmony because both have that off-balance, non-Western pulse feel.

## 4. Minor Third Up / Major Third Down

**Rule:** ascend a minor third, descend a major third.

```
pattern = [+3, -4]
```

- Net: -1 semitone. Mirror image of #3 — drifts down instead of up.
- Generates the same 8 pitch classes as #3 but in reverse order with a different arrival sequence. The *feel* differs: #3 leans bright-then-dark, this one leans dark-then-bright.
- Cheap to implement once #3 exists — just negate the pattern or swap the two intervals.

## 5. Fifth Up / Tritone Down

**Rule:** ascend a fifth, descend a tritone.

```
pattern = [+7, -6]
```

- Net: +1 semitone per cycle.
- From C: C, G, D-sharp, A-sharp, F, C, ... — closes after 5 cycles into a 5-note set. Small vocabulary, very tense (every interval against the root is unstable except the fifth).
- **Use:** short tension-building passages, not full sections. Think of it as a "dominant prolongation" device.

## 6. Fourth Up / Tritone Down

**Rule:** ascend a fourth, descend a tritone.

```
pattern = [+5, -6]
```

- Net: -1. Mirror of #5.
- From C: C, F, B-flat, E, A, D, G, C... — 7-note set that actually contains a diatonic flavor (it overlaps Lydian). Interesting hybrid: sounds partly familiar, partly wrong.

---

## Implementation Sketch (Python, fits existing adaptive_composer.py style)

```python
MIXED_PATTERNS = {
    "spiral_fifth_fourth": [7, -5],   # fifth up, fourth down
    "messiaen_mode3":      [4, -6],   # major 3rd up, tritone down
    "octatonic":           [4, -3],   # major 3rd up, minor 3rd down
    "octatonic_mirror":    [3, -4],   # minor 3rd up, major 3rd down
    "tension_fifth":       [7, -6],   # fifth up, tritone down
    "lydian_hybrid":       [5, -6],   # fourth up, tritone down
}

def build_mixed_scale(root_pc, pattern, wrap=True, max_notes=24):
    """Build a scale by applying interval pattern cyclically.
    root_pc: 0-11 pitch class
    pattern: list of semitone deltas applied in cycle
    wrap: if True, mod 12 (scale closes); if False, raw MIDI drift
    max_notes: safety cap for non-wrapping mode
    """
    notes, pc = [], root_pc
    i = 0
    while len(notes) < max_notes:
        notes.append(pc if wrap else root_pc + sum(pattern[:i % len(pattern)]) % 12 + 12 * (sum(pattern[:i]) // 12))
        # simpler: always track absolute semitone offset from root
        pc = (pc + pattern[i % len(pattern)]) % 12
        notes.append(pc)
        i += 1
        if wrap and pc == root_pc and i > 0:
            break  # closed
    return notes
```

*(The sketch above is intentionally rough — clean it to match the existing function signatures in adaptive_composer.py. The key design decision is the `wrap` flag: True gives you a closed scale for chord/mode use; False gives you the drifting spiral for generative, non-repeating lines.)*

---

## What to Avoid

- **Don't** mix more than two intervals per pattern initially. Three-interval mixes (e.g., 5th, 4th, 3rd) produce dense, near-chromatic sets fast and lose the distinctive color each pair creates.
- **Don't** default `wrap=False` — non-wrapping mode only makes sense for specific generative sections, and MIDI range will blow past 127 quickly on long runs.
- Pure stacking (all fifths, all major 3rds, all minor 3rds, all whole tones) is already covered by the existing mode system. This brief is only about the *mixed* cases.

---

## Quick Reference: Net Drift Per Cycle

| Pattern | Intervals | Net/cycle | Notes before close (wrapped) |
|---|---|---|---|
| spiral_fifth_fourth | +7, -5 | +2 | 12 (all pitches, spiral order) |
| messiaen_mode3 | +4, -6 | -2 | 8 |
| octatonic | +4, -3 | +1 | 8 |
| octatonic_mirror | +3, -4 | -1 | 8 |
| tension_fifth | +7, -6 | +1 | 5 |
| lydian_hybrid | +5, -6 | -1 | 7 |

All six are **limited transposition** in the wrapped case — they repeat under some transposition, which is exactly the Messiaen property that makes them sound "non-tonal but organized."
