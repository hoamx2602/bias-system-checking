# Expert validation form — design notes

## Files

| File | Role |
|---|---|
| `google_form_v2_spec.json` | **Source of truth.** Every string the form displays. Edit this. |
| `scripts/form_builder_template.gs` | Builder logic with a `/*__SPEC__*/` placeholder. |
| `scripts/build_form_gs.py` | Inlines the spec into the template, with validation. |
| `google_form_builder_generated.gs` | **Generated — do not edit.** Paste this into Apps Script. |
| `google_form_builder.gs` / `google_form_spec.json` | Original hand-written V1. Untouched, kept for reference. |

Regenerate after any spec change:

```bash
python scripts/build_form_gs.py
```

## Format

The V2 question format — one topic per page, short questions, radio buttons and
checkboxes, a small grid — but the pages are **categories**, not scenarios. The
scenario-annotation component is gone: respondents are domain experts evaluating
the taxonomy, not annotators applying it.

| Page | Content | Who completes it |
|---|---|---|
| 1 | Working definition, why the review is being carried out | all |
| 2 | Data protection, four declarations, consent (branch → submit) | all |
| 3 | Expert profile — reviewer code required, the rest short | all |
| 4 | Taxonomy at a glance — names and one-line focus, no questions | reference |
| 5–14 | One page per category, **gated** — "No" skips to the next | 2–4 categories |
| 15 | Boundary probe — 7 rows | all |
| 16 | Whole-taxonomy grid + confidence | all |
| 17 | 10 open recommendations, overall recommendation, declaration | all |

An expert reviewing three categories answers about 49 questions, most of them a
single click. Reviewing all ten is about 90 questions.

## Each category page

The page description carries that category's **definition, dimensions included,
illustrative example and boundary note**, so the reference material is in front
of the expert while they answer and is never repeated on another page.

| Code | Item | Why |
|---|---|---|
| `Dn_REVIEW` | Gate, multiple choice | "No" navigates to the next category. Google Forms cannot branch from a checkbox, which is why this is per-category rather than one "pick your categories" question. |
| `Dn_RATINGS` | 6-row grid, 1–5 + N/A | Name, definition, dimensions, boundary, example, annotation usability. |
| `Dn_RELEVANCE` | 4-point relevance, no midpoint | The item I-CVI is computed from. |
| `Dn_MISPLACED` | Checkboxes of **this category's own dimensions** | "Which do not belong here?" |
| `Dn_OVERLAP` | Checkboxes of **the other categories** | "Which does this overlap too strongly?" |
| `Dn_CONFIDENCE` | Linear scale 1–5, horizontal | Sensitivity check on CVI. |
| `Dn_COMMENT` | One optional paragraph | |

`Dn_MISPLACED` and `Dn_OVERLAP` reuse the V2 checkbox pattern in place of V1's
five free-text boxes per category. They are faster to answer and, unlike free
text, directly countable:

- **Overlap matrix** — tabulate `Dn_OVERLAP` across the panel as a 10×10 matrix
  of counts. High cells identify the pairs to merge or re-delimit, and should
  agree with the corresponding `E_BOUNDARIES` row. Where they disagree, that is
  itself worth reporting.
- **Relocation candidates** — count `Dn_MISPLACED` selections per dimension. Any
  dimension flagged by a substantial minority is a candidate to move.

## What this instrument establishes

**Content validity and conceptual quality** — whether the categories are clear,
relevant, distinct, comprehensive and usable, in expert judgement.

It does **not** establish that independent annotators apply the taxonomy
consistently, because there is no annotation component and therefore no
Fleiss' κ / Krippendorff's α. If a reliability claim is needed, run a separate
annotation exercise over labelled decision narratives. State this scope limit
explicitly in the write-up; the README sheet carries the same note.

## Analysis

- **CVI**: from `Dn_RELEVANCE`. Endorsement = "Quite relevant" or "Highly
  relevant". I-CVI = endorsed / valid; S-CVI/Ave = mean of the I-CVIs. The
  five-point agreement grids retain a "Neither" midpoint, which leaves
  endorsement undefined — do not compute CVI from them.
- **CVI denominator**: valid ratings actually given — exclude N/A, blanks, and
  categories skipped at the gate. Report the denominator for every item.
- **Missing data**: skipped and missed are distinguishable by design. A blank
  category block always means the gate was answered "No"; within a reviewed
  category every question is required, so N/A is the only permitted non-answer.
- **Grids**: median/IQR and percentage at 4 or 5.
- **`E_BOUNDARIES`**: any row with a median at or below 3, or wide dispersion,
  marks a boundary needing rewording before the taxonomy is used for annotation.
- **Confidence**: report the unweighted I-CVI as the primary figure and a
  confidence-weighted variant as a sensitivity check, not as a substitute.

## Generator validation

`build_form_gs.py` refuses to emit a file if the spec still contains `cases` or
`calibration`, if a category is missing a definition or example, if `dimensions`
is a string rather than a list, if category codes collide, if `relevanceOptions`
has the wrong number of points for a CVI, or if a category's `shortTitle` does
not match an entry in `categoryOptions` — the last of which would silently offer
a category as overlapping itself.

## Google Forms limitations that shaped the design

- No collapsible or accordion element, so reference material cannot be hidden
  behind an expander. Full detail therefore lives on each category's own page and
  the overview page carries names plus a one-line focus only.
- No branching from a checkbox item, hence the per-category gate.
- Long option lists render vertically, so rating questions use `addScaleItem()`
  (linear scale), which renders as one horizontal row.
- The newer publishing model rejects some form-level settings on some accounts
  with "Invalid data updating form"; these are wrapped in `trySet()` and logged
  rather than allowed to abort the build.

## Before distribution

1. Replace `ethics.dataProtection` with the approved ethics wording and DPO contact.
2. Set `meta.researcherEmail`, `meta.returnBy`, `meta.retentionPeriod`.
3. Issue a unique reviewer code with each invitation.
4. Pilot with two reviewers; record actual completion time and adjust the
   estimate in `description`.
5. Remove the `[DRAFT` labels from `title` **and** `sheetTitle`.
6. Set `meta.publish` to `true`.
7. Run `python scripts/build_form_gs.py` and re-run the Apps Script function.
8. Confirm the frozen taxonomy version matches the thesis, generation prompts,
   dataset labels and model evaluation.
