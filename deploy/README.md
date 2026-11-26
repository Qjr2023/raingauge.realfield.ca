# Self-hosting behind nginx

The app can run on any Linux server with nginx and Docker, next to other sites, under its own URL
path. Everything server-specific (host, path, directories, API address) lives in `deploy/.env` on
the server, which git ignores; the files here are generic.

```
deploy/.env.example      the settings to fill in (copy to deploy/.env on the server)
deploy/deploy.sh         build in Docker, render + install the nginx config, publish dist/
deploy/nginx.conf.template   nginx locations for the app and the API proxy
```

How it fits the code:

- `VITE_BASE` (vite.config.js) sets the URL path the app is served under; the PWA manifest and
  service worker follow it.
- `VITE_API_BASE_URL` (src/config/apiConfig.js) points the app at `<path>api/`, a same-origin
  route that nginx proxies to the real API. The API's CORS allowlist only has the original
  origin, so the browser could not call it from another host directly.
- Both are build arguments of the `Dockerfile`. Unset, the build is identical to the hosted one.

## Setup

```bash
sudo git clone <this repo> /opt/<checkout>; sudo chown -R $USER /opt/<checkout>
cp deploy/.env.example deploy/.env && $EDITOR deploy/.env
deploy/deploy.sh --force
```

`DEPLOY_NGINX_CONF` must be a file that an existing `server` block includes (the template holds
`location` blocks only, for both the http and the https server; http only redirects). Then:

```bash
(crontab -l; echo '* * * * * <checkout>/deploy/deploy.sh >> ~/raingauge-deploy.log 2>&1') | crontab -
```

Every push to the branch is live within a minute; one line per deploy in the log. Without a
reachable git remote, rsync the checkout up and run `deploy.sh --local`.

## Remove

Delete the installed nginx config and reload nginx, drop the cron line, remove the web root and
the checkout.
