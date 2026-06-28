# Crosswalk

Field-level mapping between the `edmb` block and RDA DMP Common Standard
(maDMP) v1.1, in both directions.

## Files

- **`edmb_to_madmp_forward.csv`** — every `edmb` field (74 rows), its maDMP v1.1
  target, a mapping-strength score, and a note.
- **`madmp_to_edmb_reverse.csv`** — every maDMP v1.1 property considered (37
  rows) and how it is satisfied.

## Mapping-strength scale (forward)

| Score | Meaning |
|------:|---------|
| 1.00 | Direct: identical concept and value space |
| 0.75 | Strong: same concept, minor structural difference |
| 0.50 | Partial: related concept; free-text or proxy slot |
| 0.25 | Weak: only loosely inferable; no dedicated slot |
| 0.00 | None: no corresponding maDMP property |

## Totals

Forward: 74 fields — 23 direct, 12 strong, 16 partial, 17 weak, 6 none.
Average strength **0.60**; coverage (score > 0) **91.9%** (68/74).

Reverse: 37 properties — 21 dedicated custom field, 5 partial, 5 Dataverse
Citation block, 4 Dataverse-native record metadata, 2 not covered (the host
repository's own uptime and versioning guarantees).

