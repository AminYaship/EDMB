#!/usr/bin/env bash
#
# load-edmb.sh - load the EDMB metadata block into a running containerized
# Dataverse demo instance and refresh the Solr schema.
#
# Tested against the official Dataverse container "demo/evaluation" stack
# (gdcc/dataverse:latest, Dataverse 6.10.x) started with `docker compose up`
# from the upstream compose.yml.
#
# Run this from the directory where your compose.yml lives (so that the
# ./docker-dev-volumes/solr path resolves), AFTER the stack is up and the
# bootstrap container has exited.
#
# Usage:
#   ./scripts/load-edmb.sh [PATH_TO_edmb.tsv] [COLLECTION_ALIAS]
#
# Defaults: TSV = ./metadata-block/edmb.tsv, collection alias = root
#
set -euo pipefail

TSV="${1:-./metadata-block/edmb.tsv}"
COLLECTION="${2:-root}"
DV="http://localhost:8080"
SOLR="http://localhost:8983"
CONFIGBAKER_IMAGE="gdcc/configbaker:latest"
SOLR_VOL="./docker-dev-volumes/solr/data"
SCHEMA="${SOLR_VOL}/data/collection1/conf/schema.xml"

echo "==> Checking that Dataverse is up at ${DV}"
curl -fsS "${DV}/api/info/version" >/dev/null || {
  echo "Dataverse is not reachable at ${DV}. Start the stack with 'docker compose up' first." >&2
  exit 1
}

echo "==> [1/4] Loading metadata block from ${TSV}"
curl -fsS "${DV}/api/admin/datasetfield/load" \
  -H "Content-type: text/tab-separated-values" \
  -X POST --upload-file "${TSV}"
echo

echo "==> [2/4] Backing up current Solr schema"
if [ -f "${SCHEMA}" ]; then
  cp "${SCHEMA}" "${SCHEMA}.orig"
  echo "    backup written to ${SCHEMA}.orig"
else
  echo "    WARNING: ${SCHEMA} not found - are you in the compose.yml directory?" >&2
fi

echo "==> [3/4] Updating Solr schema with Dataverse's field list"
curl -fsS "${DV}/api/admin/index/solr/schema" \
  | docker run -i --rm -v "${SOLR_VOL}:/var/solr" "${CONFIGBAKER_IMAGE}" \
      update-fields.sh /var/solr/data/collection1/conf/schema.xml

echo "==> [4/4] Reloading the Solr core"
curl -fsS "${SOLR}/solr/admin/cores?action=RELOAD&core=collection1" >/dev/null
echo "    Solr core reloaded."

echo
echo "Done. Next steps:"
echo "  1. Enable the 'edmb' block for your collection in the UI:"
echo "       ${DV}  ->  collection  ->  Edit  ->  General Information  ->  Metadata Fields"
echo "     (or via API, see docs/03-setup-edmb.md)."
echo "  2. Create a dataset and edit its metadata - the EDMB section should appear."
