# 02 — Ground-truth labeling protocol

This is the step that makes calibration meaningful — and the hardest one. The model's `P0` is
only as good as the `is_road_blocked` labels you feed it.

## The two labels, precisely

| Label | Definition | Afghanistan prevalence |
|---|---|---|
| `is_road_affected` | The event impacted a road **in any way**: happened on/next to a road, targeted road users, damaged road infrastructure, disrupted traffic even briefly. | 20.8% |
| `is_road_blocked` | A road was actually **closed or made impassable** for a meaningful period: physical barricade, sit-in occupying the carriageway, checkpoint denial, destroyed bridge/culvert, territorial closure. | 0.87% |

**Blocked ⊆ affected** by definition: a blocked road is always affected. Only `is_road_blocked`
is a model target; `is_road_affected` exists for consistency checks.

## Decision rules (with worked examples)

Classify from the event's `notes` text, cross-referenced against closure sources where possible.

| Event (from notes) | affected | blocked | Why |
|---|---|---|---|
| Roadside IED detonates against a convoy; casualties; traffic resumes | yes | **no** | The road was the *scene*, not closed. This is the single most common labeling mistake. |
| Protesters block the highway with burning tires for six hours | yes | **yes** | Deliberate closure — the archetypal blocked event. |
| Sit-in at a city intersection, traffic diverted | yes | **yes** | Occupied carriageway = impassable. |
| Armed group seizes district, closes the road to the provincial capital | yes | **yes** | Territorial-control closure. |
| Airstrike on a compound 2 km from the highway | no | no | No road interaction in the notes. |
| Bridge destroyed by shelling | yes | **yes** | Infrastructure made impassable. |
| Checkpoint established, vehicles searched but passing | yes | no | Disruption, not closure. Escalate to *blocked* only if notes say traffic was denied. |
| Abduction of travelers on the road | yes | no | Road users targeted; road itself open. |

When notes are ambiguous, label **no** (blocked). Under 0.9% prevalence, false positives distort
`P0` far more than false negatives — bias toward precision on the positive class.

## Sources to classify against

- The ACLED `notes` field itself (primary; the Afghanistan labels were produced by an
  LLM-assisted classification of notes, human-spot-checked).
- OCHA humanitarian access reports and the Logistics Cluster's access-constraint maps —
  independent closure ground truth, ideal for cross-checking (this is also listed as open
  work in the methodology §5).
- Local media / road-authority announcements where available.

## Format contract (what the code expects)

- Two extra columns on the classified CSV: `is_road_blocked` and (optionally)
  `is_road_affected`, values **`yes` / `no`** — case- and whitespace-insensitive; anything that
  isn't "yes" (including blank) parses as **no** (`c2rb.load_labels`).
- Column names are configurable via `paths.label_blocked_col` / `paths.label_affected_col` in
  the country YAML if you use different headers.

## Quality checks before training

1. **Nesting**: `blocked ⊆ affected` should hold almost exactly. Afghanistan has 1 exception
   in 607 — more than a handful means your definitions drifted.
2. **Prevalence sanity**: expect blocked prevalence around 0.5–2%. Far above that usually means
   affected/blocked conflation; far below means calibration will lean entirely on the prior.
3. **Positive count**: `train.py` hard-fails at 0 positives and warns below 30
   (`MIN_POSITIVES_WARN`). Aim for **at least a few dozen** blocked positives; below that,
   treat every per-type `P0` as provisional.
4. **Ranking sanity** (after training): protests/territorial events should out-rank explosives
   in `P0`. An inverted ranking is the classic symptom of IED-scene events mislabeled as
   blocked (see [06_evaluation.md](06_evaluation.md)).
5. **Inter-annotator spot-check**: have a second person (or a second model prompt) relabel a
   random 100–200 events and compare. Disagreement above ~5% on *blocked* means the decision
   rules need tightening before you trust the calibration.

## Known limitation

Labels inherit the reporting quality of `notes`: an event whose notes omit the closure is a
false negative you cannot detect from the data alone. This is documented in methodology §5.1;
cross-checking against OCHA/Logistics Cluster data is the mitigation.

Next: [03_road_network.md](03_road_network.md).
