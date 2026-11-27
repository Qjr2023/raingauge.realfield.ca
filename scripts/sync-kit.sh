#!/bin/bash
# Copy the shared map kit (site/kit of the prairie-layers repo) into src/kit at the tag named in
# kit.version, for local development. src/kit is not in git; deploy/deploy.sh does the same on
# the server. PL_DIR is a local checkout of prairie-layers (default: ../display).
set -euo pipefail
cd "$(dirname "$0")/.."
PL_DIR=${PL_DIR:-../display}
kit_tag=$(tr -d '[:space:]' < kit.version)
[ -d "$PL_DIR/.git" ] || { echo "no prairie-layers checkout at $PL_DIR (set PL_DIR)"; exit 1; }
git -C "$PL_DIR" rev-parse -q --verify "refs/tags/$kit_tag" >/dev/null \
  || { echo "tag $kit_tag not in $PL_DIR (git fetch --tags origin)"; exit 1; }
rm -rf src/kit && mkdir -p src/kit
git -C "$PL_DIR" archive "$kit_tag" site/kit | tar -x --strip-components=2 -C src/kit
echo "src/kit <- $PL_DIR site/kit @ $kit_tag"
ls src/kit
