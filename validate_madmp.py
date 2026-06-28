#!/usr/bin/env python3
"""
maDMP serialization + schema validation, driven by a Dataverse export.

Usage:
    pip install jsonschema
    # place madmp-schema-1.1.json next to this script (see README.md), then:
    python validate_madmp.py [path/to/export.dataverse_json]

To use a real export instead of the sample, on a running instance with the
record deposited and the EDMB values entered:
    curl "http://localhost:8080/api/datasets/export?exporter=dataverse_json&persistentId=doi:10.7910/DVN/MHN3LM" \
        -o my-export.dataverse_json
    python validate_madmp.py my-export.dataverse_json

Exit 0 = conforms; 1 = validation errors (printed). Output: madmp_MHN3LM.json.
"""
import json
import os
import sys

try:
    from jsonschema import Draft7Validator
except ImportError:
    sys.exit("Missing dependency. Run: pip install jsonschema")

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(HERE, "madmp-schema-1.1.json")
DEFAULT_EXPORT = os.path.join(HERE, "sample-export-MHN3LM.dataverse_json")
OUT_PATH = os.path.join(HERE, "madmp_MHN3LM.json")


def load_blocks(export_path):
    with open(export_path, encoding="utf-8") as f:
        doc = json.load(f)
    version = doc.get("data", {}).get("datasetVersion", doc.get("data", {}))
    blocks = {}
    for bname, block in version.get("metadataBlocks", {}).items():
        flat = {}
        for field in block.get("fields", []):
            flat[field["typeName"]] = field.get("value")
        blocks[bname] = flat
    return doc, version, blocks


export_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_EXPORT
if not os.path.exists(export_path):
    sys.exit(f"Export file not found: {export_path}")

doc, version, blocks = load_blocks(export_path)
edmb = blocks.get("edmb", {})
cite = blocks.get("citation", {})

if not edmb:
    sys.exit("No 'edmb' metadata block found in the export. Did you enter EDMB "
             "values and re-export? See validation/README.md.")


def e(key, default=None):
    return edmb.get(key, default)


def yn(v):
    return str(v).strip().lower() if v is not None else None


def cite_title():
    t = cite.get("title")
    return t if isinstance(t, str) else "Study"


dataset_doi = doc["data"].get("persistentUrl") or doc["data"].get("identifier")

byte_size = None
files = version.get("files", [])
if files and isinstance(files[0], dict):
    byte_size = files[0].get("dataFile", {}).get("filesize")

host = {
    "title": e("plannedRepository"),
    "url": e("plannedRepositoryURL"),
    "backup_frequency": (e("backupFrequency") or "").lower() or None,
    "certified_with": (e("repositoryCertification") or "").lower().replace(" ", "") or None,
    "geo_location": e("geographicBackupLocation"),
    "pid_system": [(e("persistentIdentifierScheme") or "").lower()] if e("persistentIdentifierScheme") else None,
    "storage_type": "object storage",
    "description": e("storageInfrastructure"),
}
host = {k: v for k, v in host.items() if v not in (None, "", [], [""])}

security_and_privacy = []
if e("anonymizationMethod"):
    security_and_privacy.append({"title": "Anonymization", "description": e("anonymizationMethod")})
if e("privacyRiskAssessment"):
    security_and_privacy.append({"title": "Privacy risk assessment", "description": e("privacyRiskAssessment")})

pres_fmt = e("preservationFormat")
if isinstance(pres_fmt, str):
    pres_fmt = [pres_fmt]

distribution = {
    "title": cite_title(),
    "data_access": (e("dataAccessLevel") or "open"),
    "available_until": e("availableUntil"),
    "host": host,
}
if byte_size:
    distribution["byte_size"] = int(byte_size)
if pres_fmt:
    distribution["format"] = pres_fmt
if dataset_doi:
    distribution["access_url"] = dataset_doi
if e("licenseURL"):
    lic = {"license_ref": e("licenseURL")}
    if e("embargoEndDate"):
        lic["start_date"] = e("embargoEndDate")
    distribution["license"] = [lic]
distribution = {k: v for k, v in distribution.items() if v not in (None, "", [])}

dataset = {
    "title": cite_title(),
    "type": "software",
    "dataset_id": {"identifier": dataset_doi, "type": "doi"},
    "personal_data": yn(e("personalDataIncluded")) or "no",
    "sensitive_data": yn(e("sensitiveData")) or "no",
    "distribution": [distribution],
}
if e("preservationPlan"):
    dataset["preservation_statement"] = e("preservationPlan")
if e("dataQualityAssurance"):
    dataset["data_quality_assurance"] = [e("dataQualityAssurance")]
if e("metadataStandard"):
    dataset["metadata"] = [{
        "metadata_standard_id": {"identifier": e("metadataStandard"), "type": "other"},
        "language": "eng",
    }]
if e("toolsAndSoftware"):
    dataset["technical_resource"] = [{"name": "Software", "description": e("toolsAndSoftware")}]
if security_and_privacy:
    dataset["security_and_privacy"] = security_and_privacy

steward_name = e("dataSteward")
steward_mbox = e("accessContact")
contact = {"name": steward_name or "Data Steward"}
if steward_mbox:
    contact["mbox"] = steward_mbox
    contact["contact_id"] = {"identifier": "mailto:" + steward_mbox, "type": "other"}
else:
    contact["contact_id"] = {"identifier": e("dmpIdentifier"), "type": "other"}

contributor = {"name": steward_name or "Data Steward", "role": ["Data Steward"]}
if steward_mbox:
    contributor["mbox"] = steward_mbox
    contributor["contributor_id"] = {"identifier": "mailto:" + steward_mbox, "type": "other"}

cost = None
if e("costValue") is not None:
    try:
        cost_val = float(e("costValue"))
    except (TypeError, ValueError):
        cost_val = None
    if cost_val is not None:
        cost = [{
            "title": e("costTitle") or "Cost",
            "description": e("costDescription") or "",
            "value": cost_val,
            "currency_code": e("costCurrencyCode") or "USD",
        }]

ethical_desc_parts = [p for p in (e("ethicalRestrictions"), e("consentProcedure")) if p]
created = (e("dmpCreationDate") or "2026-01-01") + "T00:00:00Z"
modified = (e("dmpLastUpdated") or e("dmpCreationDate") or "2026-01-01") + "T00:00:00Z"

dmp = {
    "title": "Data Management Plan: " + cite_title(),
    "dmp_id": {"identifier": e("dmpIdentifier"), "type": "url"},
    "created": created,
    "modified": modified,
    "language": "eng",
    "ethical_issues_exist": "yes" if (e("ethicsApproval") or "").lower() in ("yes", "true") else "unknown",
    "contact": contact,
    "contributor": [contributor],
    "dataset": [dataset],
}
if ethical_desc_parts:
    dmp["ethical_issues_description"] = " ".join(ethical_desc_parts)
if e("ethicsApprovalURL"):
    dmp["ethical_issues_report"] = e("ethicsApprovalURL")
if cost:
    dmp["cost"] = cost

madmp = {"dmp": dmp}

if not os.path.exists(SCHEMA_PATH):
    sys.exit(
        "Schema not found: " + SCHEMA_PATH + "\n"
        "Download maDMP-schema-1.1.json from the RDA DMP Common Standard repo "
        "and place it next to this script (see validation/README.md)."
    )

with open(SCHEMA_PATH) as f:
    schema = json.load(f)

validator = Draft7Validator(schema)
errors = sorted(validator.iter_errors(madmp), key=lambda er: list(er.path))

with open(OUT_PATH, "w") as f:
    json.dump(madmp, f, indent=2, ensure_ascii=False)

print(f"Input export : {os.path.basename(export_path)}")
print(f"Datasets: {len(madmp['dmp']['dataset'])} | "
      f"distributions: {sum(len(d.get('distribution', [])) for d in madmp['dmp']['dataset'])} | "
      f"cost items: {len(madmp['dmp'].get('cost', []))}")
print(f"Serialized instance written to: {OUT_PATH}")

if not errors:
    print("VALIDATION: PASS - instance conforms to maDMP-schema-1.1.json")
    sys.exit(0)

print(f"VALIDATION: FAIL - {len(errors)} error(s):")
for er in errors[:30]:
    loc = "/".join(map(str, er.path)) or "(root)"
    print(f"  - at {loc}: {er.message}")
sys.exit(1)
