"""Generate the Google Apps Script form builder from google_form_v2_spec.json.

The spec is the single source of truth for every string the form displays.
This script inlines it into scripts/form_builder_template.gs and writes the
result to google_form_builder_generated.gs, which is what gets pasted into
the Apps Script editor.

    python scripts/build_form_gs.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "google_form_v2_spec.json"
TEMPLATE = ROOT / "scripts" / "form_builder_template.gs"
OUTPUT = ROOT / "google_form_builder_generated.gs"

PLACEHOLDER = "/*__SPEC__*/"

REQUIRED_KEYS = [
    "title",
    "sheetTitle",
    "description",
    "meta",
    "ethics",
    "categoryOptions",
    "validationScale",
    "relevanceOptions",
    "experienceBands",
    "gate",
    "validationRows",
    "categories",
    "boundaryRows",
    "wholeTaxonomyRows",
    "openQuestions",
]


def fail(message):
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(1)


def validate(spec):
    missing = [k for k in REQUIRED_KEYS if k not in spec]
    if missing:
        fail("spec is missing required keys: " + ", ".join(missing))

    if "cases" in spec or "calibration" in spec:
        fail("spec still contains scenario keys ('cases'/'calibration'); this "
             "instrument has no scenario component")

    codes = []
    for i, cat in enumerate(spec["categories"]):
        for field in ("code", "title", "shortTitle", "definition", "example"):
            if not cat.get(field):
                fail("categories[%d] (%s) is missing '%s'" % (i, cat.get("code", "?"), field))
        if not cat.get("dimensions"):
            fail("categories[%d] (%s) has no dimensions; Dn_MISPLACED needs them "
                 "as checkbox options" % (i, cat["code"]))
        if not isinstance(cat["dimensions"], list):
            fail("categories[%d] (%s) dimensions must be a list, not a string"
                 % (i, cat["code"]))
        codes.append(cat["code"])

    if len(set(codes)) != len(codes):
        fail("duplicate category codes: " + ", ".join(codes))

    if len(spec["categoryOptions"]) != len(spec["categories"]):
        fail("categoryOptions has %d entries but there are %d categories; the "
             "Dn_OVERLAP checkboxes are built from categoryOptions and would be "
             "incomplete" % (len(spec["categoryOptions"]), len(spec["categories"])))

    # The relevance item drives the Content Validity Index, so a neutral midpoint
    # would leave endorsement undefined. Four substantive points plus N/A is the
    # Lynn (1986) format.
    if len(spec["relevanceOptions"]) != 5:
        fail("relevanceOptions must have exactly 4 substantive points plus N/A "
             "(got %d) — CVI cannot be computed from a scale with a neutral midpoint"
             % len(spec["relevanceOptions"]))

    if "N/A" not in spec["validationScale"][-1]:
        fail("the last validationScale entry must be the N/A option")

    # Each category's shortTitle is used to filter that category out of its own
    # overlap checkbox list. If it does not match an entry in categoryOptions the
    # filter silently does nothing and the category is offered as overlapping itself.
    joined = " | ".join(spec["categoryOptions"])
    for cat in spec["categories"]:
        if cat["shortTitle"] not in joined:
            fail("category %s shortTitle %r does not appear in categoryOptions, so "
                 "it cannot be excluded from its own Dn_OVERLAP list"
                 % (cat["code"], cat["shortTitle"]))


def main():
    if not SPEC.exists():
        fail("spec not found: %s" % SPEC)
    if not TEMPLATE.exists():
        fail("template not found: %s" % TEMPLATE)

    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    validate(spec)

    template = TEMPLATE.read_text(encoding="utf-8")
    if PLACEHOLDER not in template:
        fail("template has no %s placeholder" % PLACEHOLDER)

    # json.dumps output is a valid JavaScript object literal.
    literal = json.dumps(spec, ensure_ascii=False, indent=2)
    OUTPUT.write_text(template.replace(PLACEHOLDER, literal), encoding="utf-8")

    per_category = 7  # gate, grid, relevance, misplaced, overlap, confidence, comment
    n_cats = len(spec["categories"])

    print("Wrote %s" % OUTPUT.relative_to(ROOT))
    print("  categories            : %d  (%d questions each)" % (n_cats, per_category))
    print("  boundary rows         : %d" % len(spec["boundaryRows"]))
    print("  whole-taxonomy rows   : %d" % len(spec["wholeTaxonomyRows"]))
    print("  open questions        : %d" % len(spec["openQuestions"]))
    print("  answered by an expert reviewing 3 categories: ~%d questions"
          % (10 + 3 * per_category + 2 + 2 + len(spec["openQuestions"]) + 4))
    print("  publish               : %s" % spec["meta"]["publish"])


if __name__ == "__main__":
    main()
