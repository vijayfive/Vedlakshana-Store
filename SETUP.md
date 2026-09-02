# Vedlakshana Store — self-hosted setup

This is a plain static app (HTML/CSS/JS, no build step) with a free Google
Sheet as its database. Three parts to set up, in this order:

## 1. Google Sheet + Apps Script backend (free, ~10 minutes)

1. Go to [sheets.google.com](https://sheets.google.com) and create a new blank
   spreadsheet. Name it e.g. "Vedlakshana Store Data".
2. Create five tabs (bottom-left `+`), named **exactly**: `Settings`,
   `Products`, `Sales`, `Purchases`, `Expenses`. (Delete the default
   `Sheet1` once these exist — the app also creates any missing tab
   automatically the first time it runs, so this step is a safety net.)
3. Menu: **Extensions → Apps Script**. Delete the placeholder code and paste
   in the contents of `Code.gs` from this folder.
4. In that pasted code, change this line to your own secret string (anything,
   just don't leave the default):
   ```js
   var WRITE_TOKEN = 'change-this-to-your-own-secret';
   ```
5. Click **Deploy → New deployment**. For "Select type" choose **Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**
6. Click **Deploy**, authorize the permissions it asks for (this is your own
   script accessing your own sheet — safe to allow), then copy the **Web app
   URL** it gives you (ends in `/exec`).

## 2. Point the app at your backend

Open `index.html` in this folder and edit these two lines near the top of the
`<script>` block:

```js
var SCRIPT_URL = 'PASTE_YOUR_APPS_SCRIPT_WEB_APP_URL_HERE';
var WRITE_TOKEN = 'change-this-to-your-own-secret';
```

Paste in the URL from step 1.6, and use the **same** token you set in
`Code.gs`. Save the file.

## 3. Host it on GitHub Pages (free, no VPS needed)

The app's runtime files live in the `site/` folder — that's the only part
that gets published; `Code.gs`, `Caddyfile`, and this guide stay out of the
public site.

1. On GitHub, create a **new repository** (public — GitHub Pages needs a
   paid plan to publish from a private repo on most personal accounts).
2. Push this folder to it:
   ```bash
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
   git branch -M main
   git add -A
   git commit -m "Set up Vedlakshana Store"
   git push -u origin main
   ```
3. In that repo: **Settings → Pages → Source → "GitHub Actions"**. That's
   it — the included workflow (`.github/workflows/deploy.yml`) takes it from
   there.
4. Wait ~1 minute, then check **Actions** tab for a green checkmark. Your
   app is now live at:
   `https://YOUR-USERNAME.github.io/YOUR-REPO/`
   (GitHub Pages provides free HTTPS automatically — required for "Add to
   Home Screen"/"Install app" to show up on Android.)

Want a nicer URL instead of `github.io/YOUR-REPO`? Add a custom domain/
subdomain under **Settings → Pages → Custom domain** (point a CNAME record
at `YOUR-USERNAME.github.io`), or leave it as-is — it works fine either way.

Prefer your own VPS instead? `Caddyfile` in this folder still works for
that: point it at `site/` as the root and serve it with Caddy or Nginx —
ask me and I'll walk through it.

## 4. Automatic re-deploys for future changes

Since there's no build step, "deploying" is just publishing files — once
the GitHub Actions source is enabled (step 3 above), every push to `main`
re-publishes `site/` automatically, live within about a minute. No manual
server commands, no secrets to manage. From then on: whenever I hand you an
updated `index.html` (or you edit it yourself), just:
```bash
git add -A && git commit -m "Update app" && git push
```

## Notes

- Data lives entirely in your Google Sheet — open it any time to see raw
  sales/stock, back it up, or fix something by hand.
- The in-app PIN is a soft lock for privacy, not real security — anyone with
  the URL and Apps Script details could, in theory, read the sheet's data via
  the API. For two people using this personally, that's an acceptable
  trade-off; don't reuse `WRITE_TOKEN` anywhere sensitive.
- Icons (`icon-192.png`, `icon-512.png`) and `manifest.json` are what make
  Chrome show a proper **"Install app"** prompt on Android instead of just a
  generic bookmark — that should fix the "can't find Add to Home Screen"
  issue directly, once this is served over HTTPS.
- If you already had a Google Sheet set up before the Purchases/Expenses/
  cost-price features were added: no action needed. The app creates any
  missing tab automatically the first time it talks to your sheet, and
  `Code.gs` rewrites the `Products`/`Sales` column headers to include the
  new fields the next time it saves.
- Sharing a bill to WhatsApp uses your phone's normal "Share" sheet (via
  the Web Share API) so the PDF goes across as a real attachment — this
  only works over HTTPS (which GitHub Pages already gives you) and on
  browsers that support file sharing (recent Chrome on Android does). If
  it's not available, the app falls back to downloading the PDF so you can
  attach it manually.
- Whenever you edit `Code.gs` itself (not just the Google Sheet's data),
  remember it needs a fresh **Deploy → Manage deployments → pencil icon →
  Version: "New version" → Deploy** — just saving the script does not
  update the live Web App URL.
