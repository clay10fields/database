# Note for Claude

Clayten asked me to leave this here after we talked about interval stacking and the golden-ratio scale.

**Read these two briefs, in this order:**

1. `mixed-interval-stacking-composer.md` — the six mixed-interval patterns (octatonic first, Messiaen Mode 3 second, spiral last).
2. `golden-ratio-nonrepeating-scale.md` — the phi-based non-repeating line. This is the one Clayten is most excited about.

**One thing he specifically wants you to watch:** in the phi implementation, do NOT mod the accumulator. Modding it silently turns phi into a 12-cycle and kills the whole effect. The fold only happens on the output note.

He also mentioned running the phi generator through `research/skills/hypothesis-exhaust` to check whether any bounded window accidentally repeats — as a falsification test before trusting it.

— Ara (left this 2026-10-23)
