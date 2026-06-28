# EDMB — Extended DMP Metadata Block for Dataverse

A deployable Dataverse metadata block (`edmb`) that lets a research-data
repository store the **data-management-plan (DMP) content** a repository's
native Citation block cannot hold — ethics, consent, privacy, preservation,
access, FAIR/reuse, cost, and lifecycle governance — and export it as a
schema-valid **RDA DMP Common Standard (maDMP) v1.1** instance.

This repository accompanies the paper *"Technological Interoperability for
Machine-actionable Data Management Plans"* and contains everything needed to
reproduce the proof of concept on your own machine:

1. Spin up a containerized Harvard Dataverse instance in Docker.
2. Install and enable the `edmb` metadata block on that instance.
3. Serialize a populated block to RDA maDMP v1.1 JSON and validate it against
   the official schema.

## What's in here

| Path | Contents |
|------|----------|
| `docs/01-prerequisites.md` | What to install before you start |
| `docs/02-install-dataverse-docker.md` | Bring up Dataverse in Docker (verified against Dataverse 6.10.x) |
| `docs/03-setup-edmb.md` | Load + enable the `edmb` block, with Solr reload |
| `docs/04-validation.md` | Run the maDMP serialization + schema validation |
| `metadata-block/edmb.tsv` | The metadata block (TSV): 10 categories, 74 fields, ISO-4217 currency CV |
| `scripts/load-edmb.sh` | One-shot helper: load block + refresh Solr + reload core |
| `validation/validate_madmp.py` | Read a Dataverse export → serialize to maDMP v1.1 → validate |
| `validation/sample-export-MHN3LM.dataverse_json` | Committed `dataverse_json` export (Citation + EDMB) used as validation input |
| `crosswalk/edmb_to_madmp_forward.csv` | Full forward crosswalk (74 fields, per-field strength score) |
| `crosswalk/madmp_to_edmb_reverse.csv` | Full reverse coverage (37 maDMP v1.1 properties) |

## Quick start

```bash
# 1. Bring up Dataverse (see docs/02 for details; run from a folder with the
#    upstream compose.yml). Wait until the bootstrap container exits.
docker compose up

# 2. From this repository, load the block and refresh Solr:
./scripts/load-edmb.sh ./metadata-block/edmb.tsv root

# 3. Enable 'edmb' for your collection in the UI, then create a dataset and
#    edit its metadata — the EDMB section appears (see docs/03).

# 4. Validate the maDMP serialization (see docs/04):
cd validation
pip install jsonschema
#  download madmp-schema-1.1.json into this folder first (see validation/README.md)
python validate_madmp.py          # validates the committed dataverse_json export
```

## The `edmb` block at a glance

10 compound categories / 74 primitive fields:

| Category | Fields |
|----------|-------:|
| DMP Lifecycle | 12 |
| Ethics Information | 11 |
| Privacy and Compliance | 10 |
| Preservation Information | 10 |
| Access and Sharing | 9 |
| FAIR and Reuse | 7 |
| NIH Data Sharing | 6 |
| Cost | 4 |
| Expected Data Types | 3 |
| Related Resources | 2 |
| **Total** | **74** |

Against the native Harvard Dataverse model, a representative FioDMP plan maps at
only **27.5%**; with the `edmb` block, the schema covers **91.9%** of the RDA
maDMP v1.1 model (average mapping strength **0.60**), with only two properties
left to the host repository's own service description. See the `crosswalk/`
files for the field-by-field detail.

## Versions this was verified against

- Dataverse container stack: official `gdcc/dataverse:latest` (Dataverse 6.10.x)
  and `gdcc/configbaker:latest`, started from the upstream `compose.yml`.
- Docker Engine with the Compose plugin (`docker compose`, v2 syntax).
- Python 3.9+ with `jsonschema` for validation.

Dataverse's container tooling evolves; if a command differs, cross-check the
current upstream [Container Guide → Demo or Evaluation](https://guides.dataverse.org/en/latest/container/running/demo.html).

## License

See `LICENSE`. The `edmb` block and crosswalk are released as an open
contribution; reuse and adaptation are encouraged.
