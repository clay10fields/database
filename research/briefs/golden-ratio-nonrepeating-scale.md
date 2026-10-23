# Golden-Ratio Non-Repeating Scale for adaptive_composer.py

## Context

All twelve-tone equal-temperament interval patterns eventually close or cycle — that's the Messiaen limited-transposition property, and it's also the ceiling. The one ratio that never closes is the **golden ratio**, phi ≈ 1.618. Stepping by phi in semitone-space produces an infinite sequence that never repeats a pitch class and never returns to the start. It's the only "scale" that is genuinely non-periodic in 12-TET.

This is hard to notate by hand and nearly impossible to play from a fixed score, which is exactly why it's a composer problem, not a performer problem. `adaptive_composer.py` already handles irregular interval logic (mode templates, grid/density fallback, session JSON memory), so this slots in as a new generation mode rather than a refactor.

---

## Core Rule

Treat phi as a step size in semitones. From a root, each successive note is the previous note plus phi, quantized to the nearest equal-tempered pitch, folded back into a playable octave range.

```
phi = 1.6180339887
root = 60  # MIDI C4, or any starting note
notes = []
current = root
for i in range(N):
    notes.append(round(current))
    current += phi
    # fold into [root, root+12) so it stays in one octave
    while current >= root + 12:
        current -= 12
    while current < root:
        current += 12
```

- **Why round, not floor:** flooring biases the scale flat and creates a systematic downward drift that fights the phi motion. Rounding keeps the quantization error symmetric around zero, which preserves the "almost but never quite" quality.
- **Why fold instead of mod 12 on the raw accumulator:** modding the accumulator directly (current = (current + phi) % 12) destroys the irrationality — you'd get a 12-cycle. Folding the *displayed* note while letting the accumulator run free is what keeps the sequence non-repeating. The accumulator is the truth; the folded note is the performance.

---

## Duration Mapping

The ear needs something to hold onto when pitch repetition is gone. Map duration to interval width:

- Wide golden steps (phi rounds to 2 semitones) → shorter notes, faster surface rhythm.
- Narrow steps (phi rounds to 1 semitone) → longer notes, more sustain.

Concretely: `duration = base_duration * (1.0 - min(abs(step_in_semitones), 2) / 4.0)` clamped to a sane floor. The music breathes faster exactly when it stretches, which matches the psychoacoustic effect — tension rises with interval size, so the rhythm should too.

Alternative worth testing: inverse mapping (wide = long). That gives a slow, suspended, Ligeti-like drift. Try both; they feel like different pieces.

---

## Why It Works Musically

In any repeating scale, the ear builds a model — "this is octatonic, I know where this goes." With phi, the model never completes. Each note is statistically *almost* a note you've heard, but the almost is the point. It's the musical equivalent of a fractal coastline: familiar at every zoom level, never the same twice.

The closest human precedent is Ligeti's micropolyphony and late Feldman — music that moves by accumulation rather than progression. But those were composed by hand with enormous labor. A generative system can sustain this indefinitely, which no human ensemble can.

---

## Implementation Sketch

```python
import math

PHI = (1 + math.sqrt(5)) / 2  # 1.6180339887

def build_phi_scale(root_midi=60, n_notes=32, base_duration=0.5):
    """Golden-ratio non-repeating line. Accumulator runs free;
    displayed notes fold into one octave above root."""
    notes = []
    current = float(root_midi)
    for i in range(n_notes):
        q = round(current)
        # fold into [root, root+12)
        while q >= root_midi + 12:
            q -= 12
        while q < root_midi:
            q += 12
        step = abs(q - (notes[-1] if notes else root_midi))
        dur = base_duration * (1.0 - min(step, 2) / 4.0)
        dur = max(dur, base_duration * 0.25)  # sane floor
        notes.append({"midi": q, "duration": dur, "step_semitones": step})
        current += PHI
    return notes

def phi_to_midi_stream(notes, channel=0, velocity=80):
    """Convert phi-scale dicts to mido messages for the IAC bus."""
    import mido
    msgs = []
    t = 0
    for n in notes:
        msgs.append(mido.Message('note_on', note=n['midi'],
                                 velocity=velocity, channel=channel, time=t))
        msgs.append(mido.Message('note_off', note=n['midi'],
                                 velocity=0, channel=channel, time=n['duration']))
        t = 0  # mido relative timing: only first msg carries delay
    return msgs
```

---

## Session Memory

Add a `phi_mode` flag to the session JSON alongside mode name and mixed-pattern name. Store: root MIDI, note count, duration base, and which duration mapping (wide=short vs wide=long) was active. On reload, regenerate the line from the accumulator seed rather than storing raw MIDI — that keeps the non-repeating property intact across sessions.

---

## Test Vectors

- First 16 phi-steps from MIDI 60, rounded and folded, should produce a sequence with **zero repeated pitch classes** in any window of 12 consecutive notes. (If any 12-window repeats, the fold logic is wrong — check that the accumulator isn't being modded.)
- Step sizes between consecutive displayed notes should be only 1 or 2 semitones (phi ≈ 1.618 rounds to 2, quantization error pushes some to 1). Never 0, never 3+.
- Duration sequence should be non-monotonic and never constant — if every note gets the same duration, the mapping collapsed.
- Run 1000 notes: the set of displayed pitch classes should approach all 12 but the *order* should show no period under 1000. A period under ~50 means the fold is accidentally periodic.

---

## What to Avoid

- **Don't** mod the accumulator. `(current + PHI) % 12` is the single most common implementation error and it silently turns phi into a 12-cycle. The fold must happen on output only.
- **Don't** quantize to the nearest *scale degree* of any existing mode first — that reintroduces periodicity through the back door. Quantize in raw semitone space, fold after.
- **Don't** start with polyphony. One voice, one line. The non-repetition is the texture; adding voices before the line works alone muddies the effect.
- Duration floor matters: if phi-steps quantize small enough, durations can collapse toward zero. Clamp hard.

---

## Quick Reference

| Property | Value |
|---|---|
| Step size | phi ≈ 1.618 semitones |
| Quantization | round to nearest MIDI note |
| Fold | output only, [root, root+12) |
| Accumulator | never modded, runs free |
| Duration | inverse to step width (wide=fast) or direct (wide=slow) |
| Period | none — non-repeating by construction |
| Precedent | Ligeti micropolyphony, late Feldman (by ear, not by system) |

This is the one scale that can't be written down. That's the feature.
