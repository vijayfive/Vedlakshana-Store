# Till — self-hosted setup

This is a plain static app (HTML/CSS/JS, no build step) with a free Google
Sheet as its database. Three parts to set up, in this order:

## 1. Google Sheet + Apps Script backend (free, ~10 minutes)

1. Go to [sheets.google.com](https://sheets.google.com) and create a new blank
   spreadsheet. Name it e.g. "Till Data".
2. Create three tabs (bottom-left `+`), named **exactly**: `Settings`,
   `Products`, `Sales`. (Delete the default `Sheet1` once these exist.)
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

## 3. Host it on your VPS

You'll need a domain or subdomain (e.g. `till.yourdomain.com`) pointed at
your VPS's IP address (an A record in your DNS).

**Simplest option — Caddy** (free automatic HTTPS in one command; HTTPS is
required for "Add to Home Screen" to work on Android):

```bash
# on the VPS, if Caddy isn't installed yet:
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy

sudo mkdir -p /var/www/till
# copy Caddyfile (from this folder) to /etc/caddy/Caddyfile, editing the domain
sudo systemctl reload caddy
```

Then copy the app files up once, to get it live immediately:

```bash
rsync -avz --exclude '.github' --exclude 'Code.gs' --exclude 'SETUP.md' \
  ./ your-user@your-vps-ip:/var/www/till/
```

Visit `https://till.yourdomain.com` — you should see the PIN screen.

Already run Nginx on that VPS instead? Same idea: point a server block's
`root` at `/var/www/till`, serve `index.html` as the default doc, and use
`certbot --nginx` for the free HTTPS certificate.

## 4. Automatic re-deploys for future changes

Since there's no build step, "deploying" is just copying files — the
included GitHub Actions workflow (`.github/workflows/deploy.yml`) does this
for you on every push:

1. Push this whole folder to a **new GitHub repository** (private is fine).
2. In that repo: **Settings → Secrets and variables → Actions**, add three
   repository secrets:
   - `VPS_HOST` — your VPS's IP address or hostname
   - `VPS_USER` — the SSH username you deploy with
   - `VPS_SSH_KEY` — a private SSH key that can log into that user (generate
     a dedicated deploy key with `ssh-keygen`, and add its **public** half to
     `~/.ssh/authorized_keys` on the VPS for that user)
3. From then on: whenever I hand you an updated `index.html` (or you edit it
   yourself), commit and push to `main` — it's live on the VPS within
   seconds, no manual server commands needed.

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
