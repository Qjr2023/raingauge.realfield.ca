#!/bin/bash
# Build the Virtual Rain Gauge web app and publish it behind nginx on a plain Linux server.
# Runs ON the server. Cron runs it every minute; it only deploys when the branch has a new commit
# (or with --force). Node is not needed on the server: the build runs in Docker (the build stage of
# the Dockerfile) and dist/ is copied out of the image.
# The API (server/) runs as a Docker container, see docker-compose.yml.
#
# All server-specific values come from deploy/.env next to this script (see deploy/.env.example).
#
#   deploy.sh            deploy if the remote branch has a new commit
#   deploy.sh --force    deploy now
#   deploy.sh --local    build the checkout as it is (no fetch), e.g. after an rsync from a PC
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
[ -f "$here/.env" ] || { echo "missing $here/.env (copy deploy/.env.example and fill it in)"; exit 1; }
# shellcheck disable=SC1091
set -a; . "$here/.env"; set +a
for v in DEPLOY_HOST DEPLOY_BASE DEPLOY_WEBROOT DEPLOY_CHECKOUT DEPLOY_BRANCH DEPLOY_NGINX_CONF DEPLOY_RAIN_DIR DEPLOY_API_PORT DEPLOY_TITILER_URL; do
  [ -n "${!v:-}" ] || { echo "$v is not set in $here/.env"; exit 1; }
done
case "$DEPLOY_BASE" in */) ;; *) echo "DEPLOY_BASE must end with /"; exit 1;; esac
base_noslash=${DEPLOY_BASE%/}; [ -n "$base_noslash" ] || base_noslash=/
IMAGE=raingauge-web-build

cd "$DEPLOY_CHECKOUT"
# One deploy at a time: cron runs every minute and a first build takes minutes.
exec 9>"$DEPLOY_CHECKOUT/.deploy.lock"
flock -n 9 || { [ -n "${1:-}" ] && echo "another deploy.sh is running"; exit 0; }

if [ "${1:-}" != --local ]; then
  git fetch -q origin "$DEPLOY_BRANCH"
  if [ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$DEPLOY_BRANCH")" ] && [ "${1:-}" != --force ]; then
    exit 0
  fi
  git reset -q --hard "origin/$DEPLOY_BRANCH"
fi
rev=$(git log -1 --format='%h %s' | cut -c1-100)

staging=$(mktemp -d)
cid=
trap 'rm -rf "$staging"; [ -n "$cid" ] && docker rm -f "$cid" >/dev/null 2>&1 || true' EXIT

# The API container: build the image and (re)create the container only when something changed.
# Wait on /version, which answers without touching the rain data, so a data problem does not
# block a deploy (and /health reports it as before).
docker compose --env-file "$here/.env" -f "$here/docker-compose.yml" up -d --build --quiet-pull \
  >/dev/null 2>"$staging/compose.log" \
  || { echo "$(date -Is) NOT deployed $rev: api container failed"; cat "$staging/compose.log"; exit 1; }
for _ in $(seq 10); do
  curl -sf "http://127.0.0.1:$DEPLOY_API_PORT/version" >/dev/null && break
  sleep 1
done
curl -sf "http://127.0.0.1:$DEPLOY_API_PORT/version" >/dev/null \
  || { echo "$(date -Is) NOT deployed $rev: api not healthy"; docker logs --tail 30 raingauge-api; exit 1; }

# nginx config: render the template, install only when it differs, test, reload. This comes after
# the API container is up so nginx never points at a port that is not answering yet.
sed -e "s|@@HOST@@|$DEPLOY_HOST|g" -e "s|@@BASE@@|$DEPLOY_BASE|g" -e "s|@@BASE_NOSLASH@@|$base_noslash|g" \
    -e "s|@@WEBROOT@@|${DEPLOY_WEBROOT%/}|g" -e "s|@@API_PORT@@|$DEPLOY_API_PORT|g" \
    -e "s|@@TITILER_URL@@|${DEPLOY_TITILER_URL%/}|g" -e "s|@@TILES_LIMIT_REQ@@|${DEPLOY_TILES_LIMIT_REQ:-}|g" \
    "$here/nginx.conf.template" > "$staging/nginx.conf"
if ! sudo cmp -s "$staging/nginx.conf" "$DEPLOY_NGINX_CONF"; then
  sudo install -m 644 "$staging/nginx.conf" "$DEPLOY_NGINX_CONF"
  sudo nginx -t >/dev/null 2>"$staging/nginx.log" \
    || { echo "$(date -Is) NOT deployed $rev: nginx -t failed"; cat "$staging/nginx.log"; exit 1; }
  sudo systemctl reload nginx
fi

# The legacy builder prints a deprecation notice on stderr on every run; keep the log to one line
# per deploy and show the build output only when the build fails.
docker build -q --target build \
  --build-arg VITE_BASE="$DEPLOY_BASE" --build-arg VITE_API_BASE_URL="${DEPLOY_BASE}api" \
  -t "$IMAGE" . >/dev/null 2>"$staging/build.log" \
  || { echo "$(date -Is) NOT deployed $rev: docker build failed"; cat "$staging/build.log"; exit 1; }
cid=$(docker create "$IMAGE")
docker cp "$cid:/app/dist/." "$staging/dist/"
[ -s "$staging/dist/index.html" ] || { echo "$(date -Is) NOT deployed $rev: no index.html in build"; exit 1; }

# World-readable for nginx (mktemp -d is 0700 and rsync -a would keep that).
sudo mkdir -p "$DEPLOY_WEBROOT"
sudo rsync -a --delete --chmod=D755,F644 "$staging/dist/" "$DEPLOY_WEBROOT/"
sudo chmod 755 "$DEPLOY_WEBROOT"
echo "$(date -Is) deployed $rev"
