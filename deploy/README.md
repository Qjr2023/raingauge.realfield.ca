# Self-hosting behind nginx

The app can run on any Linux server with nginx and Docker, next to other sites, under its own URL
path. Everything server-specific (host, path, directories, ports) lives in `deploy/.env` on
the server, which git ignores; the files here are generic.

```
deploy/.env.example      the settings to fill in (copy to deploy/.env on the server)
deploy/deploy.sh         build in Docker, render + install the nginx config, publish dist/
deploy/nginx.conf.template   nginx locations for the app, the API proxy and the tile proxy
deploy/docker-compose.yml   the API container
kit.version              tag of the prairie-layers repo whose site/kit is copied into src/kit
scripts/sync-kit.sh      that copy, for local development (deploy.sh does it on the server)
```

How it fits the code:

- `VITE_BASE` (vite.config.js) sets the URL path the app is served under; the PWA manifest and
  service worker follow it.
- `VITE_API_BASE_URL` (src/config/apiConfig.js) points the app at `<path>api/`, which nginx proxies
  to the API container (`server/`, `deploy/docker-compose.yml`). The API reads the rain rasters in
  `DEPLOY_RAIN_DIR`; the overlays come from a TiTiler (`DEPLOY_TITILER_URL`) that sees the same
  directory as `/data/rain`, through `<path>tiles/`.
- Both are build arguments of the `Dockerfile`. Unset, the build is identical to the hosted one.
- `<path>stats/<week|season|year>` (POST, GeoJSON polygon body) proxies to TiTiler's statistics
  endpoint for the auto-stretch, and `<path>vector/cropland_outline.geojson` serves that one file
  from `DEPLOY_VECTOR_DIR`. The API's `legend_info` hands both URLs to the app.

## The shared map kit

The map code shared with Prairie Layers (`site/kit` of the private prairie-layers repo) is copied
into `src/kit/`, which git ignores, at the tag named in `kit.version` (for example `kit-v1`):

- locally, `scripts/sync-kit.sh` copies it from a checkout of prairie-layers next to this one
  (`PL_DIR`, default `../display`); run it after cloning and after each bump;
- on the server, `deploy.sh` fetches the tags of `DEPLOY_KIT_CHECKOUT` and copies the kit before
  the frontend build. A tag that is not in that repo makes the deploy fail with "kit tag ... not
  found" (and cron retries each minute until it is).

To move to a newer kit: tag it in prairie-layers, write the tag into `kit.version`, run
`scripts/sync-kit.sh`, test, push.

## Setup

```bash
sudo git clone <this repo> /opt/<checkout>; sudo chown -R $USER /opt/<checkout>
cp deploy/.env.example deploy/.env && $EDITOR deploy/.env
deploy/deploy.sh --force
```

Docker, the docker compose plugin, curl and flock must be installed; the user running deploy.sh
needs the docker group and passwordless sudo for nginx and the web root.

`DEPLOY_NGINX_CONF` must be a file that an existing `server` block includes (the template holds
`location` blocks only, for both the http and the https server; http only redirects). Then:

```bash
(crontab -l; echo '* * * * * <checkout>/deploy/deploy.sh >> ~/raingauge-deploy.log 2>&1') | crontab -
```

Every push to the branch is live within a minute; one line per deploy in the log. Without a
reachable git remote, rsync the checkout up and run `deploy.sh --local`.

## Developing the API

The tests run without Docker or rasters:

```bash
python3 -m venv .venv && .venv/bin/pip install -r server/requirements-dev.txt && cd server && ../.venv/bin/pytest -q
```

## Remove

`docker compose -f deploy/docker-compose.yml down --rmi local` to stop and remove the API
container and its image. Then delete the installed nginx config and reload nginx, drop the cron
line, remove the web root and the checkout.
