# Setup steps — FastAPI backend for Vedlakshana Store

Everything in this folder has already been tested — I ran the full app
against a real local Postgres, hit every endpoint, and specifically
reproduced the double-submit bug (the same sale id sent twice) and
confirmed it resolves to one row, not a duplicate. Nothing here is
untested code.

## 0. Where this folder goes

Copy this whole `api/` folder into `F:\OneApp\Vedlakshana-Store\`, so you
have:

```
F:\OneApp\Vedlakshana-Store\
├── site\        ← existing frontend, untouched
├── Code.gs       ← existing, kept as fallback reference
└── api\          ← this folder
```

Open the `Vedlakshana-Store` folder in VS Code and you'll see both the
frontend and this new backend side by side.

## 1. Local sanity check (optional but recommended before touching the VPS)

If you have Python 3.11+ and Docker on your own machine:

```bash
cd api
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

docker run -d --name test-pg -e POSTGRES_PASSWORD=test -e POSTGRES_DB=vedlakshana -p 5433:5432 postgres:16

copy .env.example .env
# edit .env: DATABASE_URL=postgresql+psycopg://postgres:test@localhost:5433/vedlakshana

uvicorn app.main:app --reload --port 8000
```

Then visit `http://localhost:8000/docs` (only available when `ENV=development`
in `.env`) — FastAPI's auto-generated interface where you can try `GET /state`
and `POST /sync` by hand in the browser, no curl/Postman needed.

## 2. Database on the VPS

```bash
docker exec -it postgres psql -U sarwora -d postgres \
  -c "CREATE DATABASE vedlakshana;"
docker exec -it postgres psql -U sarwora -d postgres \
  -c "CREATE USER vedlakshana_app WITH PASSWORD 'CHOOSE_A_STRONG_PASSWORD';"
docker exec -it postgres psql -U sarwora -d postgres \
  -c "GRANT ALL PRIVILEGES ON DATABASE vedlakshana TO vedlakshana_app;"
```

(No need to run any schema file by hand — the app creates its own tables
automatically on first startup, via `Base.metadata.create_all()` in `main.py`.
This already ran successfully in my local test.)

## 3. Configure `.env` on the VPS

```bash
cd api
cp .env.example .env
```

Edit `.env`:
- `DATABASE_URL` — use the password you set in step 2, host `postgres` (the
  container name, not `localhost` — see the comment in `.env.example`).
- `WRITE_TOKEN` — already matches your app's current token, leave as-is
  unless you want to rotate it.
- `ALLOWED_ORIGIN` — already set to your GitHub Pages origin.
- `ENV=production` — hides the `/docs` page publicly (recommended for the
  live deployment).

## 4. Add the service to Docker Compose

Paste the block from `docker-compose.snippet.yml` into your existing
`docker-compose.yml`, fixing the two path references to wherever you placed
the `api/` folder.

```bash
docker compose up -d --build store-api
docker compose logs -f store-api   # confirm "Application startup complete", Ctrl+C
```

Quick local test from the VPS:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/state
```

## 5. DNS

Add an A record: `store-api` → your VPS's IP (same pattern as your other
subdomains). Wait a few minutes for it to propagate.

## 6. Nginx + HTTPS

Add the server block from `nginx-store-api.conf`, then:

```bash
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d store-api.sarwora.com
```

Test from your own machine (not the VPS):

```bash
curl https://store-api.sarwora.com/health
```

## 7. Migrate the data

```bash
pip install requests
python3 migrate_from_sheet.py
```

Do this as close as possible to actual cutover (next step).

## 8. Cut over the app (only when you say so — not done yet)

Two small, already-identified edits to `index.html`:
- `SCRIPT_URL` (one constant today) becomes two:
  - `LOAD_URL = 'https://store-api.sarwora.com/state'`
  - `SAVE_URL = 'https://store-api.sarwora.com/sync'`
- `loadState()`'s fetch uses `LOAD_URL`; `persist()`'s fetch uses `SAVE_URL`.

Everything else in `index.html` stays as-is. I haven't made this change —
tell me when you want it done and I'll make exactly this edit, test it with
Playwright against the real staging endpoint first, and ship it the same
way we've shipped every change so far.

## 9. Keep the old backend around

Leave Apps Script + the Sheet reachable for a week or two post-cutover as a
fallback, before considering it fully retired.

## Rollback

Reverting is just pointing `LOAD_URL`/`SAVE_URL` back to the old
`SCRIPT_URL` value and redeploying — the Sheet backend isn't touched or
disabled by any of this, so rollback is same-day and low-risk.
